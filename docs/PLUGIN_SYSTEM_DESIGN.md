# LecFaka 插件系统设计方案

> 版本：v1.0  
> 日期：2026-02-07  
> 状态：规划中

---

## 一、概述

### 1.1 目标

将 LecFaka 从"一个发卡系统"升级为"一个可扩展的发卡平台"，通过 Open Core（核心开源）+ 付费插件生态 实现商业化。

### 1.2 商业模型

```
开源核心（引流）
├── 基础发卡功能
├── 基础支付（余额、易支付）
├── 基础管理后台
└── 插件开发 SDK

付费层（盈利）
├── 官方插件（支付宝/微信直连、高级模板、SMTP通知...）
├── 第三方插件（开发者生态，平台抽成 20-30%）
└── 企业授权（一次性解锁全部官方插件 + 技术支持）
```

### 1.3 技术约束

| 约束 | 说明 |
|------|------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy Async |
| 前端 | React 18 / TypeScript / Ant Design / Tailwind CSS |
| 部署 | Docker 优先，支持宝塔面板 |
| 兼容性 | 插件系统不能破坏现有功能，必须向下兼容 |

---

## 二、插件类型定义

### 2.1 五种插件类型

| 类型标识 | 名称 | 说明 | 后端 | 前端 |
|---------|------|------|------|------|
| `payment` | 支付插件 | 对接第三方支付接口 | 继承 `PaymentBase` | 无 |
| `theme` | 主题模板 | 改变前端视觉风格 | 提供配置 API | CSS + 组件覆盖 |
| `notify` | 通知插件 | 邮件/Telegram/企业微信通知 | 继承 `NotifyBase` | 设置页扩展 |
| `delivery` | 发货插件 | 自定义发货逻辑（API发货等） | 继承 `DeliveryBase` | 无 |
| `extension` | 通用扩展 | 防刷、统计、SEO 等 | Hook 注入 | 可选前端组件 |

### 2.2 现有代码的映射

当前 `backend/app/payments/` 目录已有的代码就是 `payment` 类型插件的雏形：

```
现有结构                          → 目标结构
payments/base.py (PaymentBase)   → plugins/sdk/payment_base.py
payments/epay.py                 → plugins/builtin/payment_epay/
payments/balance.py              → 内置于核心（不作为插件）
payments/usdt.py                 → plugins/builtin/payment_usdt/
```

---

## 三、插件标准规范

### 3.1 目录结构

每个插件是 `plugins/` 下的一个独立目录：

```
backend/app/plugins/
├── __init__.py              # 插件管理器入口
├── sdk/                     # 插件开发 SDK（开源）
│   ├── __init__.py
│   ├── base.py              # PluginBase 基类
│   ├── payment_base.py      # 支付插件基类（从现有 PaymentBase 迁移）
│   ├── notify_base.py       # 通知插件基类
│   ├── delivery_base.py     # 发货插件基类
│   └── hooks.py             # 钩子系统
│
├── builtin/                 # 内置插件（随主程序分发，免费）
│   ├── payment_epay/
│   │   ├── plugin.json
│   │   ├── __init__.py
│   │   └── handler.py
│   └── payment_usdt/
│       ├── plugin.json
│       ├── __init__.py
│       └── handler.py
│
└── installed/               # 用户安装的插件（付费/第三方）
    ├── .gitignore           # 此目录不入版本库
    └── payment_alipay/
        ├── plugin.json
        ├── __init__.py
        └── handler.py
```

### 3.2 插件描述文件 `plugin.json`

这是每个插件必须包含的元数据文件：

```json
{
  "id": "payment_alipay_direct",
  "name": "支付宝当面付",
  "version": "1.2.0",
  "type": "payment",
  "author": {
    "name": "LecFaka Official",
    "url": "https://lecfaka.com"
  },
  "description": "支付宝官方当面付接口，支持扫码支付、手机网站支付",
  "icon": "https://store.lecfaka.com/icons/alipay.png",
  "min_app_version": "1.0.0",
  "max_app_version": null,
  "license_required": true,
  "price": 68.88,
  
  "backend": {
    "entry": "handler:AlipayDirectPayment",
    "hooks": ["order.paid", "app.startup"],
    "routes": false,
    "models": false,
    "migrations": []
  },
  
  "frontend": {
    "entry": null,
    "settings_component": "settings.js",
    "assets": ["style.css"]
  },
  
  "config_schema": {
    "app_id": {
      "type": "string",
      "label": "应用 App ID",
      "required": true,
      "placeholder": "2021000000000000"
    },
    "private_key": {
      "type": "textarea",
      "label": "应用私钥",
      "required": true,
      "encrypted": true
    },
    "alipay_public_key": {
      "type": "textarea",
      "label": "支付宝公钥",
      "required": true
    },
    "sandbox": {
      "type": "boolean",
      "label": "沙箱模式",
      "default": false
    }
  },
  
  "dependencies": [],
  "changelog": {
    "1.2.0": "新增手机网站支付通道",
    "1.1.0": "修复签名验证问题",
    "1.0.0": "初始版本"
  }
}
```

### 3.3 插件基类

```python
# plugins/sdk/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class PluginMeta:
    """插件元数据（从 plugin.json 解析）"""
    id: str
    name: str
    version: str
    type: str  # payment | theme | notify | delivery | extension
    author: Dict[str, str]
    description: str = ""
    license_required: bool = False
    config_schema: Dict[str, Any] = field(default_factory=dict)


class PluginBase(ABC):
    """
    所有插件的基类。
    
    生命周期：
    1. __init__(meta, config) - 实例化，注入元数据和用户配置
    2. on_install()          - 首次安装时调用（创建表、初始化数据）
    3. on_enable()           - 每次启用时调用
    4. on_disable()          - 禁用时调用
    5. on_uninstall()        - 卸载时调用（清理数据）
    """
    
    def __init__(self, meta: PluginMeta, config: Dict[str, Any]):
        self.meta = meta
        self.config = config
        self._enabled = False
    
    @property
    def id(self) -> str:
        return self.meta.id
    
    @property
    def name(self) -> str:
        return self.meta.name
    
    async def on_install(self) -> None:
        """插件安装时调用"""
        pass
    
    async def on_enable(self) -> None:
        """插件启用时调用"""
        self._enabled = True
    
    async def on_disable(self) -> None:
        """插件禁用时调用"""
        self._enabled = False
    
    async def on_uninstall(self) -> None:
        """插件卸载时调用"""
        pass
    
    def validate_config(self) -> List[str]:
        """
        验证配置。返回错误消息列表，空列表表示通过。
        """
        errors = []
        for key, schema in self.meta.config_schema.items():
            if schema.get("required") and not self.config.get(key):
                errors.append(f"缺少必填配置: {schema.get('label', key)}")
        return errors
```

---

## 四、钩子系统设计

### 4.1 事件定义

```python
# plugins/sdk/hooks.py

from typing import Callable, Any, Dict, List
from dataclasses import dataclass, field
import asyncio


# ============ 预定义事件 ============

class Events:
    """所有可用的钩子事件"""
    
    # --- 应用生命周期 ---
    APP_STARTUP      = "app.startup"        # 应用启动完成
    APP_SHUTDOWN      = "app.shutdown"       # 应用关闭前
    
    # --- 订单流程（核心） ---
    ORDER_CREATING    = "order.creating"     # 订单创建前（可修改/拦截）
    ORDER_CREATED     = "order.created"      # 订单创建后
    ORDER_PAID        = "order.paid"         # 支付成功
    ORDER_DELIVERED   = "order.delivered"    # 发货完成
    ORDER_CANCELLED   = "order.cancelled"   # 订单取消
    
    # --- 支付 ---
    PAYMENT_CREATING  = "payment.creating"   # 发起支付前
    PAYMENT_CALLBACK  = "payment.callback"   # 收到支付回调
    
    # --- 用户 ---
    USER_REGISTERED   = "user.registered"    # 用户注册
    USER_LOGIN        = "user.login"         # 用户登录
    USER_RECHARGED    = "user.recharged"     # 用户充值
    
    # --- 商品/卡密 ---
    CARD_IMPORTED     = "card.imported"      # 卡密导入
    COMMODITY_CREATED = "commodity.created"  # 商品创建
    
    # --- 通知（插件可监听并发送通知） ---
    NOTIFY_SEND       = "notify.send"        # 触发发送通知


# ============ 事件上下文 ============

@dataclass
class EventContext:
    """传递给钩子处理函数的上下文"""
    event: str
    data: Dict[str, Any] = field(default_factory=dict)
    cancelled: bool = False  # 如果为 True，业务流程会中断（仅 .creating 事件支持）
    cancel_reason: str = ""
    
    def cancel(self, reason: str = ""):
        """取消当前操作（仅 creating 类事件有效）"""
        self.cancelled = True
        self.cancel_reason = reason


# ============ 钩子管理器 ============

class HookManager:
    """
    全局钩子管理器（单例）。
    
    使用方式：
    
    # 注册钩子（插件中）
    hooks.on(Events.ORDER_PAID, my_handler)
    
    # 触发钩子（核心代码中）
    ctx = await hooks.emit(Events.ORDER_PAID, {"order": order})
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event: str, handler: Callable, priority: int = 10):
        """
        注册事件处理函数。
        
        Args:
            event: 事件名称
            handler: 异步处理函数，签名为 async def handler(ctx: EventContext)
            priority: 优先级，数字越小越先执行（默认 10）
        """
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append((priority, handler))
        self._handlers[event].sort(key=lambda x: x[0])
    
    def off(self, event: str, handler: Callable):
        """移除事件处理函数"""
        if event in self._handlers:
            self._handlers[event] = [
                (p, h) for p, h in self._handlers[event] if h != handler
            ]
    
    async def emit(self, event: str, data: Dict[str, Any] = None) -> EventContext:
        """
        触发事件。
        
        Args:
            event: 事件名称
            data: 事件数据
            
        Returns:
            EventContext（检查 .cancelled 判断是否被拦截）
        """
        ctx = EventContext(event=event, data=data or {})
        
        handlers = self._handlers.get(event, [])
        for priority, handler in handlers:
            try:
                await handler(ctx)
            except Exception as e:
                # 记录错误但不中断其他插件
                print(f"[Plugin Error] {event}: {e}")
            
            # creating 类事件被取消时停止后续处理
            if ctx.cancelled:
                break
        
        return ctx
    
    def clear(self):
        """清除所有钩子（测试用）"""
        self._handlers.clear()


# 全局实例
hooks = HookManager()
```

### 4.2 在核心代码中埋入钩子点

以 `OrderService.create_order` 为例，展示改造方式：

```python
# services/order.py 中的改造（伪代码，展示插入位置）

from ..plugins.sdk.hooks import hooks, Events

class OrderService:
    async def create_order(self, ...):
        # ... 前置验证 ...
        
        # ===== 钩子：订单创建前 =====
        ctx = await hooks.emit(Events.ORDER_CREATING, {
            "commodity": commodity,
            "quantity": quantity,
            "user": user,
            "amount": price_info["amount"],
        })
        if ctx.cancelled:
            raise ValidationError(ctx.cancel_reason or "订单创建被拦截")
        # ===========================
        
        # ... 创建订单 ...
        
        # ===== 钩子：订单创建后 =====
        await hooks.emit(Events.ORDER_CREATED, {
            "order": order,
            "commodity": commodity,
        })
        # ===========================
        
        # ... 处理支付 ...
        
        if order.status == 1:
            # ===== 钩子：支付成功 =====
            await hooks.emit(Events.ORDER_PAID, {
                "order": order,
                "user": user,
            })
            # ===========================
        
        return result
```

---

## 五、插件管理器

### 5.1 核心职责

```python
# plugins/__init__.py

class PluginManager:
    """
    插件管理器。
    
    职责：
    1. 扫描并加载插件（builtin/ 和 installed/）
    2. 验证插件元数据和授权
    3. 管理插件生命周期（安装/启用/禁用/卸载）
    4. 将插件注册到对应的子系统（支付注册表、钩子系统等）
    5. 提供插件查询 API
    """
    
    plugins: Dict[str, PluginInstance]   # 所有已加载的插件
    enabled: Set[str]                     # 已启用的插件 ID
    
    async def scan_and_load(self):
        """
        扫描 builtin/ 和 installed/ 目录，加载所有插件。
        在 app.startup 时调用。
        """
    
    async def install_plugin(self, plugin_zip: bytes, license_key: str = None):
        """
        安装插件。
        1. 解压到 installed/ 目录
        2. 验证 plugin.json
        3. 验证授权（如果 license_required）
        4. 调用 on_install()
        5. 记录到数据库
        """
    
    async def enable_plugin(self, plugin_id: str):
        """
        启用插件。
        1. 调用 on_enable()
        2. 注册钩子
        3. 注册到对应子系统（支付/通知/发货注册表）
        """
    
    async def disable_plugin(self, plugin_id: str):
        """
        禁用插件。
        1. 移除钩子
        2. 从子系统注销
        3. 调用 on_disable()
        """
    
    async def uninstall_plugin(self, plugin_id: str):
        """
        卸载插件。
        1. disable
        2. 调用 on_uninstall()
        3. 删除文件
        4. 清理数据库记录
        """
    
    def get_plugin(self, plugin_id: str) -> Optional[PluginInstance]:
        """获取插件实例"""
    
    def get_plugins_by_type(self, plugin_type: str) -> List[PluginInstance]:
        """按类型获取插件列表"""
```

### 5.2 数据库表设计

```sql
-- 插件安装记录
CREATE TABLE plugins (
    id            SERIAL PRIMARY KEY,
    plugin_id     VARCHAR(100) UNIQUE NOT NULL,  -- 插件唯一标识
    name          VARCHAR(200) NOT NULL,
    version       VARCHAR(20) NOT NULL,
    type          VARCHAR(20) NOT NULL,           -- payment/theme/notify/delivery/extension
    author        VARCHAR(100),
    description   TEXT,
    icon          VARCHAR(500),
    
    -- 状态
    status        SMALLINT DEFAULT 0,             -- 0=禁用 1=启用
    is_builtin    BOOLEAN DEFAULT FALSE,          -- 是否内置插件
    
    -- 授权
    license_key   VARCHAR(200),                   -- 授权码
    license_status SMALLINT DEFAULT 0,            -- 0=未授权 1=已授权 2=已过期
    license_domain VARCHAR(200),                  -- 绑定域名
    license_expires_at TIMESTAMP,                 -- 授权过期时间
    last_verify_at TIMESTAMP,                     -- 上次验证时间
    
    -- 配置（JSON）
    config        TEXT,                            -- 插件配置
    
    -- 时间
    installed_at  TIMESTAMP DEFAULT NOW(),
    updated_at    TIMESTAMP DEFAULT NOW(),
    
    -- 索引
    INDEX idx_plugins_type (type),
    INDEX idx_plugins_status (status)
);
```

### 5.3 加载流程

```
App 启动 (main.py lifespan)
    │
    ├── init_db()
    │
    ├── PluginManager.scan_and_load()
    │   ├── 扫描 builtin/ 目录 → 加载内置插件
    │   ├── 扫描 installed/ 目录 → 加载已安装插件
    │   ├── 读取数据库 plugins 表 → 获取启用状态和配置
    │   ├── 验证授权（静默，失败不阻塞启动，仅标记状态）
    │   └── 对已启用的插件调用 enable_plugin()
    │       ├── 注册钩子
    │       ├── payment 类型 → 注册到 PAYMENT_HANDLERS
    │       ├── notify 类型  → 注册到 NOTIFY_HANDLERS
    │       └── delivery 类型 → 注册到 DELIVERY_HANDLERS
    │
    ├── hooks.emit(Events.APP_STARTUP)
    │
    └── 就绪，开始接收请求
```

---

## 六、授权系统

### 6.1 架构

```
┌────────────────────────────────────────────┐
│           授权服务器 (store.lecfaka.com)      │
│           独立的 FastAPI 项目                 │
│                                              │
│  /api/v1/license/verify                      │
│  /api/v1/store/plugins                       │
│  /api/v1/store/download/{plugin_id}          │
│  /api/v1/store/purchase                      │
└────────────────────┬───────────────────────┘
                     │
        HTTPS + HMAC 签名验证
                     │
┌────────────────────┴───────────────────────┐
│          用户的 LecFaka 实例                  │
│                                              │
│  PluginManager                               │
│  ├── install_plugin() → 下载 + 验证授权       │
│  ├── 定时任务(24h) → 静默验证授权             │
│  └── license_client.py → 与授权服务器通信      │
└──────────────────────────────────────────────┘
```

### 6.2 授权验证流程

```
1. 用户在插件商店购买插件 → 获得 license_key
2. 在 LecFaka 后台「插件管理」中输入 license_key
3. 后端发起验证请求：

   POST https://store.lecfaka.com/api/v1/license/verify
   {
     "plugin_id": "payment_alipay",
     "license_key": "LF-XXXX-XXXX-XXXX",
     "domain": "shop.example.com",
     "app_version": "1.2.0",
     "timestamp": 1707321600,
     "sign": "hmac_sha256(secret, payload)"
   }

4. 授权服务器验证：
   - license_key 是否存在且有效
   - domain 是否匹配（首次绑定/已绑定）
   - 是否在有效期内
   
5. 响应：
   {
     "valid": true,
     "expires_at": "2027-02-07T00:00:00Z",
     "features": ["alipay_f2f", "alipay_wap"],
     "message": "授权有效"
   }

6. 本地缓存验证结果，24小时后再次验证
```

### 6.3 防盗版策略（分层）

| 层级 | 策略 | 说明 |
|------|------|------|
| L1 | 域名绑定 | license_key 绑定域名，换域名需重新授权 |
| L2 | 定期验证 | 每24小时静默联网验证一次 |
| L3 | 代码编译 | 付费插件核心逻辑用 Cython 编译为 `.so`/`.pyd`，不暴露源码 |
| L4 | 服务端关键逻辑 | 最核心的功能（如签名算法）放在授权服务器，通过 API 调用 |
| L5 | 混淆 + 完整性校验 | 文件 hash 校验，防止篡改绕过授权检查 |

---

## 七、前端插件系统

### 7.1 主题系统（配置化方案）

主题插件不需要加载远程 JS，而是通过 CSS 变量 + 配置驱动：

```json
{
  "id": "theme_anime",
  "type": "theme",
  "config_schema": {
    "primary_color": {"type": "color", "label": "主色调", "default": "#ec4899"},
    "bg_mode": {"type": "select", "label": "背景模式", "options": ["gradient", "image", "solid"]},
    "card_style": {"type": "select", "label": "卡片风格", "options": ["rounded", "glass", "flat"]},
    "particle_enabled": {"type": "boolean", "label": "粒子特效", "default": true}
  }
}
```

前端读取主题配置：

```typescript
// hooks/useTheme.ts
const useTheme = () => {
  const [themeConfig, setThemeConfig] = useState(null)
  
  useEffect(() => {
    api.get('/plugins/active-theme').then(setThemeConfig)
  }, [])
  
  useEffect(() => {
    if (themeConfig) {
      // 注入 CSS 变量
      document.documentElement.style.setProperty('--primary-color', themeConfig.primary_color)
      // 加载主题 CSS
      if (themeConfig.css_url) {
        loadCSS(themeConfig.css_url)
      }
    }
  }, [themeConfig])
}
```

### 7.2 功能插件（动态组件）

对于需要在后台注入自定义 UI 的插件（如统计面板、设置页）：

```typescript
// plugins/plugin-loader.ts

interface FrontendPlugin {
  id: string
  // 在哪个位置注入
  slot: 'admin_dashboard_widget' | 'admin_settings_tab' | 'shop_product_extra' | 'order_success_extra'
  // 编译后的 JS 文件 URL
  componentUrl: string
}

// 在后台页面中预留插槽
function AdminDashboard() {
  const pluginWidgets = usePluginSlot('admin_dashboard_widget')
  
  return (
    <div>
      {/* 原有内容 */}
      <Row>
        <Col>...</Col>
      </Row>
      
      {/* 插件注入区 */}
      {pluginWidgets.map(widget => (
        <Suspense key={widget.id} fallback={<Spin />}>
          <RemoteComponent url={widget.componentUrl} />
        </Suspense>
      ))}
    </div>
  )
}
```

### 7.3 前端插槽（Slot）位置

| 插槽 ID | 位置 | 用途 |
|---------|------|------|
| `admin_dashboard_widget` | 管理后台仪表盘 | 统计插件添加图表 |
| `admin_settings_tab` | 管理后台设置页 | 插件配置页面 |
| `admin_nav_extra` | 管理后台侧边栏 | 插件添加菜单项 |
| `shop_product_extra` | 商品详情页 | 自定义购买组件 |
| `order_success_extra` | 下单成功页 | 额外操作按钮 |
| `user_dashboard_widget` | 用户中心首页 | 用户统计组件 |

---

## 八、插件商店 API

### 8.1 授权服务器 API

```
GET  /api/v1/store/plugins                    # 插件列表（分类、搜索）
GET  /api/v1/store/plugins/{id}               # 插件详情
POST /api/v1/store/purchase                    # 购买插件
GET  /api/v1/store/download/{id}              # 下载插件（需授权）
POST /api/v1/license/verify                    # 验证授权
POST /api/v1/license/bind                      # 绑定域名
GET  /api/v1/license/my                        # 我的授权列表
```

### 8.2 LecFaka 本地 API

```
GET    /api/v1/admin/plugins                   # 已安装插件列表
POST   /api/v1/admin/plugins/install           # 安装插件（上传 zip）
POST   /api/v1/admin/plugins/{id}/enable       # 启用
POST   /api/v1/admin/plugins/{id}/disable      # 禁用
DELETE /api/v1/admin/plugins/{id}              # 卸载
PUT    /api/v1/admin/plugins/{id}/config       # 更新配置
POST   /api/v1/admin/plugins/{id}/license      # 输入授权码
GET    /api/v1/admin/plugins/store             # 代理插件商店列表
POST   /api/v1/admin/plugins/store/install     # 从商店安装
```

---

## 九、实施计划

### Phase 1：插件基础框架（预计 1-2 周）

**目标**：搭建可运行的插件加载系统，将现有支付处理器迁移为插件。

| 任务 | 优先级 | 预计工时 |
|------|--------|---------|
| 创建 `plugins/sdk/` 目录，实现 `PluginBase`、`HookManager` | P0 | 4h |
| 创建 `plugins/__init__.py` 实现 `PluginManager` | P0 | 6h |
| 创建 `plugins` 数据库表 + Model | P0 | 2h |
| 迁移 `payments/epay.py` → `plugins/builtin/payment_epay/` | P0 | 3h |
| 迁移 `payments/usdt.py` → `plugins/builtin/payment_usdt/` | P0 | 2h |
| 在 `main.py` 的 `lifespan` 中集成插件加载 | P0 | 2h |
| 在 `OrderService` 中埋入钩子点 | P1 | 4h |
| 后台「插件管理」页面（列表、启用/禁用） | P1 | 6h |
| 编写第一个 extension 示例插件（如 order_notify） | P1 | 3h |

### Phase 2：授权与商店（预计 2-3 周）

**目标**：独立部署授权服务器，实现插件购买和验证闭环。

| 任务 | 优先级 | 预计工时 |
|------|--------|---------|
| 搭建授权服务器项目（独立 FastAPI） | P0 | 8h |
| 授权服务器 - 插件管理后台 | P0 | 6h |
| 授权服务器 - 授权码生成/管理/验证 API | P0 | 6h |
| LecFaka 本地 - `license_client.py` 授权验证客户端 | P0 | 4h |
| LecFaka 本地 - 定时授权验证任务（24h） | P1 | 2h |
| 前端「插件商店」页面（浏览/搜索/安装） | P1 | 8h |
| 前端「插件配置」页面（根据 config_schema 自动生成表单） | P1 | 6h |
| 插件上传/下载打包机制 | P1 | 4h |

### Phase 3：生态建设（持续）

| 任务 | 说明 |
|------|------|
| 开发 3-5 个官方付费插件 | 支付宝直连、微信直连、Telegram通知、高级模板 |
| 编写插件开发文档 | SDK 使用指南、示例代码、发布流程 |
| Cython 编译工具链 | 付费插件自动编译流水线 |
| 第三方开发者注册/发布系统 | 开发者后台、审核流程、分成结算 |
| 主题系统 | CSS 变量体系、主题配置 API |

### Phase 4：商业化完善

| 任务 | 说明 |
|------|------|
| 企业版授权 | 一次性解锁全部官方插件 |
| 开发者分成 | 第三方插件销售分成（70/30 或 80/20） |
| 插件评分/评论 | 用户反馈系统 |
| 自动更新 | 插件版本检测 + 一键升级 |
| 数据统计 | 插件安装量、活跃度、收入仪表盘 |

---

## 十、关键设计决策

### 10.1 为什么不用 Python 热重载？

PHP 可以随改随生效，但 Python 进程需要重启才能加载新模块。我们的方案：

- **安装/卸载插件后**：提示用户"需要重启服务以生效"
- **Docker 部署**：自动 `docker restart lecfaka-backend`
- **配置变更**：配置存数据库，修改配置不需要重启

### 10.2 余额支付为什么不作为插件？

`#balance` 是核心功能，与用户余额系统深度耦合。将其内置于核心代码中，避免被禁用导致系统不可用。

### 10.3 前端主题为什么用配置化而非模板？

React 是编译型框架，不像 PHP 模板引擎可以直接替换文件。配置化 + CSS 变量是最稳定的方案：
- 不需要重新编译前端
- 不会因为主题代码错误导致整站崩溃
- 升级主程序时不会覆盖主题修改

### 10.4 插件间如何通信？

通过 Hook 系统：
- 插件 A 在某个事件上 `emit`
- 插件 B 在同一事件上 `on` 监听
- 通过 `EventContext.data` 传递数据

---

## 十一、安全考量

| 风险 | 对策 |
|------|------|
| 恶意插件执行危险代码 | 官方商店审核机制；Docker 隔离 |
| 授权绕过 | 多层防盗版；核心逻辑服务端执行 |
| 插件导致主程序崩溃 | try/except 包裹所有插件调用；超时控制 |
| 插件间冲突 | 插件隔离命名空间；依赖声明 |
| 用户上传恶意 zip | 文件类型白名单；沙箱解压；签名验证 |
| SQL 注入 | 插件不直接操作 SQL，通过 ORM 和预定义 Service |

---

## 附录 A：支付插件示例

```python
# plugins/builtin/payment_epay/handler.py

from plugins.sdk.payment_base import PaymentBase, PaymentResult, CallbackResult
from typing import Dict, Any


class EpayPaymentPlugin(PaymentBase):
    """易支付插件"""
    
    name = "易支付"
    channels = {"alipay": "支付宝", "wxpay": "微信支付"}
    
    async def create_payment(self, trade_no, amount, callback_url, return_url, **kwargs):
        # ... 现有 epay.py 的逻辑 ...
        pass
    
    async def verify_callback(self, data):
        # ... 现有逻辑 ...
        pass
    
    def get_callback_response(self, success):
        return "success" if success else "fail"
```

```json
// plugins/builtin/payment_epay/plugin.json
{
  "id": "payment_epay",
  "name": "易支付",
  "version": "1.0.0",
  "type": "payment",
  "author": {"name": "LecFaka"},
  "description": "支持所有易支付兼容接口",
  "license_required": false,
  "backend": {
    "entry": "handler:EpayPaymentPlugin"
  },
  "config_schema": {
    "url": {"type": "string", "label": "接口地址", "required": true},
    "pid": {"type": "string", "label": "商户ID", "required": true},
    "key": {"type": "string", "label": "商户密钥", "required": true, "encrypted": true},
    "use_mapi": {"type": "boolean", "label": "使用MAPI接口", "default": false}
  }
}
```

## 附录 B：通知插件示例

```python
# plugins/installed/notify_telegram/handler.py

from plugins.sdk.base import PluginBase
from plugins.sdk.hooks import hooks, Events, EventContext
import httpx


class TelegramNotifyPlugin(PluginBase):
    """Telegram 通知插件"""
    
    async def on_enable(self):
        await super().on_enable()
        # 注册钩子 - 监听订单支付成功事件
        hooks.on(Events.ORDER_PAID, self.on_order_paid)
        hooks.on(Events.USER_REGISTERED, self.on_user_registered)
    
    async def on_disable(self):
        hooks.off(Events.ORDER_PAID, self.on_order_paid)
        hooks.off(Events.USER_REGISTERED, self.on_user_registered)
        await super().on_disable()
    
    async def on_order_paid(self, ctx: EventContext):
        """订单支付成功时发送 Telegram 通知"""
        order = ctx.data.get("order")
        if not order:
            return
        
        text = (
            f"💰 新订单支付成功\n"
            f"订单号: {order.trade_no}\n"
            f"金额: ¥{order.amount}\n"
            f"数量: {order.quantity}"
        )
        await self._send_message(text)
    
    async def on_user_registered(self, ctx: EventContext):
        """新用户注册时通知"""
        user = ctx.data.get("user")
        if user:
            await self._send_message(f"👤 新用户注册: {user.username}")
    
    async def _send_message(self, text: str):
        """发送 Telegram 消息"""
        bot_token = self.config.get("bot_token")
        chat_id = self.config.get("chat_id")
        if not bot_token or not chat_id:
            return
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        async with httpx.AsyncClient() as client:
            await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            })
```

```json
// plugins/installed/notify_telegram/plugin.json
{
  "id": "notify_telegram",
  "name": "Telegram 机器人通知",
  "version": "1.0.0",
  "type": "notify",
  "author": {"name": "LecFaka Official"},
  "description": "通过 Telegram Bot 接收订单通知、用户注册通知等",
  "license_required": true,
  "price": 29.88,
  "backend": {
    "entry": "handler:TelegramNotifyPlugin",
    "hooks": ["order.paid", "user.registered"]
  },
  "config_schema": {
    "bot_token": {
      "type": "string",
      "label": "Bot Token",
      "required": true,
      "placeholder": "123456:ABC-DEF1234..."
    },
    "chat_id": {
      "type": "string",
      "label": "Chat ID",
      "required": true,
      "placeholder": "-1001234567890"
    }
  }
}
```
