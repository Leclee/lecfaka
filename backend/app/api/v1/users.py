"""
用户接口
"""

from typing import Optional, List
from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, func

from ..deps import DbSession, CurrentUser
from ...models.user import User
from ...models.order import Order
from ...models.bill import Bill


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
    import hashlib
    
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
    
    # 生成商户密钥
    merchant_key = hashlib.sha256(
        f"{user.id}-{user.username}-{user.created_at}".encode()
    ).hexdigest()[:16].upper()
    
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
        "merchant_key": merchant_key,
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
        
        items = []
        for order in orders:
            # 获取商品信息
            commodity_name = None
            commodity_cover = None
            delivery_way = 0
            leave_message = None
            
            try:
                commodity_result = await db.execute(
                    select(
                        Commodity.name, 
                        Commodity.cover, 
                        Commodity.delivery_way,
                        Commodity.leave_message
                    ).where(Commodity.id == order.commodity_id)
                )
                commodity = commodity_result.first()
                if commodity:
                    commodity_name = commodity[0]
                    commodity_cover = commodity[1]
                    delivery_way = commodity[2] or 0
                    leave_message = commodity[3]
            except Exception:
                pass
            
            # 获取支付方式名称
            payment_method_name = None
            if order.payment_id:
                try:
                    from ...models.payment import PaymentMethod
                    payment_result = await db.execute(
                        select(PaymentMethod.name).where(PaymentMethod.id == order.payment_id)
                    )
                    payment_method_name = payment_result.scalar()
                except Exception:
                    pass
            
            # 获取卡密信息（已发货的订单）
            cards_info = None
            if order.delivery_status == 1:
                try:
                    cards_result = await db.execute(
                        select(Card.secret).where(Card.order_id == order.id)
                    )
                    cards = [c for c in cards_result.scalars().all() if c]
                    cards_info = "\n".join(cards) if cards else None
                except Exception:
                    pass
            
            items.append({
                "trade_no": order.trade_no,
                "amount": float(order.amount),
                "quantity": order.quantity,
                "status": order.status,
                "delivery_status": order.delivery_status,
                "delivery_way": delivery_way,
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
    import hashlib
    from datetime import datetime
    
    # 生成新的商户密钥
    new_key = hashlib.sha256(
        f"{user.id}-{user.username}-{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()[:16].upper()
    
    return {
        "merchant_key": new_key,
        "message": "商户密钥已重置",
    }


class RechargeRequest(BaseModel):
    """充值请求"""
    amount: float = Field(..., gt=0, description="充值金额")
    payment_id: int = Field(..., description="支付方式ID")


class WithdrawRequest(BaseModel):
    """提现请求"""
    amount: float = Field(..., gt=0, description="提现金额")
    method: str = Field(..., description="提现方式 alipay/wechat")


@router.post("/me/recharge", summary="余额充值")
async def create_recharge(
    request: RechargeRequest,
    user: CurrentUser,
    db: DbSession,
):
    """创建充值订单"""
    from ...models.recharge import RechargeOrder
    from ...models.payment import PaymentMethod
    import uuid
    from datetime import datetime
    
    # 检查支付方式
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.id == request.payment_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        from ...core.exceptions import NotFoundError
        raise NotFoundError("支付方式不存在")
    
    # 创建充值订单
    trade_no = f"R{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
    
    recharge = RechargeOrder(
        trade_no=trade_no,
        user_id=user.id,
        amount=request.amount,
        payment_id=request.payment_id,
        status=0,
    )
    db.add(recharge)
    await db.flush()
    
    # TODO: 调用支付接口获取支付链接
    
    return {
        "trade_no": trade_no,
        "amount": request.amount,
        "payment_url": None,  # 实际应返回支付链接
    }


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
    
    # 检查余额（硬币）
    if user.coin < request.amount:
        raise ValidationError("硬币余额不足")
    
    # 获取提现手续费
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
    
    # 获取提现账户
    account = user.alipay if request.method == "alipay" else user.wechat
    if not account:
        raise ValidationError(f"请先在安全中心设置{request.method}账号")
    
    # 扣除硬币
    user.coin = user.coin - request.amount
    
    # 创建提现记录
    withdrawal = Withdrawal(
        user_id=user.id,
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
