"""
订单服务
处理订单创建、支付、发货等核心业务逻辑
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Order, Commodity, Card, User, PaymentMethod,
    Coupon, Bill, UserGroup
)
from ..core.exceptions import (
    ValidationError, NotFoundError, StockError,
    PaymentError, InsufficientBalanceError
)
from ..core.security import generate_trade_no
from ..payments import get_payment_handler, PaymentResult
from ..plugins.sdk.hooks import hooks, Events


class OrderService:
    """订单服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_amount(
        self,
        commodity: Commodity,
        quantity: int,
        user: Optional[User] = None,
        user_group: Optional[UserGroup] = None,
        race: Optional[str] = None,
        card_id: Optional[int] = None,
        coupon_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        计算订单金额
        
        Returns:
            {
                "amount": 订单金额,
                "unit_price": 单价,
                "coupon_discount": 优惠券抵扣,
                "draft_premium": 预选加价,
            }
        """
        # 基础价格
        if user:
            unit_price = float(commodity.user_price)
        else:
            unit_price = float(commodity.price)
        
        # 用户组折扣
        if user_group and commodity.level_disable != 1:
            discount = float(user_group.discount)
            if discount > 0:
                unit_price = unit_price * (1 - discount)
        
        # TODO: 解析商品配置中的批发价格
        # TODO: 解析会员等级自定义价格
        
        amount = unit_price * quantity
        draft_premium = 0
        coupon_discount = 0
        
        # 预选加价
        if card_id and commodity.draft_status == 1:
            draft_premium = float(commodity.draft_premium)
            amount += draft_premium
        
        # 优惠券
        if coupon_code:
            coupon = await self._validate_coupon(coupon_code, commodity, amount)
            if coupon:
                if coupon.mode == 0:  # 固定金额
                    coupon_discount = float(coupon.money)
                else:  # 按件优惠
                    coupon_discount = float(coupon.money) * quantity
                amount -= coupon_discount
        
        # 保留两位小数
        amount = round(amount, 2)
        
        return {
            "amount": amount,
            "unit_price": round(unit_price, 2),
            "coupon_discount": round(coupon_discount, 2),
            "draft_premium": draft_premium,
        }
    
    async def create_order(
        self,
        commodity_id: int,
        quantity: int,
        payment_id: int,
        contact: str,
        user: Optional[User] = None,
        password: Optional[str] = None,
        race: Optional[str] = None,
        card_id: Optional[int] = None,
        coupon_code: Optional[str] = None,
        widget: Optional[Dict] = None,
        client_ip: Optional[str] = None,
        device: int = 0,
        callback_url: str = "",
        return_url: str = "",
    ) -> Dict[str, Any]:
        """
        创建订单
        
        Returns:
            {
                "trade_no": 订单号,
                "amount": 金额,
                "status": 状态,
                "payment_url": 支付链接,
                "secret": 卡密(余额支付时),
            }
        """
        # 1. 验证商品
        commodity = await self._get_commodity(commodity_id)
        
        # 2. 验证购买条件
        await self._validate_purchase(commodity, quantity, user, card_id, race)
        
        # 3. 验证库存
        await self._validate_stock(commodity, quantity, race, card_id)
        
        # 4. 验证支付方式
        payment_method = await self._get_payment_method(payment_id, user)
        
        # 5. 获取用户组
        user_group = None
        if user and user.group_id:
            result = await self.db.execute(
                select(UserGroup).where(UserGroup.id == user.group_id)
            )
            user_group = result.scalar_one_or_none()
        
        # 6. 计算金额
        price_info = await self.calculate_amount(
            commodity, quantity, user, user_group, race, card_id, coupon_code
        )
        
        # 7. 钩子：订单创建前（插件可拦截）
        ctx = await hooks.emit(Events.ORDER_CREATING, {
            "commodity": commodity,
            "quantity": quantity,
            "user": user,
            "amount": price_info["amount"],
            "race": race,
            "contact": contact,
        })
        if ctx.cancelled:
            raise ValidationError(ctx.cancel_reason or "订单创建被拦截")
        
        # 8. 创建订单
        trade_no = generate_trade_no()
        order = Order(
            trade_no=trade_no,
            user_id=user.id if user else None,
            commodity_id=commodity.id,
            payment_id=payment_method.id,
            amount=price_info["amount"],
            quantity=quantity,
            contact=contact,
            password=password,
            race=race,
            card_id=card_id,
            widget=str(widget) if widget else None,
            owner_id=commodity.owner_id,
            rent=float(commodity.factory_price) * quantity,
            create_ip=client_ip,
            create_device=device,
            status=0,
            delivery_status=0,
        )
        
        # 8. 处理优惠券
        if coupon_code:
            coupon = await self._use_coupon(coupon_code, trade_no)
            if coupon:
                order.coupon_id = coupon.id
        
        # 9. 处理推广关系
        if user and user.parent_id:
            order.from_user_id = user.parent_id
        
        self.db.add(order)
        await self.db.flush()
        
        # 钩子：订单创建后
        await hooks.emit(Events.ORDER_CREATED, {
            "order": order,
            "commodity": commodity,
            "user": user,
        })
        
        # 10. 处理支付
        result = {
            "trade_no": trade_no,
            "amount": price_info["amount"],
            "status": 0,
            "payment_url": None,
            "secret": None,
        }
        
        # 余额支付
        if payment_method.handler == "#balance":
            if not user:
                raise PaymentError("余额支付需要登录")
            await self._pay_with_balance(order, user)
            secret = await self.deliver_order(order)
            result["status"] = 1
            result["secret"] = secret
            
            # 钩子：支付成功 + 发货完成
            await hooks.emit(Events.ORDER_PAID, {
                "order": order, "user": user, "commodity": commodity,
            })
            await hooks.emit(Events.ORDER_DELIVERED, {
                "order": order, "secret": secret,
            })
        else:
            # 第三方支付
            payment_result = await self._create_payment(
                order, payment_method, callback_url, return_url, client_ip
            )
            if payment_result.success:
                order.pay_url = payment_result.payment_url or payment_result.qrcode_url
                result["payment_url"] = order.pay_url
                result["payment_type"] = payment_result.payment_type.value
                result["extra"] = payment_result.extra
        
        await self.db.commit()
        return result
    
    async def handle_callback(
        self,
        handler: str,
        data: Dict[str, Any]
    ) -> str:
        """处理支付回调"""
        # 获取支付处理器
        payment_class = get_payment_handler(handler)
        if not payment_class:
            return "unknown handler"
        
        # 获取支付配置
        result = await self.db.execute(
            select(PaymentMethod).where(PaymentMethod.handler == handler).limit(1)
        )
        payment_method = result.scalar_one_or_none()
        if not payment_method:
            return "payment not configured"
        
        import json
        config = json.loads(payment_method.config) if payment_method.config else {}
        payment = payment_class(config)
        
        # 验证回调
        callback_result = await payment.verify_callback(data)
        if not callback_result.success:
            return payment.get_callback_response(False)
        
        # 查找订单
        result = await self.db.execute(
            select(Order).where(Order.trade_no == callback_result.trade_no)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return payment.get_callback_response(False)
        
        # 检查状态
        if order.status != 0:
            return payment.get_callback_response(True)
        
        # 验证金额
        if abs(float(order.amount) - callback_result.amount) > 0.01:
            return payment.get_callback_response(False)
        
        # 完成订单
        order.status = 1
        order.paid_at = datetime.utcnow()
        order.external_trade_no = callback_result.external_trade_no
        
        # 钩子：支付成功
        await hooks.emit(Events.ORDER_PAID, {
            "order": order,
            "callback_data": data,
        })
        
        # 发货
        secret = await self.deliver_order(order)
        
        # 钩子：发货完成
        await hooks.emit(Events.ORDER_DELIVERED, {
            "order": order,
            "secret": secret,
        })
        
        # 处理佣金
        await self._process_commission(order)
        
        # 累计用户充值
        if order.user_id:
            result = await self.db.execute(
                select(User).where(User.id == order.user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.total_recharge = float(user.total_recharge) + float(order.amount)
        
        await self.db.commit()
        return payment.get_callback_response(True)
    
    async def deliver_order(self, order: Order) -> str:
        """发货"""
        # 获取商品
        result = await self.db.execute(
            select(Commodity).where(Commodity.id == order.commodity_id)
        )
        commodity = result.scalar_one_or_none()
        
        if not commodity:
            order.secret = "商品不存在"
            order.delivery_status = 1
            return order.secret
        
        # 自动发货
        if commodity.delivery_way == 0:
            secret = await self._pull_cards(order, commodity)
            order.secret = secret
            order.delivery_status = 1
        else:
            # 手动发货
            order.secret = commodity.delivery_message or "正在发货中，请耐心等待"
            order.delivery_status = 0
        
        return order.secret
    
    async def _pull_cards(self, order: Order, commodity: Commodity) -> str:
        """拉取卡密"""
        # 预选卡密
        if order.card_id:
            result = await self.db.execute(
                select(Card).where(Card.id == order.card_id).where(Card.status == 0)
            )
            card = result.scalar_one_or_none()
            if card:
                card.status = 1
                card.order_id = order.id
                card.sold_at = datetime.utcnow()
                return card.secret
            return "预选卡密已被售出"
        
        # 确定排序方式
        if commodity.delivery_auto_mode == 0:
            order_by = Card.id.asc()
        elif commodity.delivery_auto_mode == 1:
            order_by = func.random()
        else:
            order_by = Card.id.desc()
        
        # 查询卡密
        query = (
            select(Card)
            .where(Card.commodity_id == order.commodity_id)
            .where(Card.status == 0)
        )
        
        if order.race:
            query = query.where(Card.race == order.race)
        
        query = query.order_by(order_by).limit(order.quantity)
        
        result = await self.db.execute(query)
        cards = result.scalars().all()
        
        if len(cards) < order.quantity:
            return "库存不足，请联系客服"
        
        secrets = []
        for card in cards:
            card.status = 1
            card.order_id = order.id
            card.sold_at = datetime.utcnow()
            secrets.append(card.secret)
        
        return "\n".join(secrets)
    
    async def _get_commodity(self, commodity_id: int) -> Commodity:
        """获取商品"""
        result = await self.db.execute(
            select(Commodity).where(Commodity.id == commodity_id)
        )
        commodity = result.scalar_one_or_none()
        
        if not commodity:
            raise NotFoundError("商品不存在")
        if commodity.status != 1:
            raise ValidationError("商品已下架")
        
        return commodity
    
    async def _validate_purchase(
        self,
        commodity: Commodity,
        quantity: int,
        user: Optional[User],
        card_id: Optional[int],
        race: Optional[str],
    ):
        """验证购买条件"""
        # 仅登录用户可购买
        if commodity.only_user == 1 and not user:
            raise ValidationError("请先登录后再购买")
        
        # 最少购买数量
        if commodity.minimum > 0 and quantity < commodity.minimum:
            raise ValidationError(f"最少购买 {commodity.minimum} 件")
        
        # 最多购买数量
        if commodity.maximum > 0 and quantity > commodity.maximum:
            raise ValidationError(f"最多购买 {commodity.maximum} 件")
        
        # 预选卡密数量限制
        if card_id and commodity.draft_status == 1 and quantity != 1:
            raise ValidationError("预选卡密只能购买1件")
        
        # 限购检查
        if commodity.purchase_count > 0 and user:
            result = await self.db.execute(
                select(func.count())
                .select_from(Order)
                .where(Order.user_id == user.id)
                .where(Order.commodity_id == commodity.id)
                .where(Order.status == 1)
            )
            count = result.scalar()
            if count >= commodity.purchase_count:
                raise ValidationError(f"该商品每人限购 {commodity.purchase_count} 件")
    
    async def _validate_stock(
        self,
        commodity: Commodity,
        quantity: int,
        race: Optional[str],
        card_id: Optional[int],
    ):
        """验证库存"""
        if commodity.delivery_way != 0:
            return  # 手动发货不检查
        
        query = (
            select(func.count())
            .select_from(Card)
            .where(Card.commodity_id == commodity.id)
            .where(Card.status == 0)
        )
        
        if race:
            query = query.where(Card.race == race)
        
        result = await self.db.execute(query)
        stock = result.scalar()
        
        if stock < quantity:
            raise StockError("库存不足")
    
    async def _get_payment_method(
        self,
        payment_id: int,
        user: Optional[User]
    ) -> PaymentMethod:
        """获取支付方式"""
        result = await self.db.execute(
            select(PaymentMethod).where(PaymentMethod.id == payment_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise NotFoundError("支付方式不存在")
        if payment.status != 1 or payment.commodity != 1:
            raise ValidationError("该支付方式不可用")
        if payment.handler == "#balance" and not user:
            raise ValidationError("余额支付需要登录")
        
        return payment
    
    async def _validate_coupon(
        self,
        code: str,
        commodity: Commodity,
        amount: float
    ) -> Optional[Coupon]:
        """验证优惠券"""
        result = await self.db.execute(
            select(Coupon).where(Coupon.code == code)
        )
        coupon = result.scalar_one_or_none()
        
        if not coupon:
            raise ValidationError("优惠券不存在")
        if coupon.status != 0:
            raise ValidationError("优惠券已失效")
        if coupon.owner_id != commodity.owner_id:
            raise ValidationError("该优惠券不可用")
        if coupon.commodity_id and coupon.commodity_id != commodity.id:
            raise ValidationError("该优惠券不适用于此商品")
        if coupon.category_id and coupon.category_id != commodity.category_id:
            raise ValidationError("该优惠券不适用于此分类")
        if coupon.expires_at and coupon.expires_at < datetime.utcnow():
            raise ValidationError("优惠券已过期")
        if float(coupon.money) >= amount:
            raise ValidationError("优惠券面额大于订单金额")
        
        return coupon
    
    async def _use_coupon(self, code: str, trade_no: str) -> Optional[Coupon]:
        """使用优惠券"""
        result = await self.db.execute(
            select(Coupon).where(Coupon.code == code).where(Coupon.status == 0)
        )
        coupon = result.scalar_one_or_none()
        
        if coupon:
            coupon.use_life += 1
            coupon.life -= 1
            coupon.trade_no = trade_no
            coupon.used_at = datetime.utcnow()
            if coupon.life <= 0:
                coupon.status = 1
        
        return coupon
    
    async def _pay_with_balance(self, order: Order, user: User):
        """余额支付"""
        if float(user.balance) < float(order.amount):
            raise InsufficientBalanceError()
        
        # 扣除余额
        user.balance = float(user.balance) - float(order.amount)
        
        # 记录账单
        bill = Bill(
            user_id=user.id,
            amount=float(order.amount),
            balance=float(user.balance),
            type=0,
            description=f"商品购买[{order.trade_no}]",
            order_trade_no=order.trade_no,
        )
        self.db.add(bill)
        
        # 更新订单状态
        order.status = 1
        order.paid_at = datetime.utcnow()
    
    async def _create_payment(
        self,
        order: Order,
        payment_method: PaymentMethod,
        callback_url: str,
        return_url: str,
        client_ip: Optional[str],
    ) -> PaymentResult:
        """创建第三方支付"""
        payment_class = get_payment_handler(payment_method.handler)
        if not payment_class:
            raise PaymentError("支付方式未实现")
        
        import json
        config = json.loads(payment_method.config) if payment_method.config else {}
        payment = payment_class(config)
        
        # 添加手续费
        amount = float(order.amount)
        if payment_method.cost > 0:
            if payment_method.cost_type == 0:
                order.pay_cost = float(payment_method.cost)
            else:
                order.pay_cost = amount * float(payment_method.cost)
            amount += float(order.pay_cost)
            order.amount = round(amount, 2)
        
        # 拼接完整的回调路径
        notify_url = f"{callback_url.rstrip('/')}/api/v1/payments/{payment_method.handler}/callback"
        sync_return_url = f"{return_url.rstrip('/')}/api/v1/payments/{payment_method.handler}/return"
        
        return await payment.create_payment(
            trade_no=order.trade_no,
            amount=float(order.amount),
            callback_url=notify_url,
            return_url=sync_return_url,
            channel=payment_method.code,
            client_ip=client_ip,
        )
    
    async def _process_commission(self, order: Order):
        """处理分销佣金"""
        if not order.from_user_id:
            return
        
        # 获取推广人
        result = await self.db.execute(
            select(User).where(User.id == order.from_user_id)
        )
        promoter = result.scalar_one_or_none()
        
        if not promoter:
            return
        
        # TODO: 实现三级分销逻辑
        # 这里简化为单级返佣10%
        rebate_rate = 0.1
        rebate = float(order.amount) * rebate_rate
        
        if rebate >= 0.01:
            promoter.balance = float(promoter.balance) + rebate
            order.rebate = rebate
            
            # 记录账单
            bill = Bill(
                user_id=promoter.id,
                amount=rebate,
                balance=float(promoter.balance),
                type=1,
                description=f"推广返佣[{order.trade_no}]",
                order_trade_no=order.trade_no,
            )
            self.db.add(bill)
