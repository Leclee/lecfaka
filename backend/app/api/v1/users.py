"""
用户接口
"""

import json as json_lib
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ..deps import DbSession, CurrentUser
from ...models.user import User, UserGroup
from ...models.order import Order
from ...models.bill import Bill
from ...models.config import SystemConfig
from ...models.payment import PaymentMethod
from ...models.recharge import RechargeOrder
from ...core.exceptions import NotFoundError, ValidationError
from ...payments import get_payment_handler as legacy_get_handler
from ...plugins import plugin_manager, PAYMENT_HANDLERS
from ...plugins.sdk.payment_base import PaymentPluginBase


router = APIRouter()


# ============== Schemas ==============

class UpdateUserRequest(BaseModel):
    """更新用户信息请求"""
    avatar: Optional[str] = Field(None, description="头像URL")
    alipay: Optional[str] = Field(None, description="支付宝账号")
    wechat: Optional[str] = Field(None, description="微信账号")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class OrderListItem(BaseModel):
    """订单列表项"""
    trade_no: str
    amount: float
    quantity: int
    status: int
    delivery_status: int
    created_at: str
    commodity_name: Optional[str]


class BillListItem(BaseModel):
    """账单列表项"""
    id: int
    amount: float
    balance: float
    type: int
    description: str
    created_at: str


# ============== APIs ==============

@router.get("/me", summary="获取当前用户信息")
async def get_current_user(
    user: CurrentUser,
    db: DbSession,
):
    """获取当前用户详细信息"""
    # 统计推广人数
    referral_count_result = await db.execute(
        select(func.count()).where(User.parent_id == user.id)
    )
    referral_count = referral_count_result.scalar() or 0
    
    # 统计总收入(佣金)
    income_result = await db.execute(
        select(func.coalesce(func.sum(Bill.amount), 0)).where(
            Bill.user_id == user.id,
            Bill.type == 1  # 收入
        )
    )
    total_income = float(income_result.scalar() or 0)
    
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "avatar": user.avatar,
        "balance": float(user.balance),
        "coin": float(user.coin),
        "total_recharge": float(user.total_recharge),
        "total_income": total_income,
        "is_admin": user.is_admin,
        "business_level": user.business_level,
        "alipay": user.alipay,
        "wechat": user.wechat,
        "qq": user.qq,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "last_login_ip": user.last_login_ip,
        "parent_id": user.parent_id,
        "merchant_id": user.id + 1000,
        "merchant_key": "",
        "referral_count": referral_count,
    }


@router.put("/me", summary="更新用户信息")
async def update_current_user(
    request: UpdateUserRequest,
    user: CurrentUser,
    db: DbSession,
):
    """更新当前用户信息"""
    
    if request.avatar is not None:
        user.avatar = request.avatar
    if request.alipay is not None:
        user.alipay = request.alipay
    if request.wechat is not None:
        user.wechat = request.wechat
    
    return {"message": "更新成功"}


@router.post("/me/password", summary="修改密码")
async def change_password(
    request: ChangePasswordRequest,
    user: CurrentUser,
    db: DbSession,
):
    """修改密码"""
    from ...core.security import verify_password, get_password_hash
    
    # 验证旧密码
    if not verify_password(request.old_password, user.password_hash, user.salt):
        from ...core.exceptions import ValidationError
        raise ValidationError("旧密码错误")
    
    # 设置新密码
    password_hash, salt = get_password_hash(request.new_password)
    user.password_hash = password_hash
    user.salt = salt
    
    return {"message": "密码修改成功"}


@router.get("/me/orders", summary="获取我的订单")
async def get_my_orders(
    user: CurrentUser,
    db: DbSession,
    status: Optional[int] = Query(None, description="订单状态"),
    trade_no: Optional[str] = Query(None, description="订单号"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """获取当前用户的订单列表"""
    from ...models.commodity import Commodity
    from ...models.card import Card
    
    try:
        query = select(Order).where(Order.user_id == user.id)
        
        if status is not None:
            query = query.where(Order.status == status)
        
        if trade_no:
            query = query.where(Order.trade_no.contains(trade_no))
        
        query = query.order_by(Order.created_at.desc())
        
        # 统计总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # 分页
        query = query.offset((page - 1) * limit).limit(limit)
        
        result = await db.execute(query)
        orders = result.scalars().all()
        
        if not orders:
            return {"total": total, "page": page, "limit": limit, "items": []}
        
        # 批量预加载商品信息（避免 N+1）
        from ...models.commodity import Commodity
        from ...models.card import Card
        commodity_ids = list({o.commodity_id for o in orders})
        payment_ids = list({o.payment_id for o in orders if o.payment_id})
        order_ids = [o.id for o in orders]
        
        commodity_map = {}
        if commodity_ids:
            c_result = await db.execute(
                select(Commodity.id, Commodity.name, Commodity.cover, Commodity.delivery_way, Commodity.leave_message)
                .where(Commodity.id.in_(commodity_ids))
            )
            for row in c_result.all():
                commodity_map[row[0]] = row
        
        payment_map = {}
        if payment_ids:
            from ...models.payment import PaymentMethod
            p_result = await db.execute(
                select(PaymentMethod.id, PaymentMethod.name).where(PaymentMethod.id.in_(payment_ids))
            )
            for row in p_result.all():
                payment_map[row[0]] = row[1]
        
        # 批量预加载卡密信息（只查已发货的订单）
        delivered_order_ids = [o.id for o in orders if o.delivery_status == 1]
        cards_map = {}
        if delivered_order_ids:
            cards_result = await db.execute(
                select(Card.order_id, Card.secret).where(Card.order_id.in_(delivered_order_ids))
            )
            for row in cards_result.all():
                cards_map.setdefault(row[0], []).append(row[1])
        
        items = []
        for order in orders:
            commodity = commodity_map.get(order.commodity_id)
            commodity_name = commodity[1] if commodity else None
            commodity_cover = commodity[2] if commodity else None
            delivery_way = commodity[3] if commodity else 0
            leave_message = commodity[4] if commodity else None
            payment_method_name = payment_map.get(order.payment_id)
            
            cards = cards_map.get(order.id, [])
            cards_info = "\n".join(c for c in cards if c) or None
            
            items.append({
                "trade_no": order.trade_no,
                "amount": float(order.amount),
                "quantity": order.quantity,
                "status": order.status,
                "delivery_status": order.delivery_status,
                "delivery_way": delivery_way or 0,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "commodity_name": commodity_name,
                "commodity_cover": commodity_cover,
                "contact": order.contact,
                "payment_method": payment_method_name,
                "cards_info": cards_info,
                "leave_message": leave_message,
            })
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "items": items,
        }
    except Exception as e:
        import traceback
        print(f"[ERROR] get_my_orders: {e}")
        traceback.print_exc()
        raise



@router.get("/me/bills", summary="获取我的账单")
async def get_my_bills(
    user: CurrentUser,
    db: DbSession,
    type: Optional[int] = Query(None, description="账单类型 0=支出 1=收入"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取当前用户的账单列表"""
    
    query = select(Bill).where(Bill.user_id == user.id)
    
    if type is not None:
        query = query.where(Bill.type == type)
    
    query = query.order_by(Bill.created_at.desc())
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    bills = result.scalars().all()
    
    items = [
        {
            "id": bill.id,
            "amount": float(bill.amount),
            "balance": float(bill.balance),
            "type": bill.type,
            "description": bill.description,
            "created_at": bill.created_at.isoformat() if bill.created_at else None,
        }
        for bill in bills
    ]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items,
    }


@router.get("/me/invite-link", summary="获取推广链接")
async def get_invite_link(
    user: CurrentUser,
    request: Request,
):
    """获取用户的推广链接"""
    from ...utils.request import get_base_url
    
    base_url = get_base_url(request)
    
    return {
        "invite_code": str(user.id),
        "invite_link": f"{base_url}?from={user.id}",
    }


@router.get("/me/referrals", summary="获取我的下级")
async def get_my_referrals(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """获取当前用户邀请的下级列表"""
    
    query = select(User).where(User.parent_id == user.id)
    query = query.order_by(User.created_at.desc())
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    items = [
        {
            "id": u.id,
            "username": u.username,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "total_recharge": float(u.total_recharge),
        }
        for u in users
    ]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items,
    }


@router.post("/me/reset-merchant-key", summary="重置商户密钥")
async def reset_merchant_key(
    user: CurrentUser,
    db: DbSession,
):
    """重置商户密钥"""
    from ...core.security import generate_api_key
    
    # 生成新的商户密钥并持久化到数据库
    new_key = generate_api_key()
    user.api_key = new_key
    await db.flush()
    
    return {
        "merchant_key": new_key,
        "message": "商户密钥已重置",
    }


class RechargeRequest(BaseModel):
    """Recharge request"""
    amount: float = Field(..., gt=0, description="Recharge amount")
    payment_id: int = Field(..., description="Payment method ID")


def _parse_recharge_bonus_config(raw_config: str) -> List[dict]:
    """Parse recharge bonus config: amount-bonus per line."""
    items: List[dict] = []
    for line in (raw_config or "").splitlines():
        line = line.strip()
        if not line or "-" not in line:
            continue
        left, right = line.split("-", 1)
        try:
            amount = float(left.strip())
            bonus = float(right.strip())
            if amount > 0 and bonus > 0:
                items.append({"amount": amount, "bonus": bonus})
        except ValueError:
            continue
    items.sort(key=lambda x: x["amount"])
    return items


async def _create_payment_instance(payment: PaymentMethod):
    """Create payment handler instance (plugin first, legacy fallback)."""
    handler_id = payment.handler
    payment_instance = None

    pi = plugin_manager.get_plugin(handler_id)
    if pi and pi.instance and isinstance(pi.instance, PaymentPluginBase):
        payment_instance = pi.instance

    if payment_instance:
        return payment_instance

    payment_class = PAYMENT_HANDLERS.get(handler_id)
    if not payment_class:
        payment_class = legacy_get_handler(handler_id)
    if not payment_class:
        raise ValidationError(f"Payment handler not found: {handler_id}")

    try:
        config = json_lib.loads(payment.config) if payment.config else {}
    except Exception:
        config = {}

    from ...payments.base import PaymentBase as LegacyPaymentBase
    from ...plugins.sdk.base import PluginMeta

    if issubclass(payment_class, PaymentPluginBase):
        meta = PluginMeta(
            id=handler_id,
            name=payment.name,
            version="1.0.0",
            type="payment",
        )
        return payment_class(meta, config)
    if issubclass(payment_class, LegacyPaymentBase):
        return payment_class(config)
    raise ValidationError(f"Invalid payment handler type: {handler_id}")


@router.get("/me/recharge/options", summary="Get recharge options")
async def get_recharge_options(
    user: CurrentUser,
    db: DbSession,
):
    """Return recharge page data: payments, groups, and recharge config."""
    payment_result = await db.execute(
        select(PaymentMethod)
        .where(PaymentMethod.status == 1)
        .where(PaymentMethod.recharge == 1)
        .where(PaymentMethod.handler != "#balance")
        .order_by(PaymentMethod.sort.asc(), PaymentMethod.id.asc())
    )
    payments = payment_result.scalars().all()

    group_result = await db.execute(
        select(UserGroup)
        .where(UserGroup.status == 1)
        .order_by(UserGroup.min_recharge.asc(), UserGroup.id.asc())
    )
    groups = group_result.scalars().all()

    cfg_result = await db.execute(
        select(SystemConfig.key, SystemConfig.value).where(
            SystemConfig.key.in_(
                [
                    "recharge_min",
                    "recharge_max",
                    "recharge_bonus_enabled",
                    "recharge_bonus_config",
                ]
            )
        )
    )
    cfg_map = {row.key: row.value for row in cfg_result.all()}

    recharge_min = float(cfg_map.get("recharge_min") or 1)
    recharge_max = float(cfg_map.get("recharge_max") or 1000)
    bonus_enabled = str(cfg_map.get("recharge_bonus_enabled") or "0") in {"1", "true", "True"}
    bonus_items = _parse_recharge_bonus_config(cfg_map.get("recharge_bonus_config") or "")

    return {
        "payments": [
            {
                "id": p.id,
                "name": p.name,
                "icon": p.icon,
                "handler": p.handler,
                "code": p.code,
            }
            for p in payments
        ],
        "user_groups": [
            {
                "id": g.id,
                "name": g.name,
                "discount": float(g.discount),
                "min_recharge": float(g.min_recharge),
                "icon": g.icon,
            }
            for g in groups
        ],
        "recharge_config": {
            "min": recharge_min,
            "max": recharge_max,
            "bonus_enabled": bonus_enabled,
            "bonus": bonus_items,
        },
    }


@router.post("/me/recharge", summary="Create recharge order")
async def create_recharge(
    request: RechargeRequest,
    user: CurrentUser,
    db: DbSession,
    req: Request,
):
    """Create recharge order and initialize payment."""
    import uuid
    from ...utils.request import get_callback_base_url

    amount = Decimal(str(request.amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    payment_result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.id == request.payment_id)
    )
    payment = payment_result.scalar_one_or_none()
    if not payment:
        raise NotFoundError("Payment method not found")
    if payment.status != 1 or payment.recharge != 1:
        raise ValidationError("This payment method does not support recharge")
    if payment.handler == "#balance":
        raise ValidationError("Balance payment is not allowed for recharge")

    cfg_result = await db.execute(
        select(SystemConfig.key, SystemConfig.value).where(
            SystemConfig.key.in_(["recharge_min", "recharge_max"])
        )
    )
    cfg_map = {row.key: row.value for row in cfg_result.all()}
    recharge_min = float(cfg_map.get("recharge_min") or 1)
    recharge_max = float(cfg_map.get("recharge_max") or 1000)
    if float(amount) < recharge_min:
        raise ValidationError(f"Minimum recharge amount is {recharge_min}")
    if recharge_max > 0 and float(amount) > recharge_max:
        raise ValidationError(f"Maximum recharge amount is {recharge_max}")

    fee = Decimal("0")
    cost = Decimal(str(payment.cost or 0))
    if cost > 0:
        if payment.cost_type == 0:
            fee = cost
        else:
            fee = (amount * cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    actual_amount = (amount - fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if actual_amount <= 0:
        raise ValidationError("Actual recharge amount must be greater than 0")

    trade_no = f"R{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    recharge = RechargeOrder(
        trade_no=trade_no,
        user_id=user.id,
        payment_id=payment.id,
        amount=amount,
        actual_amount=actual_amount,
        status=0,
        create_ip=req.client.host if req.client else None,
    )
    db.add(recharge)
    await db.flush()

    base_url = get_callback_base_url(req).rstrip("/")
    notify_url = f"{base_url}/api/v1/payments/{payment.handler}/callback"
    sync_return = f"{base_url}/api/v1/payments/{payment.handler}/return"

    try:
        payment_instance = await _create_payment_instance(payment)
        payment_create_result = await payment_instance.create_payment(
            trade_no=trade_no,
            amount=float(amount),
            callback_url=notify_url,
            return_url=sync_return,
            channel=payment.code or "alipay",
            client_ip=req.client.host if req.client else None,
            product_name="Account Recharge",
        )
        if not payment_create_result.success:
            raise ValidationError(f"Failed to create recharge payment: {payment_create_result.error_msg}")

        payment_url = payment_create_result.payment_url
        payment_type = payment_create_result.payment_type.value
        extra = payment_create_result.extra or {}

        if payment_type == "qrcode" and payment_create_result.qrcode_url:
            payment_url = payment_create_result.qrcode_url
            extra["qrcode_url"] = payment_create_result.qrcode_url

        if payment_create_result.form_action:
            payment_url = payment_create_result.form_action
            payment_type = "form"
            extra = {"form_data": payment_create_result.form_data}

        await db.commit()
    except Exception:
        await db.rollback()
        raise

    return {
        "trade_no": trade_no,
        "amount": float(amount),
        "actual_amount": float(actual_amount),
        "payment_url": payment_url,
        "payment_type": payment_type,
        "extra": extra,
    }


@router.get("/me/recharge/{trade_no}", summary="Get recharge order status")
async def get_recharge_order_status(
    trade_no: str,
    user: CurrentUser,
    db: DbSession,
):
    """Used by frontend QR code polling."""
    result = await db.execute(
        select(RechargeOrder)
        .where(RechargeOrder.trade_no == trade_no)
        .where(RechargeOrder.user_id == user.id)
    )
    recharge = result.scalar_one_or_none()
    if not recharge:
        raise NotFoundError("Recharge order not found")

    return {
        "trade_no": recharge.trade_no,
        "status": recharge.status,
        "amount": float(recharge.amount),
        "actual_amount": float(recharge.actual_amount),
        "payment_id": recharge.payment_id,
        "external_trade_no": recharge.external_trade_no,
        "created_at": recharge.created_at.isoformat() if recharge.created_at else None,
        "paid_at": recharge.paid_at.isoformat() if recharge.paid_at else None,
    }


class WithdrawRequest(BaseModel):
    """Withdraw request"""
    amount: float = Field(..., gt=0, description="Withdraw amount")
    method: str = Field(..., description="Withdraw method: alipay/wechat")


@router.get("/me/withdrawals", summary="获取提现记录")
async def get_my_withdrawals(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
):
    """获取当前用户的提现记录"""
    from ...models.withdrawal import Withdrawal
    
    query = select(Withdrawal).where(Withdrawal.user_id == user.id)
    query = query.order_by(Withdrawal.created_at.desc())
    
    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    query = query.offset((page - 1) * limit).limit(limit)
    
    result = await db.execute(query)
    withdrawals = result.scalars().all()
    
    items = [
        {
            "id": w.id,
            "amount": float(w.amount),
            "fee": float(w.fee) if w.fee else 0,
            "actual_amount": float(w.actual_amount) if w.actual_amount else float(w.amount),
            "method": w.method,
            "account": w.account,
            "status": w.status,
            "created_at": w.created_at.isoformat() if w.created_at else None,
            "processed_at": w.processed_at.isoformat() if w.processed_at else None,
        }
        for w in withdrawals
    ]
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "items": items,
    }


@router.post("/me/withdraw", summary="申请提现")
async def create_withdrawal(
    request: WithdrawRequest,
    user: CurrentUser,
    db: DbSession,
):
    """申请提现"""
    from ...models.withdrawal import Withdrawal
    from ...core.exceptions import ValidationError
    
    # 获取提现手续费和最低金额
    from ...models.config import SystemConfig
    fee_result = await db.execute(
        select(SystemConfig.value).where(SystemConfig.key == "withdraw_fee")
    )
    fee = float(fee_result.scalar() or 5)
    
    min_result = await db.execute(
        select(SystemConfig.value).where(SystemConfig.key == "withdraw_min")
    )
    min_amount = float(min_result.scalar() or 100)
    
    if request.amount < min_amount:
        raise ValidationError(f"最低提现金额为 {min_amount} 元")
    
    actual_amount = request.amount - fee
    if actual_amount <= 0:
        raise ValidationError("提现金额扣除手续费后不能为零或负数")
    
    # 为了防并发超提，加排他悲观锁重新读取用户最新硬币余额
    result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = result.scalar_one_or_none()
    if not locked_user:
        raise NotFoundError("用户不存在")
    
    # 加锁后再次检查余额
    if float(locked_user.coin or 0) < request.amount:
        raise ValidationError("硬币余额不足")
    
    # 获取提现账户
    account = locked_user.alipay if request.method == "alipay" else locked_user.wechat
    if not account:
        raise ValidationError(f"请先在安全中心设置{request.method}账号")
    
    # 扣除硬币
    locked_user.coin = float(locked_user.coin or 0) - request.amount
    
    # 创建提现记录
    withdrawal = Withdrawal(
        user_id=locked_user.id,
        amount=request.amount,
        fee=fee,
        actual_amount=actual_amount,
        method=request.method,
        account=account,
        status=0,
    )
    db.add(withdrawal)
    await db.flush()
    
    return {
        "id": withdrawal.id,
        "amount": request.amount,
        "fee": fee,
        "actual_amount": actual_amount,
        "message": "提现申请已提交",
    }
