"""
支付回调接口
"""

import json
import logging
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Request
from fastapi, timezone.responses import PlainTextResponse
from sqlalchemy import select, func

from ..deps import DbSession
from ...models.order import Order
from ...models.card import Card
from ...models.commodity import Commodity
from ...models.user import User
from ...models.payment import PaymentMethod
from ...models.recharge import RechargeOrder
from ...models.bill import Bill
from ...payments import get_payment_handler as legacy_get_handler
from ...plugins import plugin_manager, PAYMENT_HANDLERS
from ...plugins.sdk.payment_base import PaymentPluginBase
from ...plugins.sdk.hooks import hooks, Events

logger = logging.getLogger("payments.callback")
router = APIRouter()


async def _handle_callback(handler: str, request: Request, db):
    """通用支付回调处理"""
    
    # 1. 获取回调数据
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)
    data.update(dict(request.query_params))
    
    logger.info(f"Payment callback [{handler}]: {data}")
    
    # 2. 查找支付处理器并实例化
    payment_instance = None
    
    # 先查插件系统中已启用的实例
    pi = plugin_manager.get_plugin(handler)
    if pi and pi.instance and isinstance(pi.instance, PaymentPluginBase):
        payment_instance = pi.instance
    
    if not payment_instance:
        # 从插件注册表查找类
        payment_class = PAYMENT_HANDLERS.get(handler)
        if not payment_class:
            # Fallback 旧模块
            payment_class = legacy_get_handler(handler)
        
        if not payment_class:
            return "unknown handler"
        
        # 获取配置
        result = await db.execute(
            select(PaymentMethod).where(PaymentMethod.handler == handler).limit(1)
        )
        payment_method = result.scalar_one_or_none()
        if not payment_method:
            return "payment not configured"
        
        config = json.loads(payment_method.config) if payment_method.config else {}
        
        # 实例化
        from ...payments.base import PaymentBase as LegacyPaymentBase
        from ...plugins.sdk.base import PluginMeta
        
        if issubclass(payment_class, PaymentPluginBase):
            meta = PluginMeta(id=handler, name="", version="1.0.0", type="payment")
            payment_instance = payment_class(meta, config)
        elif issubclass(payment_class, LegacyPaymentBase):
            payment_instance = payment_class(config)
        else:
            return "invalid handler"
    
    # 3. 验证回调签名和数据
    callback_result = await payment_instance.verify_callback(data)
    if not callback_result.success:
        logger.warning(f"Callback verify failed [{handler}]: {callback_result.error_msg}")
        return payment_instance.get_callback_response(False)
    
    # 4. 查找商品订单或充值订单
    result = await db.execute(
        select(Order).where(Order.trade_no == callback_result.trade_no)
    )
    order = result.scalar_one_or_none()

    recharge_result = await db.execute(
        select(RechargeOrder).where(RechargeOrder.trade_no == callback_result.trade_no)
    )
    recharge_order = recharge_result.scalar_one_or_none()

    if not order and not recharge_order:
        logger.warning(f"Order not found: {callback_result.trade_no}")
        return payment_instance.get_callback_response(False)

    # 充值订单回调处理（无商品发货流程）
    if recharge_order and not order:
        if recharge_order.status != 0:
            return payment_instance.get_callback_response(True)

        if abs(float(recharge_order.amount) - callback_result.amount) > 0.01:
            logger.warning(
                f"Recharge amount mismatch: order={recharge_order.amount}, callback={callback_result.amount}"
            )
            return payment_instance.get_callback_response(False)

        user_result = await db.execute(
            select(User).where(User.id == recharge_order.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            logger.warning(f"Recharge user not found: {recharge_order.user_id}")
            return payment_instance.get_callback_response(False)

        recharge_order.status = 1
        recharge_order.paid_at = datetime.now(timezone.utc)
        recharge_order.external_trade_no = callback_result.external_trade_no

        user.balance = Decimal(str(user.balance or 0)) + Decimal(str(recharge_order.actual_amount or 0))
        user.total_recharge = Decimal(str(user.total_recharge or 0)) + Decimal(str(recharge_order.amount or 0))

        bill = Bill(
            user_id=user.id,
            amount=Decimal(str(recharge_order.actual_amount or 0)),
            balance=Decimal(str(user.balance or 0)),
            type=1,
            currency=0,
            description=f"充值到账[{recharge_order.trade_no}]",
            order_trade_no=recharge_order.trade_no,
        )
        db.add(bill)

        await hooks.emit(
            Events.PAYMENT_CALLBACK,
            {
                "recharge_order": recharge_order,
                "handler": handler,
                "callback_data": data,
            },
        )
        await hooks.emit(
            Events.USER_RECHARGED,
            {
                "user": user,
                "recharge_order": recharge_order,
                "amount": float(recharge_order.actual_amount or 0),
            },
        )

        await db.commit()
        logger.info(f"Recharge order {recharge_order.trade_no} paid successfully")
        return payment_instance.get_callback_response(True)
    
    # 5. 避免重复处理
    if order.status != 0:
        return payment_instance.get_callback_response(True)
    
    # 6. 验证金额
    if abs(float(order.amount) - callback_result.amount) > 0.01:
        logger.warning(
            f"Amount mismatch: order={order.amount}, callback={callback_result.amount}"
        )
        return payment_instance.get_callback_response(False)
    
    # 7. 更新订单状态为已支付
    order.status = 1
    order.paid_at = datetime.now(timezone.utc)
    order.external_trade_no = callback_result.external_trade_no
    
    # 8. 钩子：支付回调 + 支付成功
    await hooks.emit(Events.PAYMENT_CALLBACK, {"order": order, "handler": handler, "callback_data": data})
    await hooks.emit(Events.ORDER_PAID, {"order": order, "callback_data": data})
    
    # 9. 发货（委托 OrderService，带行锁防并发超卖）
    from ...services.order import OrderService
    svc = OrderService(db)
    secret = await svc.deliver_order(order)
    
    # 10. 钩子：发货完成
    await hooks.emit(Events.ORDER_DELIVERED, {"order": order, "secret": secret})
    
    # 11. 处理分销佣金（Decimal 精度）
    await svc._process_commission(order)
    
    # 12. 累计用户消费（Decimal 精度）
    await svc._accumulate_recharge(order)
    
    await db.commit()
    
    logger.info(f"Order {order.trade_no} paid and delivered successfully")
    return payment_instance.get_callback_response(True)


@router.post("/{handler}/callback", response_class=PlainTextResponse, summary="支付回调")
async def payment_callback(handler: str, request: Request, db: DbSession):
    """通用支付回调接口（POST）"""
    return await _handle_callback(handler, request, db)


@router.get("/{handler}/callback", response_class=PlainTextResponse, summary="支付回调(GET)")
async def payment_callback_get(handler: str, request: Request, db: DbSession):
    """通用支付回调接口（GET，部分支付平台使用）"""
    return await _handle_callback(handler, request, db)


@router.get("/{handler}/return", summary="支付同步跳转")
async def payment_return(handler: str, request: Request, db: DbSession):
    """
    支付完成后浏览器同步跳转 (return_url)。
    验证签名、处理订单，然后 302 跳转到前端订单详情页。
    """
    from fastapi.responses import RedirectResponse
    from ...utils.request import get_base_url

    # 获取参数
    data = dict(request.query_params)
    logger.info(f"Payment return [{handler}]: {data}")

    out_trade_no = data.get("out_trade_no", "")
    trade_status = data.get("trade_status", "")

    # 构建前端跳转 URL（商品单 -> /query，充值单 -> /user/recharge）
    base_url = get_base_url(request)
    frontend_url = f"{base_url}/query?trade_no={out_trade_no}"
    if out_trade_no:
        recharge_result = await db.execute(
            select(RechargeOrder.id).where(RechargeOrder.trade_no == out_trade_no).limit(1)
        )
        if recharge_result.scalar_one_or_none():
            frontend_url = f"{base_url}/user/recharge?trade_no={out_trade_no}"

    # 如果支付成功，尝试走回调逻辑处理订单
    if trade_status == "TRADE_SUCCESS" and out_trade_no:
        try:
            result = await _handle_callback(handler, request, db)
            logger.info(f"Payment return callback result: {result}")
        except Exception as e:
            logger.error(f"Payment return callback error: {e}")

    # 无论如何都跳转到前端订单页
    return RedirectResponse(url=frontend_url, status_code=302)
