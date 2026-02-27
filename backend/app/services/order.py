"""
订单服务
处理订单创建、支付、发货等核心业务逻辑

注意: 此模块是订单创建的唯一入口，API 层应委托给此服务。
"""

import json as json_lib
import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
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
from ..plugins.sdk.hooks import hooks, Events
from ..plugins.sdk.payment_base import PaymentPluginBase

logger = logging.getLogger("services.order")


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
        计算订单金额（使用 Decimal 避免精度丢失）。
        
        支持：基础价格、用户价、用户组折扣、种类定价、批发规则、
        预选加价、优惠券抵扣。
        
        Returns:
            {
                "amount": Decimal 订单金额,
                "unit_price": Decimal 单价,
                "coupon_discount": Decimal 优惠券抵扣,
                "draft_premium": Decimal 预选加价,
            }
        """
        TWO_PLACES = Decimal("0.01")
        
        # 基础价格
        if user:
            unit_price = Decimal(str(commodity.user_price))
        else:
            unit_price = Decimal(str(commodity.price))
        
        # 用户组折扣
        if user_group and commodity.level_disable != 1:
            discount = Decimal(str(user_group.discount))
            if discount > 0:
                unit_price = unit_price * (Decimal("1") - discount)
        
        # 解析商品配置中的种类定价和批发规则
        if commodity.config and race:
            unit_price = self._apply_config_pricing(
                commodity.config, unit_price, race, quantity
            )
        else:
            # 无种类维度时，应用全局批发规则（新字段优先，旧配置兼容）
            unit_price = self._apply_global_wholesale_pricing(
                commodity, unit_price, quantity
            )
        
        amount = unit_price * quantity
        draft_premium = Decimal("0")
        coupon_discount = Decimal("0")
        
        # 预选加价
        if card_id and commodity.draft_status == 1:
            draft_premium = Decimal(str(commodity.draft_premium))
            amount += draft_premium
        
        # 优惠券
        if coupon_code:
            coupon = await self._validate_coupon(
                coupon_code, commodity, float(amount)
            )
            if coupon:
                if coupon.mode == 0:  # 固定金额
                    coupon_discount = Decimal(str(coupon.money))
                else:  # 按件优惠
                    coupon_discount = Decimal(str(coupon.money)) * quantity
                amount -= coupon_discount
        
        # 保留两位小数
        amount = amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        unit_price = unit_price.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        
        return {
            "amount": amount,
            "unit_price": unit_price,
            "coupon_discount": coupon_discount.quantize(TWO_PLACES),
            "draft_premium": draft_premium,
        }
    
    @staticmethod
    def _apply_config_pricing(
        config_text: str,
        base_price: Decimal,
        race: str,
        quantity: int,
    ) -> Decimal:
        """
        解析商品 config 中的种类定价和批发规则。
        
        格式：
            [category]
            种类A=10.00
            
            [category_wholesale]
            种类A.10=9.00        # 买10件及以上，单价9.00
            种类A.50=80%         # 买50件及以上，打八折
        """
        category_price = base_price
        wholesale_rules = []
        
        current_section = None
        for line in config_text.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].lower()
            elif "=" in line and current_section:
                key, value = line.split("=", 1)
                key, value = key.strip(), value.strip()
                
                if current_section == "category" and key == race:
                    try:
                        category_price = Decimal(value)
                    except Exception:
                        pass
                        
                elif current_section == "category_wholesale" and "." in key:
                    cat_name, qty_str = key.split(".", 1)
                    if cat_name == race:
                        try:
                            qty = int(qty_str)
                            if value.endswith("%"):
                                wholesale_rules.append(
                                    (qty, "percent", Decimal(value[:-1]))
                                )
                            else:
                                wholesale_rules.append(
                                    (qty, "fixed", Decimal(value))
                                )
                        except (ValueError, Exception):
                            pass
        
        # 应用批发规则（取最大匹配数量的规则）
        unit_price = category_price
        if wholesale_rules:
            wholesale_rules.sort(key=lambda x: x[0])
            for min_qty, rule_type, rule_val in wholesale_rules:
                if quantity >= min_qty:
                    if rule_type == "percent":
                        unit_price = category_price * rule_val / Decimal("100")
                    else:
                        unit_price = rule_val
        
        return unit_price

    @staticmethod
    def _apply_global_wholesale_pricing(
        commodity: Commodity,
        base_price: Decimal,
        quantity: int,
    ) -> Decimal:
        """应用全局批发规则（wholesale_config 优先，config[wholesale] 兜底）。"""
        rules: List[tuple[int, str, Decimal]] = []

        # 1) 新字段: wholesale_config(JSON)
        if commodity.wholesale_config:
            try:
                config_items = json_lib.loads(commodity.wholesale_config)
                if isinstance(config_items, list):
                    for item in config_items:
                        if not isinstance(item, dict):
                            continue
                        qty = int(item.get("quantity", 0))
                        if qty <= 0:
                            continue
                        if item.get("type") == "percent" or item.get("discount_percent") is not None:
                            discount_percent = item.get("discount_percent")
                            if discount_percent is None:
                                continue
                            rules.append((qty, "percent", Decimal(str(discount_percent))))
                        elif item.get("price") is not None:
                            rules.append((qty, "fixed", Decimal(str(item.get("price")))))
            except Exception:
                rules = []

        # 2) 兼容旧字段: config 中的 [wholesale]（仅在新字段无有效规则时）
        if not rules and commodity.config:
            current_section = None
            for line in commodity.config.strip().split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1].lower()
                    continue
                if current_section != "wholesale" or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                try:
                    qty = int(key)
                    if qty <= 0:
                        continue
                    if value.endswith("%"):
                        rules.append((qty, "percent", Decimal(value[:-1])))
                    else:
                        rules.append((qty, "fixed", Decimal(value)))
                except Exception:
                    continue

        unit_price = base_price
        if rules:
            rules.sort(key=lambda x: x[0])
            for min_qty, rule_type, rule_val in rules:
                if quantity >= min_qty:
                    if rule_type == "percent":
                        unit_price = base_price * rule_val / Decimal("100")
                    else:
                        unit_price = rule_val

        return unit_price
    
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
        创建订单（统一入口）。
        
        Returns:
            {
                "trade_no": 订单号,
                "amount": 金额,
                "status": 状态,
                "payment_url": 支付链接,
                "payment_type": 支付类型,
                "extra": 额外信息,
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
        
        # 8. 创建订单（trade_no 冲突时自动重试，数据库 UNIQUE 约束兜底）
        for _retry in range(3):
            trade_no = generate_trade_no()
            exists = await self.db.execute(
                select(Order.id).where(Order.trade_no == trade_no).limit(1)
            )
            if not exists.scalar_one_or_none():
                break
        else:
            trade_no = generate_trade_no()  # 最后一搏
        
        # 处理密码哈希
        hashed_password = password
        if password:
            from ..core.security import get_password_hash
            hashed_password, _ = get_password_hash(password)
            
        order = Order(
            trade_no=trade_no,
            user_id=user.id if user else None,
            commodity_id=commodity.id,
            payment_id=payment_method.id,
            amount=price_info["amount"],
            quantity=quantity,
            contact=contact,
            password=hashed_password,
            race=race,
            card_id=card_id,
            widget=str(widget) if widget else None,
            owner_id=commodity.owner_id,
            rent=Decimal(str(commodity.factory_price)) * quantity,
            create_ip=client_ip,
            create_device=device,
            status=0,
            delivery_status=0,
        )
        
        # 处理优惠券
        if coupon_code:
            coupon = await self._use_coupon(coupon_code, trade_no)
            if coupon:
                order.coupon_id = coupon.id
        
        # 处理推广关系
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
        
        # 9. 处理支付
        result = {
            "trade_no": trade_no,
            "amount": float(price_info["amount"]),
            "status": 0,
            "payment_url": None,
            "payment_type": None,
            "extra": {},
            "secret": None,
        }
        
        # 余额支付
        if payment_method.handler == "#balance":
            if not user:
                raise PaymentError("余额支付需要登录")
            await self._pay_with_balance(order, user, commodity)
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
            
            # 佣金 + 累计消费
            await self._process_commission(order)
            await self._accumulate_recharge(order)
        else:
            # 第三方支付
            payment_result = await self._create_payment(
                order, payment_method, callback_url, return_url,
                client_ip, commodity.name,
            )
            if payment_result.success:
                pay_url = payment_result.payment_url
                p_type = payment_result.payment_type.value
                extra = payment_result.extra or {}
                
                # 二维码模式
                if p_type == "qrcode" and payment_result.qrcode_url:
                    pay_url = payment_result.qrcode_url
                    extra["qrcode_url"] = payment_result.qrcode_url
                
                # 表单模式
                if payment_result.form_action:
                    pay_url = payment_result.form_action
                    p_type = "form"
                    extra = {"form_data": payment_result.form_data}
                
                order.pay_url = pay_url or payment_result.qrcode_url
                result["payment_url"] = pay_url
                result["payment_type"] = p_type
                result["extra"] = extra
            else:
                raise PaymentError(f"支付创建失败: {payment_result.error_msg}")
        
        result["amount"] = float(order.amount)
        await self.db.commit()
        return result
    
    async def handle_callback(
        self,
        handler: str,
        data: Dict[str, Any]
    ) -> str:
        """
        处理支付回调。
        
        注意: 实际的回调入口在 api/v1/payments.py，此方法已不推荐直接使用。
        保留是为了向后兼容，已升级为支持插件系统。
        """
        from ..plugins import plugin_manager, PAYMENT_HANDLERS as PLUGIN_HANDLERS
        from ..payments.base import PaymentBase as LegacyPaymentBase
        
        payment_instance = None
        
        # 查找支付处理器（插件系统优先）
        pi = plugin_manager.get_plugin(handler)
        if pi and pi.instance and isinstance(pi.instance, PaymentPluginBase):
            payment_instance = pi.instance
        
        if not payment_instance:
            payment_class = PLUGIN_HANDLERS.get(handler)
            if not payment_class:
                from ..payments import get_payment_handler as legacy_get
                payment_class = legacy_get(handler)
            if not payment_class:
                return "unknown handler"
            
            result = await self.db.execute(
                select(PaymentMethod).where(PaymentMethod.handler == handler).limit(1)
            )
            payment_method = result.scalar_one_or_none()
            if not payment_method:
                return "payment not configured"
            
            config = json_lib.loads(payment_method.config) if payment_method.config else {}
            
            if issubclass(payment_class, PaymentPluginBase):
                from ..plugins.sdk.base import PluginMeta
                meta = PluginMeta(id=handler, name="", version="1.0.0", type="payment")
                payment_instance = payment_class(meta, config)
            elif issubclass(payment_class, LegacyPaymentBase):
                payment_instance = payment_class(config)
            else:
                return "invalid handler"
        
        # 验证回调
        callback_result = await payment_instance.verify_callback(data)
        if not callback_result.success:
            return payment_instance.get_callback_response(False)
        
        # 查找订单
        result = await self.db.execute(
            select(Order).where(Order.trade_no == callback_result.trade_no)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return payment_instance.get_callback_response(False)
        
        # 检查状态
        if order.status != 0:
            return payment_instance.get_callback_response(True)
        
        # 验证金额
        if abs(float(order.amount) - callback_result.amount) > 0.01:
            return payment_instance.get_callback_response(False)
        
        # 完成订单
        order.status = 1
        order.paid_at = datetime.now(timezone.utc)
        order.external_trade_no = callback_result.external_trade_no
        
        # 钩子
        await hooks.emit(Events.ORDER_PAID, {"order": order, "callback_data": data})
        
        secret = await self.deliver_order(order)
        await hooks.emit(Events.ORDER_DELIVERED, {"order": order, "secret": secret})
        
        # 佣金 + 累计消费（Decimal 精度）
        await self._process_commission(order)
        await self._accumulate_recharge(order)
        
        await self.db.commit()
        return payment_instance.get_callback_response(True)
    
    async def deliver_order(self, order: Order) -> str:
        """发货"""
        # 获取商品（加行锁，防止并发超卖）
        result = await self.db.execute(
            select(Commodity).where(Commodity.id == order.commodity_id).with_for_update()
        )
        commodity = result.scalar_one_or_none()
        
        if not commodity:
            order.secret = "商品不存在"
            order.delivery_status = 1
            return order.secret
        
        # 自动发货（卡密）
        if commodity.delivery_way == 0:
            secret = await self._pull_cards(order, commodity)
            order.secret = secret
            order.delivery_status = 1
        else:
            # 手动发货：检查库存是否足够
            if commodity.stock > 0 and commodity.stock < order.quantity:
                raise StockError("库存不足，请联系客服")
            # 扣减手动发货库存（stock > 0 才扣减，为 0 表示不限库存）
            if commodity.stock > 0:
                commodity.stock = commodity.stock - order.quantity
            order.secret = commodity.delivery_message or "正在发货中，请耐心等待"
            order.delivery_status = 0
        
        return order.secret
    
    async def _pull_cards(self, order: Order, commodity: Commodity) -> str:
        """拉取卡密（带行锁防并发超卖）"""
        # 预选卡密
        if order.card_id:
            result = await self.db.execute(
                select(Card)
                .where(Card.id == order.card_id)
                .where(Card.status == 0)
                .with_for_update(skip_locked=True)
            )
            card = result.scalar_one_or_none()
            if card:
                card.status = 1
                card.order_id = order.id
                card.sold_at = datetime.now(timezone.utc)
                return card.secret
            return "预选卡密已被售出"
        
        # 确定排序方式
        if commodity.delivery_auto_mode == 0:
            order_by = Card.id.asc()
        elif commodity.delivery_auto_mode == 1:
            order_by = func.random()
        else:
            order_by = Card.id.desc()
        
        # 查询卡密（FOR UPDATE SKIP LOCKED: 已被其它事务锁定的行直接跳过）
        query = (
            select(Card)
            .where(Card.commodity_id == order.commodity_id)
            .where(Card.status == 0)
        )
        
        if order.race:
            query = query.where(Card.race == order.race)
        
        query = query.order_by(order_by).limit(order.quantity).with_for_update(skip_locked=True)
        
        result = await self.db.execute(query)
        cards = result.scalars().all()
        
        if len(cards) < order.quantity:
            return "库存不足，请联系客服"
        
        secrets = []
        for card in cards:
            card.status = 1
            card.order_id = order.id
            card.sold_at = datetime.now(timezone.utc)
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
        if quantity <= 0:
            raise ValidationError("购买数量必须大于0")
            
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
        if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
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
            coupon.used_at = datetime.now(timezone.utc)
            if coupon.life <= 0:
                coupon.status = 1
        
        return coupon
    
    async def _pay_with_balance(
        self, order: Order, user: User, commodity: Commodity
    ):
        """余额支付（Decimal 精度）"""
        
        # 为了防并发双花，加排他悲观锁重新拿一遍用户的最新余额
        result = await self.db.execute(
            select(User).where(User.id == user.id).with_for_update()
        )
        locked_user = result.scalar_one_or_none()
        if not locked_user:
            raise NotFoundError("用户已不存在")
            
        balance = Decimal(str(locked_user.balance or 0))
        amount = Decimal(str(order.amount or 0))
        
        if balance < amount:
            raise InsufficientBalanceError(
                f"余额不足，当前余额: {balance}，需要: {amount}"
            )
        
        # 扣除余额
        locked_user.balance = balance - amount
        
        # 记录账单
        bill = Bill(
            user_id=locked_user.id,
            amount=amount,
            balance=locked_user.balance,
            type=0,
            currency=0,
            description=f"购买商品[{commodity.name}]",
            order_trade_no=order.trade_no,
        )
        self.db.add(bill)
        
        # 更新订单状态
        order.status = 1
        order.paid_at = datetime.now(timezone.utc)
    
    async def _create_payment(
        self,
        order: Order,
        payment_method: PaymentMethod,
        callback_url: str,
        return_url: str,
        client_ip: Optional[str],
        product_name: str = "",
    ):
        """
        创建第三方支付。
        支持插件系统 (PaymentPluginBase) 和旧模块 (PaymentBase)。
        """
        from ..plugins import plugin_manager, PAYMENT_HANDLERS
        
        handler_id = payment_method.handler
        payment_instance = None
        
        # 1. 先查插件系统中已启用的实例
        pi = plugin_manager.get_plugin(handler_id)
        if pi and pi.instance and isinstance(pi.instance, PaymentPluginBase):
            payment_instance = pi.instance
        
        # 2. 从插件注册表或旧模块查找类
        if not payment_instance:
            payment_class = PAYMENT_HANDLERS.get(handler_id)
            if not payment_class:
                from ..payments import get_payment_handler as legacy_get
                payment_class = legacy_get(handler_id)
            
            if not payment_class:
                raise PaymentError(f"支付方式 {handler_id} 未找到处理器")
            
            config = json_lib.loads(payment_method.config) if payment_method.config else {}
            
            from ..payments.base import PaymentBase as LegacyPaymentBase
            if issubclass(payment_class, PaymentPluginBase):
                from ..plugins.sdk.base import PluginMeta
                meta = PluginMeta(
                    id=handler_id, name=payment_method.name,
                    version="1.0.0", type="payment",
                )
                payment_instance = payment_class(meta, config)
            elif issubclass(payment_class, LegacyPaymentBase):
                payment_instance = payment_class(config)
            else:
                raise PaymentError(f"支付方式 {handler_id} 类型无效")
        
        # 3. 添加手续费
        amount = Decimal(str(order.amount))
        cost = Decimal(str(payment_method.cost or 0))
        if cost > 0:
            if payment_method.cost_type == 0:
                order.pay_cost = cost
            else:
                order.pay_cost = (amount * cost).quantize(Decimal("0.01"))
            amount += Decimal(str(order.pay_cost))
            order.amount = amount.quantize(Decimal("0.01"))
        
        # 4. 拼接回调 URL
        cb = callback_url.rstrip("/")
        notify_url = f"{cb}/api/v1/payments/{handler_id}/callback"
        sync_return = f"{cb}/api/v1/payments/{handler_id}/return"
        
        # 5. 钩子：支付创建前（可拦截）
        ctx = await hooks.emit(Events.PAYMENT_CREATING, {
            "order": order,
            "payment_method": payment_method,
            "amount": float(order.amount),
        })
        if ctx.cancelled:
            raise PaymentError(ctx.cancel_reason or "支付创建被拦截")
        
        # 6. 调用支付接口
        return await payment_instance.create_payment(
            trade_no=order.trade_no,
            amount=float(order.amount),
            callback_url=notify_url,
            return_url=sync_return,
            channel=payment_method.code or "alipay",
            client_ip=client_ip,
            product_name=product_name,
        )
    
    async def _process_commission(self, order: Order):
        """处理分销佣金（Decimal 精度）"""
        if not order.from_user_id:
            return
        
        result = await self.db.execute(
            select(User).where(User.id == order.from_user_id)
        )
        promoter = result.scalar_one_or_none()
        if not promoter:
            return
        
        # 动态获取分销返佣比例，默认 10%
        from ..models.config import SystemConfig
        rate_str = await SystemConfig.get_value(self.db, "commission_rate", "0.1")
        try:
            rebate_rate = Decimal(rate_str)
        except:
            rebate_rate = Decimal("0.1")
            
        rebate = (Decimal(str(order.amount)) * rebate_rate).quantize(Decimal("0.01"))
        
        if rebate >= Decimal("0.01"):
            promoter.balance = Decimal(str(promoter.balance)) + rebate
            order.rebate = rebate
            
            bill = Bill(
                user_id=promoter.id,
                amount=rebate,
                balance=promoter.balance,
                type=1,
                description=f"推广返佣[{order.trade_no}]",
                order_trade_no=order.trade_no,
            )
            self.db.add(bill)
    
    async def _accumulate_recharge(self, order: Order):
        """累计用户消费（Decimal 精度）"""
        if not order.user_id:
            return
        result = await self.db.execute(
            select(User).where(User.id == order.user_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.total_recharge = (
                Decimal(str(user.total_recharge or 0))
                + Decimal(str(order.amount))
            )
