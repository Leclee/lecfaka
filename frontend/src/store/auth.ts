import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import * as authApi from '../api/auth'

interface User {
  id: number
  username: string
  email?: string
  phone?: string
  avatar?: string
  balance: number
  coin: number
  total_recharge?: number
  is_admin: boolean
  business_level: number
  alipay?: string
  wechat?: string
  qq?: string
}

interface AuthState {
  token: string | null
  refreshToken: string | null
  user: User | null
  isLoading: boolean
  
  // Actions
  login: (username: string, password: string) => Promise<void>
  register: (data: authApi.RegisterRequest) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  setToken: (token: string, refreshToken: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,
      isLoading: false,
      
      login: async (username: string, password: string) => {
        set({ isLoading: true })
        try {
          const res = await authApi.login({ username, password })
          set({
            token: res.access_token,
            refreshToken: res.refresh_token,
          })
          // 存储到 localStorage
          localStorage.setItem('token', res.access_token)
          localStorage.setItem('refreshToken', res.refresh_token)
          // 获取用户信息
          await get().fetchUser()
        } finally {
          set({ isLoading: false })
        }
      },
      
      register: async (data: authApi.RegisterRequest) => {
        set({ isLoading: true })
        try {
          const res = await authApi.register(data)
          set({
            token: res.access_token,
            refreshToken: res.refresh_token,
          })
          localStorage.setItem('token', res.access_token)
          localStorage.setItem('refreshToken', res.refresh_token)
          await get().fetchUser()
        } finally {
          set({ isLoading: false })
        }
      },
      
      logout: () => {
        set({ token: null, refreshToken: null, user: null })
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
      },
      
      fetchUser: async () => {
        const token = get().token || localStorage.getItem('token')
        if (!token) return
        
        try {
          const user = await authApi.getCurrentUser()
          set({ user })
        } catch (error) {
          // 只有在 401 错误时才登出，其他错误不处理
          if ((error as any)?.response?.status === 401) {
            get().logout()
          }
        }
      },
      
      setToken: (token: string, refreshToken: string) => {
        set({ token, refreshToken })
        localStorage.setItem('token', token)
        localStorage.setItem('refreshToken', refreshToken)
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        // 页面加载后，如果有 token，自动获取用户信息
        if (state?.token && !state?.user) {
          state.fetchUser()
        }
      },
    }
  )
)
