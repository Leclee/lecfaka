"""
管理后台 - 系统设置
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import select

from ...deps import DbSession, CurrentAdmin
from ....models.config import SystemConfig
from ....models.payment import PaymentMethod
from ....core.exceptions import NotFoundError


router = APIRouter()


# 默认配置项
DEFAULT_CONFIGS = [
    # 基本设置
    {"key": "site_name", "value": "LecFaka发卡系统", "type": "text", "group": "basic", "description": "店铺名称"},
    {"key": "site_title", "value": "LecFaka - 自动发卡平台", "type": "text", "group": "basic", "description": "网站标题"},
    {"key": "site_keywords", "value": "发卡,自动发卡,卡密", "type": "text", "group": "basic", "description": "关键词"},
    {"key": "site_description", "value": "专业的自动发卡平台", "type": "text", "group": "basic", "description": "站点描述"},
    {"key": "site_logo", "value": "", "type": "image", "group": "basic", "description": "网站LOGO"},
    {"key": "site_favicon", "value": "", "type": "image", "group": "basic", "description": "网站图标"},
    {"key": "site_bg_pc", "value": "", "type": "image", "group": "basic", "description": "PC背景图片"},
    {"key": "site_bg_mobile", "value": "", "type": "image", "group": "basic", "description": "手机背景图片"},
    {"key": "site_notice", "value": "", "type": "textarea", "group": "basic", "description": "店铺公告"},
    {"key": "register_type", "value": "username_email", "type": "select", "group": "basic", "description": "注册方式"},
    {"key": "register_captcha", "value": "1", "type": "boolean", "group": "basic", "description": "注册人机验证"},
    {"key": "register_sms_captcha", "value": "0", "type": "boolean", "group": "basic", "description": "注册手机验证码"},
    {"key": "register_email_captcha", "value": "1", "type": "boolean", "group": "basic", "description": "注册邮箱验证码"},
    {"key": "login_captcha", "value": "1", "type": "boolean", "group": "basic", "description": "登录验证码"},
    {"key": "order_captcha", "value": "1", "type": "boolean", "group": "basic", "description": "下单验证码"},
    {"key": "register_enabled", "value": "1", "type": "boolean", "group": "basic", "description": "开启注册"},
    {"key": "register_username_length", "value": "6", "type": "number", "group": "basic", "description": "注册用户名长度"},
    {"key": "password_reset_type", "value": "email", "type": "select", "group": "basic", "description": "找回密码方式"},
    {"key": "session_timeout", "value": "86400", "type": "number", "group": "basic", "description": "会话保持时间(秒)"},
    {"key": "maintenance_mode", "value": "0", "type": "boolean", "group": "basic", "description": "店铺维护"},
    {"key": "maintenance_notice", "value": "我们正在升级，请耐心等待完成。", "type": "textarea", "group": "basic", "description": "维护公告"},
    
    # 短信设置
    {"key": "sms_platform", "value": "aliyun", "type": "select", "group": "sms", "description": "短信平台"},
    {"key": "sms_access_key_id", "value": "", "type": "text", "group": "sms", "description": "AccessKeyId"},
    {"key": "sms_access_key_secret", "value": "", "type": "password", "group": "sms", "description": "AccessKeySecret"},
    {"key": "sms_sign_name", "value": "", "type": "text", "group": "sms", "description": "签名名称"},
    {"key": "sms_template_code", "value": "", "type": "text", "group": "sms", "description": "模版CODE"},
    
    # 邮箱设置
    {"key": "smtp_host", "value": "", "type": "text", "group": "email", "description": "SMTP服务器"},
    {"key": "smtp_encryption", "value": "ssl", "type": "select", "group": "email", "description": "通信加密协议"},
    {"key": "smtp_port", "value": "465", "type": "number", "group": "email", "description": "端口"},
    {"key": "smtp_username", "value": "", "type": "text", "group": "email", "description": "用户名"},
    {"key": "smtp_password", "value": "", "type": "password", "group": "email", "description": "授权码"},
    
    # 其他设置
    {"key": "payment_callback_domain", "value": "", "type": "text", "group": "other", "description": "支付回调域名（留空自动检测）"},
    {"key": "site_domain", "value": "", "type": "text", "group": "other", "description": "主站域名（仅展示用，实际域名自动检测）"},
    {"key": "dns_cname", "value": "", "type": "text", "group": "other", "description": "DNS-CNAME"},
    {"key": "show_supplier_goods", "value": "1", "type": "boolean", "group": "other", "description": "主站显示其他商家商品"},
    {"key": "recharge_min", "value": "1", "type": "number", "group": "other", "description": "单次最低充值金额"},
    {"key": "recharge_max", "value": "1000", "type": "number", "group": "other", "description": "单次最高充值金额"},
    {"key": "recharge_bonus_enabled", "value": "0", "type": "boolean", "group": "other", "description": "充值赠送"},
    {"key": "recharge_bonus_config", "value": "100-10\n200-25\n500-80", "type": "textarea", "group": "other", "description": "充值赠送配置"},
    {"key": "customer_qq", "value": "", "type": "text", "group": "other", "description": "客服QQ"},
    {"key": "customer_url", "value": "", "type": "text", "group": "other", "description": "网页客服地址"},
    {"key": "withdraw_methods", "value": "alipay,wechat", "type": "text", "group": "other", "description": "提现方式"},
    {"key": "withdraw_fee", "value": "5", "type": "number", "group": "other", "description": "提现手续费"},
    {"key": "withdraw_min", "value": "100", "type": "number", "group": "other", "description": "最低提现金额"},
    {"key": "category_expand", "value": "0", "type": "boolean", "group": "other", "description": "默认展开分类"},
    {"key": "recommend_enabled", "value": "0", "type": "boolean", "group": "other", "description": "首页商品推荐"},
    {"key": "recommend_category_name", "value": "推荐", "type": "text", "group": "other", "description": "推荐分类名称"},
]


# ============== Schemas ==============

class UpdateConfigRequest(BaseModel):
    """更新配置请求"""
    configs: Dict[str, Any]


class PaymentConfigRequest(BaseModel):
    """支付配置请求"""
    name: str
    icon: Optional[str] = None
    handler: str
    code: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    cost: float = 0
    cost_type: int = 0
    commodity: int = 1
    recharge: int = 1
    equipment: int = 0
    sort: int = 0
    status: int = 1


# ============== APIs ==============

@router.get("", summary="获取系统配置")
async def get_settings(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取所有系统配置"""
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    
    # 按组分类
    grouped = {}
    for c in configs:
        if c.group not in grouped:
            grouped[c.group] = []
        grouped[c.group].append({
            "key": c.key,
            "value": c.value,
            "type": c.type,
            "description": c.description,
        })
    
    return grouped


@router.get("/flat", summary="获取扁平化配置")
async def get_settings_flat(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取扁平化的系统配置（key-value形式）"""
    result = await db.execute(select(SystemConfig))
    configs = result.scalars().all()
    
    return {c.key: c.value for c in configs}


@router.post("/init", summary="初始化默认配置")
async def init_default_settings(
    admin: CurrentAdmin,
    db: DbSession,
):
    """初始化默认配置项（仅创建不存在的配置）"""
    created_count = 0
    
    for cfg in DEFAULT_CONFIGS:
        # 检查是否已存在
        result = await db.execute(
            select(SystemConfig).where(SystemConfig.key == cfg["key"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            config = SystemConfig(
                key=cfg["key"],
                value=cfg["value"],
                type=cfg["type"],
                group=cfg["group"],
                description=cfg["description"],
            )
            db.add(config)
            created_count += 1
    
    if created_count > 0:
        await db.flush()
    
    return {"message": f"初始化完成，新增 {created_count} 项配置"}


@router.put("", summary="更新系统配置")
async def update_settings(
    request: UpdateConfigRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """批量更新系统配置"""
    for key, value in request.configs.items():
        await SystemConfig.set_value(db, key, str(value))
    
    return {"message": "保存成功"}


# ============== 支付配置 ==============

@router.get("/payments", summary="获取支付配置列表")
async def get_payment_settings(
    admin: CurrentAdmin,
    db: DbSession,
):
    """获取所有支付配置"""
    result = await db.execute(
        select(PaymentMethod).order_by(PaymentMethod.sort.asc())
    )
    payments = result.scalars().all()
    
    import json
    return {
        "items": [
            {
                "id": p.id,
                "name": p.name,
                "icon": p.icon,
                "handler": p.handler,
                "code": p.code,
                "config": json.loads(p.config) if p.config else {},
                "cost": float(p.cost),
                "cost_type": p.cost_type,
                "commodity": p.commodity,
                "recharge": p.recharge,
                "equipment": p.equipment,
                "sort": p.sort,
                "status": p.status,
            }
            for p in payments
        ]
    }


@router.post("/payments", summary="创建支付配置")
async def create_payment_setting(
    request: PaymentConfigRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """创建支付配置"""
    import json
    
    payment = PaymentMethod(
        name=request.name,
        icon=request.icon,
        handler=request.handler,
        code=request.code,
        config=json.dumps(request.config) if request.config else None,
        cost=request.cost,
        cost_type=request.cost_type,
        commodity=request.commodity,
        recharge=request.recharge,
        equipment=request.equipment,
        sort=request.sort,
        status=request.status,
    )
    db.add(payment)
    await db.flush()
    
    return {"id": payment.id, "message": "创建成功"}


@router.put("/payments/{payment_id}", summary="更新支付配置")
async def update_payment_setting(
    payment_id: int,
    request: PaymentConfigRequest,
    admin: CurrentAdmin,
    db: DbSession,
):
    """更新支付配置"""
    import json
    
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise NotFoundError("支付配置不存在")
    
    payment.name = request.name
    payment.icon = request.icon
    payment.handler = request.handler
    payment.code = request.code
    payment.config = json.dumps(request.config) if request.config else None
    payment.cost = request.cost
    payment.cost_type = request.cost_type
    payment.commodity = request.commodity
    payment.recharge = request.recharge
    payment.equipment = request.equipment
    payment.sort = request.sort
    payment.status = request.status
    
    return {"message": "更新成功"}


@router.delete("/payments/{payment_id}", summary="删除支付配置")
async def delete_payment_setting(
    payment_id: int,
    admin: CurrentAdmin,
    db: DbSession,
):
    """删除支付配置"""
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.id == payment_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise NotFoundError("支付配置不存在")
    
    await db.delete(payment)
    return {"message": "删除成功"}


# ============== 域名检测 ==============

@router.get("/detect-domain", summary="检测当前域名")
async def detect_domain(
    request: Request,
    admin: CurrentAdmin,
):
    """
    实时检测当前访问的域名和协议。
    从请求头自动获取，无需手动配置。
    """
    from ....utils.request import get_base_url, get_callback_base_url
    
    base_url = get_base_url(request)
    callback_url = get_callback_base_url(request)
    
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    
    return {
        "detected_domain": host,
        "detected_scheme": scheme,
        "base_url": base_url,
        "callback_url": callback_url,
    }
