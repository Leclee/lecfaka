/**
 * @brief 主题状态管理 (Zustand Store)
 * @details 管理当前激活的主题配置，支持亮/暗模式切换，
 *          将 CSS Variables 注入 DOM，与 Ant Design ConfigProvider 集成
 */

import { create } from 'zustand'
import { getTheme, ThemeData } from '../api/shop'

/** 实际应用的颜色模式 */
type ColorMode = 'light' | 'dark'

interface ThemeState {
    /** 主题数据（来自后端） */
    themeData: ThemeData | null
    /** 当前颜色模式 */
    colorMode: ColorMode
    /** 是否正在加载 */
    loading: boolean
    /** 是否已初始化 */
    initialized: boolean

    // Actions
    /** 从后端加载主题配置 */
    loadTheme: () => Promise<void>
    /** 切换颜色模式 */
    toggleColorMode: () => void
    /** 设置颜色模式 */
    setColorMode: (mode: ColorMode) => void
    /** 获取当前生效的 Ant Design token */
    getAntdToken: () => Record<string, any>
}

/**
 * @brief 检测系统偏好的颜色模式
 */
function getSystemColorMode(): ColorMode {
    if (typeof window !== 'undefined' && window.matchMedia) {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }
    return 'light'
}

/**
 * @brief 将 CSS Variables 注入到 document.documentElement
 */
function applyCssVariables(variables: Record<string, string>) {
    const root = document.documentElement
    Object.entries(variables).forEach(([key, value]) => {
        root.style.setProperty(key, value)
    })
}

/**
 * @brief 加载外部字体
 */
function loadFont(url: string) {
    const existingLink = document.getElementById('theme-font-link')
    if (existingLink) {
        existingLink.setAttribute('href', url)
        return
    }
    const link = document.createElement('link')
    link.id = 'theme-font-link'
    link.rel = 'stylesheet'
    link.href = url
    document.head.appendChild(link)
}

/**
 * @brief 清除主题相关的 CSS Variables
 */
function clearCssVariables() {
    const root = document.documentElement
    const style = root.style
    const toRemove: string[] = []
    for (let i = 0; i < style.length; i++) {
        const prop = style[i]
        if (prop.startsWith('--theme-')) {
            toRemove.push(prop)
        }
    }
    toRemove.forEach(prop => root.style.removeProperty(prop))
}

export const useThemeStore = create<ThemeState>()((set, get) => ({
    themeData: null,
    colorMode: 'light',
    loading: false,
    initialized: false,

    loadTheme: async () => {
        set({ loading: true })
        try {
            const res = await getTheme()
            const theme = res.theme

            if (theme) {
                // 根据主题配置的 mode 决定初始颜色模式
                let initialMode: ColorMode = 'light'
                if (theme.mode === 'dark') {
                    initialMode = 'dark'
                } else if (theme.mode === 'auto') {
                    initialMode = getSystemColorMode()
                }

                // 应用 CSS Variables
                const isDark = initialMode === 'dark'
                const cssVars = (isDark && theme.css_variables_dark) ? theme.css_variables_dark : theme.css_variables
                applyCssVariables(cssVars)

                // 在 body 上设置 data-theme 属性
                document.documentElement.setAttribute('data-theme', initialMode)

                // 加载自定义字体
                if (theme.font_import_url) {
                    loadFont(theme.font_import_url)
                }

                set({ themeData: theme, colorMode: initialMode })
            } else {
                // 没有激活主题，清理残留变量
                clearCssVariables()
                document.documentElement.removeAttribute('data-theme')
            }
        } catch (e) {
            // 主题加载失败不阻断应用
            console.warn('Failed to load theme:', e)
        } finally {
            set({ loading: false, initialized: true })
        }
    },

    toggleColorMode: () => {
        const current = get().colorMode
        const next: ColorMode = current === 'light' ? 'dark' : 'light'
        get().setColorMode(next)
    },

    setColorMode: (mode: ColorMode) => {
        const theme = get().themeData
        if (!theme) return

        const isDark = mode === 'dark'
        const cssVars = (isDark && theme.css_variables_dark) ? theme.css_variables_dark : theme.css_variables
        applyCssVariables(cssVars)
        document.documentElement.setAttribute('data-theme', mode)

        set({ colorMode: mode })
    },

    getAntdToken: () => {
        const { themeData, colorMode } = get()
        if (!themeData) return {}

        const isDark = colorMode === 'dark'
        return (isDark && themeData.antd_token_dark) ? themeData.antd_token_dark : themeData.antd_token
    },
}))
