/**
 * @brief 亮/暗模式切换按钮
 * @details 仅在当前主题支持暗色模式时显示
 */

import { Button, Tooltip } from 'antd'
import { useThemeStore } from '../../store'

/** 太阳图标 SVG */
const SunIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
)

/** 月亮图标 SVG */
const MoonIcon = () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
)

export default function DarkModeToggle() {
    const { themeData, colorMode, toggleColorMode } = useThemeStore()

    // 仅当主题支持暗色模式时显示
    if (!themeData?.supports_dark_mode) return null

    const isDark = colorMode === 'dark'

    return (
        <Tooltip title={isDark ? '切换到亮色模式' : '切换到暗色模式'}>
            <Button
                type="text"
                size="small"
                onClick={toggleColorMode}
                style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 32,
                    height: 32,
                    borderRadius: 8,
                    cursor: 'pointer',
                    transition: 'all 250ms cubic-bezier(0.4, 0, 0.2, 1)',
                }}
                icon={isDark ? <SunIcon /> : <MoonIcon />}
            />
        </Tooltip>
    )
}
