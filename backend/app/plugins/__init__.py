"""
插件管理器
负责扫描、加载、管理所有插件的生命周期
"""

import json
import importlib
import logging
import os
from pathlib import Path
from typing import Dict, Optional, List, Type

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .sdk.base import PluginBase, PluginMeta
from .sdk.hooks import hooks
from .sdk.payment_base import PaymentPluginBase

logger = logging.getLogger("plugins.manager")

# 支付处理器注册表（兼容旧的 payments/ 模块接口）
PAYMENT_HANDLERS: Dict[str, Type[PaymentPluginBase]] = {}

# 通知处理器注册表
NOTIFY_HANDLERS: Dict[str, PluginBase] = {}

# 发货处理器注册表
DELIVERY_HANDLERS: Dict[str, PluginBase] = {}


class PluginInstance:
    """运行时的插件实例包装"""

    def __init__(
        self,
        meta: PluginMeta,
        plugin_class: Type[PluginBase],
        path: str,
        is_builtin: bool = False,
    ):
        self.meta = meta
        self.plugin_class = plugin_class
        self.path = path
        self.is_builtin = is_builtin
        self.instance: Optional[PluginBase] = None
        self.enabled = False
        self.config: Dict = {}
        self.license_status = 0  # 0=未授权 1=已授权

    def create_instance(self, config: Dict = None) -> PluginBase:
        """创建插件实例"""
        self.config = config or {}
        self.instance = self.plugin_class(self.meta, self.config)
        return self.instance


class PluginManager:
    """
    插件管理器（单例）。

    使用:
        pm = PluginManager()
        await pm.scan_and_load(db_session)
    """

    def __init__(self):
        self._plugins: Dict[str, PluginInstance] = {}
        self._base_dir = Path(__file__).parent

    @property
    def plugins(self) -> Dict[str, PluginInstance]:
        return self._plugins

    async def scan_and_load(self, db: AsyncSession):
        """
        扫描并加载所有插件。在应用启动时调用。

        1. 扫描 builtin/ 和 installed/ 目录
        2. 从数据库加载状态和配置
        3. 启用已标记为启用的插件
        """
        logger.info("Scanning plugins...")

        # 扫描内置插件
        builtin_dir = self._base_dir / "builtin"
        await self._scan_directory(builtin_dir, is_builtin=True)

        # 扫描已安装插件
        installed_dir = self._base_dir / "installed"
        await self._scan_directory(installed_dir, is_builtin=False)

        logger.info(f"Found {len(self._plugins)} plugin(s)")

        # 从数据库同步状态
        await self._sync_from_db(db)

        # 启用已标记为启用的插件
        enabled_count = 0
        for plugin_id, pi in self._plugins.items():
            if pi.enabled:
                try:
                    await self._enable_plugin_internal(pi)
                    enabled_count += 1
                except Exception as e:
                    logger.error(f"Failed to enable plugin {plugin_id}: {e}")

        logger.info(f"Enabled {enabled_count} plugin(s)")

    async def _scan_directory(self, directory: Path, is_builtin: bool):
        """扫描插件目录"""
        if not directory.exists():
            return

        for item in directory.iterdir():
            if not item.is_dir() or item.name.startswith("_"):
                continue

            plugin_json = item / "plugin.json"
            if not plugin_json.exists():
                logger.warning(f"Skipping {item.name}: no plugin.json")
                continue

            try:
                meta = self._load_meta(plugin_json)
                plugin_class = self._load_class(item, meta)

                pi = PluginInstance(
                    meta=meta,
                    plugin_class=plugin_class,
                    path=str(item),
                    is_builtin=is_builtin,
                )
                self._plugins[meta.id] = pi
                logger.info(f"  Loaded: {meta.id} v{meta.version} ({meta.type})")
            except Exception as e:
                logger.error(f"Failed to load plugin from {item.name}: {e}")

    def _load_meta(self, plugin_json: Path) -> PluginMeta:
        """从 plugin.json 加载元数据"""
        with open(plugin_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        return PluginMeta(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            type=data["type"],
            author=data.get("author", {}),
            description=data.get("description", ""),
            icon=data.get("icon"),
            min_app_version=data.get("min_app_version"),
            max_app_version=data.get("max_app_version"),
            license_required=data.get("license_required", False),
            price=data.get("price", 0),
            config_schema=data.get("config_schema", {}),
            backend=data.get("backend", {}),
            frontend=data.get("frontend", {}),
            dependencies=data.get("dependencies", []),
            changelog=data.get("changelog", {}),
        )

    def _load_class(self, plugin_dir: Path, meta: PluginMeta) -> Type[PluginBase]:
        """动态加载插件类"""
        entry = meta.backend.get("entry", "__init__:Plugin")
        module_name, class_name = entry.split(":")

        # 构建模块路径
        if plugin_dir.parent.name == "builtin":
            module_path = f"app.plugins.builtin.{plugin_dir.name}.{module_name}"
        else:
            module_path = f"app.plugins.installed.{plugin_dir.name}.{module_name}"

        module = importlib.import_module(module_path)
        plugin_class = getattr(module, class_name)

        if not issubclass(plugin_class, PluginBase):
            raise TypeError(
                f"{class_name} in {module_path} is not a subclass of PluginBase"
            )

        return plugin_class

    async def _sync_from_db(self, db: AsyncSession):
        """从数据库同步插件状态和配置"""
        from ..models.plugin import Plugin

        result = await db.execute(select(Plugin))
        db_plugins = {p.plugin_id: p for p in result.scalars().all()}

        for plugin_id, pi in self._plugins.items():
            if plugin_id in db_plugins:
                # 已有记录，同步状态
                db_plugin = db_plugins[plugin_id]
                pi.enabled = db_plugin.status == 1
                pi.license_status = db_plugin.license_status
                try:
                    pi.config = json.loads(db_plugin.config) if db_plugin.config else {}
                except (json.JSONDecodeError, TypeError):
                    pi.config = {}

                # 更新版本信息
                if db_plugin.version != pi.meta.version:
                    db_plugin.version = pi.meta.version
                    db_plugin.name = pi.meta.name
                    db_plugin.description = pi.meta.description
            else:
                # 新插件，创建数据库记录
                author_name = ""
                if isinstance(pi.meta.author, dict):
                    author_name = pi.meta.author.get("name", "")
                elif isinstance(pi.meta.author, str):
                    author_name = pi.meta.author

                new_plugin = Plugin(
                    plugin_id=plugin_id,
                    name=pi.meta.name,
                    version=pi.meta.version,
                    type=pi.meta.type,
                    author=author_name,
                    description=pi.meta.description,
                    icon=pi.meta.icon or "",
                    is_builtin=pi.is_builtin,
                    status=1 if pi.is_builtin else 0,  # 内置插件默认启用
                    config="{}",
                )
                db.add(new_plugin)
                pi.enabled = pi.is_builtin

        await db.commit()

    async def _enable_plugin_internal(self, pi: PluginInstance):
        """内部启用插件"""
        instance = pi.create_instance(pi.config)
        await instance.on_enable()
        pi.enabled = True

        # 按类型注册到对应子系统
        if pi.meta.type == "payment" and isinstance(instance, PaymentPluginBase):
            PAYMENT_HANDLERS[pi.meta.id] = pi.plugin_class
            logger.info(f"  Registered payment handler: {pi.meta.id}")

    async def enable_plugin(self, plugin_id: str, db: AsyncSession) -> bool:
        """启用插件（API 调用）"""
        pi = self._plugins.get(plugin_id)
        if not pi:
            return False

        # 授权检查
        if pi.meta.license_required and pi.license_status != 1:
            raise ValueError("Plugin requires a valid license")

        await self._enable_plugin_internal(pi)

        # 更新数据库
        from ..models.plugin import Plugin

        result = await db.execute(
            select(Plugin).where(Plugin.plugin_id == plugin_id)
        )
        db_plugin = result.scalar_one_or_none()
        if db_plugin:
            db_plugin.status = 1
        await db.commit()

        return True

    async def disable_plugin(self, plugin_id: str, db: AsyncSession) -> bool:
        """禁用插件"""
        pi = self._plugins.get(plugin_id)
        if not pi or not pi.instance:
            return False

        # 清理钩子
        hooks.off_by_owner(plugin_id)

        # 按类型注销
        if pi.meta.type == "payment":
            PAYMENT_HANDLERS.pop(plugin_id, None)

        await pi.instance.on_disable()
        pi.enabled = False

        # 更新数据库
        from ..models.plugin import Plugin

        result = await db.execute(
            select(Plugin).where(Plugin.plugin_id == plugin_id)
        )
        db_plugin = result.scalar_one_or_none()
        if db_plugin:
            db_plugin.status = 0
        await db.commit()

        return True

    async def update_plugin_config(
        self, plugin_id: str, config: Dict, db: AsyncSession
    ) -> bool:
        """更新插件配置"""
        pi = self._plugins.get(plugin_id)
        if not pi:
            return False

        pi.config = config
        if pi.instance:
            pi.instance.config = config

        # 持久化
        from ..models.plugin import Plugin

        result = await db.execute(
            select(Plugin).where(Plugin.plugin_id == plugin_id)
        )
        db_plugin = result.scalar_one_or_none()
        if db_plugin:
            db_plugin.config = json.dumps(config, ensure_ascii=False)
        await db.commit()

        return True

    def get_plugin(self, plugin_id: str) -> Optional[PluginInstance]:
        """获取插件实例"""
        return self._plugins.get(plugin_id)

    def get_plugins_by_type(self, plugin_type: str) -> List[PluginInstance]:
        """按类型获取插件列表"""
        return [
            pi for pi in self._plugins.values() if pi.meta.type == plugin_type
        ]

    def get_all_plugins(self) -> List[PluginInstance]:
        """获取所有插件"""
        return list(self._plugins.values())

    def get_payment_handler(self, handler_id: str):
        """获取支付处理器类（兼容旧接口）"""
        return PAYMENT_HANDLERS.get(handler_id)


# 全局单例
plugin_manager = PluginManager()


def get_payment_handler(handler: str):
    """
    兼容旧版支付处理器查找接口。
    先从插件系统查找，再 fallback 到旧的 payments/ 模块。
    """
    # 先查插件系统
    cls = PAYMENT_HANDLERS.get(handler)
    if cls:
        return cls

    # Fallback: 旧的 payments/ 模块
    from ..payments import PAYMENT_HANDLERS as LEGACY_HANDLERS
    return LEGACY_HANDLERS.get(handler)
