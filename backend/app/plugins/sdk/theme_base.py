"""
主题插件基类
所有主题类型插件的基类，定义了主题配置的标准结构
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from .base import PluginBase, PluginMeta


@dataclass
class ThemeColors:
    """
    @brief 主题色彩配置
    @details 定义主题中所有颜色变量
    """
    primary: str = "#1677ff"           ## 主色
    primary_hover: str = "#4096ff"     ## 主色悬停
    secondary: str = "#722ed1"         ## 辅助色
    accent: str = "#f5222d"            ## 强调色/CTA
    background: str = "#ffffff"        ## 页面背景
    surface: str = "#fafafa"           ## 卡片/面板背景
    surface_hover: str = "#f5f5f5"     ## 卡片悬停背景
    text_primary: str = "#000000d9"    ## 主要文本
    text_secondary: str = "#00000073"  ## 次要文本
    text_muted: str = "#00000040"      ## 弱化文本
    border: str = "#d9d9d9"            ## 边框色
    divider: str = "#f0f0f0"           ## 分割线
    success: str = "#52c41a"           ## 成功色
    warning: str = "#faad14"           ## 警告色
    error: str = "#f5222d"             ## 错误色
    info: str = "#1677ff"              ## 信息色

    ## 渐变色
    gradient_start: str = "#1677ff"    ## 渐变起始
    gradient_end: str = "#722ed1"      ## 渐变结束


@dataclass
class ThemeTypography:
    """
    @brief 主题字体配置
    """
    heading_font: str = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto"
    body_font: str = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto"
    mono_font: str = "'SFMono-Regular', Consolas, monospace"
    font_import_url: Optional[str] = None  ## Google Fonts 或其他字体 CDN URL
    base_size: int = 14                     ## 基础字号(px)
    heading_weight: int = 600               ## 标题字重


@dataclass
class ThemeLayout:
    """
    @brief 主题布局配置
    """
    border_radius: int = 8           ## 基础圆角(px)
    border_radius_lg: int = 12       ## 大圆角
    border_radius_sm: int = 4        ## 小圆角
    header_height: int = 64          ## 顶栏高度(px)
    content_max_width: int = 1280    ## 内容最大宽度(px)


@dataclass
class ThemeEffects:
    """
    @brief 主题特效配置
    """
    shadow_sm: str = "0 1px 2px rgba(0,0,0,0.05)"
    shadow_md: str = "0 4px 6px rgba(0,0,0,0.1)"
    shadow_lg: str = "0 10px 15px rgba(0,0,0,0.1)"
    shadow_xl: str = "0 20px 25px rgba(0,0,0,0.15)"
    backdrop_blur: str = "blur(12px)"         ## 毛玻璃模糊度
    transition_duration: str = "200ms"        ## 默认过渡时长
    transition_timing: str = "ease"           ## 默认过渡曲线
    glass_bg: str = "rgba(255,255,255,0.8)"   ## 毛玻璃背景色
    glass_border: str = "rgba(255,255,255,0.3)"  ## 毛玻璃边框


@dataclass
class ThemeConfig:
    """
    @brief 完整的主题配置
    @details 包含颜色、字体、布局、特效四大部分
    """
    id: str = "default"                 ## 主题内部ID（同一插件包多主题时区分）
    name: str = "默认主题"
    mode: str = "light"                 ## light | dark
    colors: ThemeColors = field(default_factory=ThemeColors)
    dark_colors: Optional[ThemeColors] = None   ## 暗色模式颜色（可选）
    typography: ThemeTypography = field(default_factory=ThemeTypography)
    layout: ThemeLayout = field(default_factory=ThemeLayout)
    effects: ThemeEffects = field(default_factory=ThemeEffects)

    def to_css_variables(self, dark: bool = False) -> Dict[str, str]:
        """
        @brief 将主题配置转换为 CSS Variables 字典
        @param dark 是否使用暗色模式
        @return CSS 变量名到值的映射
        """
        colors = self.dark_colors if (dark and self.dark_colors) else self.colors
        variables = {
            ## 颜色变量
            "--theme-primary": colors.primary,
            "--theme-primary-hover": colors.primary_hover,
            "--theme-secondary": colors.secondary,
            "--theme-accent": colors.accent,
            "--theme-bg": colors.background,
            "--theme-surface": colors.surface,
            "--theme-surface-hover": colors.surface_hover,
            "--theme-text": colors.text_primary,
            "--theme-text-secondary": colors.text_secondary,
            "--theme-text-muted": colors.text_muted,
            "--theme-border": colors.border,
            "--theme-divider": colors.divider,
            "--theme-success": colors.success,
            "--theme-warning": colors.warning,
            "--theme-error": colors.error,
            "--theme-info": colors.info,
            "--theme-gradient-start": colors.gradient_start,
            "--theme-gradient-end": colors.gradient_end,
            ## 字体变量
            "--theme-font-heading": self.typography.heading_font,
            "--theme-font-body": self.typography.body_font,
            "--theme-font-mono": self.typography.mono_font,
            "--theme-font-size-base": f"{self.typography.base_size}px",
            "--theme-font-weight-heading": str(self.typography.heading_weight),
            ## 布局变量
            "--theme-radius": f"{self.layout.border_radius}px",
            "--theme-radius-lg": f"{self.layout.border_radius_lg}px",
            "--theme-radius-sm": f"{self.layout.border_radius_sm}px",
            "--theme-header-height": f"{self.layout.header_height}px",
            "--theme-content-max-width": f"{self.layout.content_max_width}px",
            ## 特效变量
            "--theme-shadow-sm": self.effects.shadow_sm,
            "--theme-shadow-md": self.effects.shadow_md,
            "--theme-shadow-lg": self.effects.shadow_lg,
            "--theme-shadow-xl": self.effects.shadow_xl,
            "--theme-backdrop-blur": self.effects.backdrop_blur,
            "--theme-transition": f"all {self.effects.transition_duration} {self.effects.transition_timing}",
            "--theme-glass-bg": self.effects.glass_bg,
            "--theme-glass-border": self.effects.glass_border,
        }
        return variables

    def to_antd_token(self, dark: bool = False) -> Dict[str, Any]:
        """
        @brief 将主题配置转换为 Ant Design 5 的 ConfigProvider token
        @param dark 是否使用暗色模式
        @return Ant Design token 配置
        """
        colors = self.dark_colors if (dark and self.dark_colors) else self.colors
        return {
            "colorPrimary": colors.primary,
            "colorSuccess": colors.success,
            "colorWarning": colors.warning,
            "colorError": colors.error,
            "colorInfo": colors.info,
            "colorBgContainer": colors.surface,
            "colorBgLayout": colors.background,
            "colorBgElevated": colors.surface,
            "colorText": colors.text_primary,
            "colorTextSecondary": colors.text_secondary,
            "colorBorder": colors.border,
            "colorSplit": colors.divider,
            "borderRadius": self.layout.border_radius,
            "borderRadiusLG": self.layout.border_radius_lg,
            "borderRadiusSM": self.layout.border_radius_sm,
            "fontSize": self.typography.base_size,
            "fontFamily": self.typography.body_font,
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        @brief 序列化为完整字典，用于 API 响应
        """
        return {
            "id": self.id,
            "name": self.name,
            "mode": self.mode,
            "css_variables": self.to_css_variables(dark=False),
            "css_variables_dark": self.to_css_variables(dark=True) if self.dark_colors else None,
            "antd_token": self.to_antd_token(dark=False),
            "antd_token_dark": self.to_antd_token(dark=True) if self.dark_colors else None,
            "font_import_url": self.typography.font_import_url,
            "supports_dark_mode": self.dark_colors is not None,
        }


class ThemePluginBase(PluginBase):
    """
    @brief 主题插件基类
    @details 所有主题插件必须继承此类，通过 get_all_themes 返回该包包含的主题，或者为了兼容仅实现 get_theme_config 。
    """

    def __init__(self, meta: PluginMeta, config: Dict[str, Any]):
        super().__init__(meta, config)
        self._theme_configs: Dict[str, ThemeConfig] = {}
        self._active_theme_id: str = "default"

    def get_theme_config(self) -> ThemeConfig:
        """
        @brief （向后兼容）获取单个主题配置
        @details 新插件如果不想要单主题模式，请覆盖 get_all_themes 即可，不用实现此方法。
        """
        raise NotImplementedError("Theme must implement get_all_themes or get_theme_config")

    def get_all_themes(self) -> Dict[str, ThemeConfig]:
        """
        @brief 获取此主题包内所有的主题配置
        @return Dict[str, ThemeConfig] 主题id -> 主题配置
        """
        # 兼容旧版本插件单主题写法
        try:
            single = self.get_theme_config()
            return {single.id: single}
        except NotImplementedError:
            return {}

    async def on_enable(self) -> None:
        """@brief 启用时构建并缓存主题配置"""
        await super().on_enable()
        self._theme_configs = self.get_all_themes()
        
        # 加载配置的激活主题，若无且有多个则默认第一个
        saved_id = self.config.get("active_theme_id", "")
        if saved_id in self._theme_configs:
            self._active_theme_id = saved_id
        elif self._theme_configs:
            self._active_theme_id = list(self._theme_configs.keys())[0]
            
        self.logger.info(f"Theme pack loaded: {self.meta.name}, active variations: {len(self._theme_configs)}")

    async def on_disable(self) -> None:
        """@brief 禁用时清理缓存"""
        self._theme_configs = {}
        await super().on_disable()

    @property
    def theme_config(self) -> Optional[ThemeConfig]:
        """@brief 获取目前被激活的主题配置（供全局调用）"""
        return self._theme_configs.get(self._active_theme_id)

    @property
    def all_themes(self) -> Dict[str, ThemeConfig]:
        """@brief 获取包内所有主题配置"""
        return self._theme_configs

    def set_active_theme_id(self, theme_id: str) -> bool:
        """@brief 切换本插件包内的活动主题 ID"""
        if theme_id in self._theme_configs:
            self._active_theme_id = theme_id
            self.config["active_theme_id"] = theme_id
            return True
        return False
