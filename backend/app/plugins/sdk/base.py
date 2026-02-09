"""
插件基类
所有插件类型的根基类
"""

import logging
from abc import ABC
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("plugins")


@dataclass
class PluginMeta:
    """插件元数据（从 plugin.json 解析）"""
    id: str
    name: str
    version: str
    type: str  # payment | theme | notify | delivery | extension
    author: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    icon: Optional[str] = None
    min_app_version: Optional[str] = None
    max_app_version: Optional[str] = None
    license_required: bool = False
    price: float = 0.0
    config_schema: Dict[str, Any] = field(default_factory=dict)
    backend: Dict[str, Any] = field(default_factory=dict)
    frontend: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    changelog: Dict[str, str] = field(default_factory=dict)


class PluginBase(ABC):
    """
    所有插件的基类。

    生命周期:
    1. __init__(meta, config)   - 实例化
    2. on_install()             - 首次安装
    3. on_enable()              - 启用（注册钩子等）
    4. on_disable()             - 禁用（清理钩子等）
    5. on_uninstall()           - 卸载（清理数据）
    """

    def __init__(self, meta: PluginMeta, config: Dict[str, Any]):
        self.meta = meta
        self.config = config
        self._enabled = False
        self.logger = logging.getLogger(f"plugins.{meta.id}")

    @property
    def id(self) -> str:
        return self.meta.id

    @property
    def name(self) -> str:
        return self.meta.name

    @property
    def plugin_type(self) -> str:
        return self.meta.type

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def on_install(self) -> None:
        """插件首次安装时调用"""
        self.logger.info(f"Plugin installed: {self.name} v{self.meta.version}")

    async def on_enable(self) -> None:
        """插件启用时调用（注册钩子、初始化资源）"""
        self._enabled = True
        self.logger.info(f"Plugin enabled: {self.name}")

    async def on_disable(self) -> None:
        """插件禁用时调用（清理钩子、释放资源）"""
        self._enabled = False
        self.logger.info(f"Plugin disabled: {self.name}")

    async def on_uninstall(self) -> None:
        """插件卸载时调用（清理持久化数据）"""
        self.logger.info(f"Plugin uninstalled: {self.name}")

    def validate_config(self) -> List[str]:
        """
        验证配置。返回错误消息列表，空列表表示通过。
        子类可重写添加自定义验证。
        """
        errors = []
        for key, schema in self.meta.config_schema.items():
            if schema.get("required") and not self.config.get(key):
                label = schema.get("label", key)
                errors.append(f"Missing required config: {label}")
        return errors

    def get_config(self, key: str, default: Any = None) -> Any:
        """安全获取配置值"""
        return self.config.get(key, default)

    def __repr__(self) -> str:
        status = "enabled" if self._enabled else "disabled"
        return f"<Plugin {self.meta.id} v{self.meta.version} [{status}]>"
