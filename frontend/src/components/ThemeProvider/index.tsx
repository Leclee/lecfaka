/**
 * @brief 主题提供者组件
 * @details 在应用启动时加载主题配置，并通过 Ant Design ConfigProvider 注入主题 token。
 *          同时负责监听系统颜色偏好变化（当主题模式为 auto 时）。
 */

import { useEffect } from 'react'
import { ConfigProvider, theme as antdTheme } from 'antd'
import { useThemeStore } from '../../store'

interface ThemeProviderProps {
    children: React.ReactNode
}

export default function ThemeProvider({ children }: ThemeProviderProps) {
    const { themeData, colorMode, loadTheme, setColorMode, getAntdToken } = useThemeStore()

    // 应用启动时加载主题
    useEffect(() => {
        loadTheme()
    }, [])

    // 监听系统颜色模式变化（仅当主题模式为 auto 时）
    useEffect(() => {
        if (!themeData || themeData.mode !== 'auto') return

        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
        const handler = (e: MediaQueryListEvent) => {
            setColorMode(e.matches ? 'dark' : 'light')
        }

        mediaQuery.addEventListener('change', handler)
        return () => mediaQuery.removeEventListener('change', handler)
    }, [themeData?.mode])

    // 构建 Ant Design 主题配置
    const antdToken = getAntdToken()
    const isDark = colorMode === 'dark'

    const themeConfig = themeData ? {
        algorithm: isDark ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
        token: antdToken,
    } : undefined

    return (
        <ConfigProvider theme={themeConfig}>
            {children}
        </ConfigProvider>
    )
}
