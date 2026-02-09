import api from './index'

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
  phone?: string
  invite_code?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserInfo {
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
  created_at: string
}

// 登录
export const login = (data: LoginRequest): Promise<TokenResponse> => {
  return api.post('/auth/login', data)
}

// 注册
export const register = (data: RegisterRequest): Promise<TokenResponse> => {
  return api.post('/auth/register', data)
}

// 刷新Token
export const refreshToken = (refresh_token: string): Promise<TokenResponse> => {
  return api.post('/auth/refresh', { refresh_token })
}

// 获取当前用户信息
export const getCurrentUser = (): Promise<UserInfo> => {
  return api.get('/auth/me')
}

// 退出登录
export const logout = (): Promise<void> => {
  return api.post('/auth/logout')
}
