import api from './index'

// 用户订单
export interface UserOrder {
  trade_no: string
  amount: number
  quantity: number
  status: number
  delivery_status: number
  created_at: string
  commodity_name?: string
}

// 账单
export interface Bill {
  id: number
  amount: number
  balance: number
  type: number
  description: string
  created_at: string
}

export interface RechargePayment {
  id: number
  name: string
  icon?: string
  handler: string
  code?: string
}

export interface RechargeUserGroup {
  id: number
  name: string
  discount: number
  min_recharge: number
  icon?: string
}

export interface RechargeBonus {
  amount: number
  bonus: number
}

export interface RechargeConfig {
  min: number
  max: number
  bonus_enabled: boolean
  bonus: RechargeBonus[]
}

export interface RechargeOptions {
  payments: RechargePayment[]
  user_groups: RechargeUserGroup[]
  recharge_config: RechargeConfig
}

export interface RechargeCreateResponse {
  trade_no: string
  amount: number
  actual_amount: number
  payment_url?: string
  payment_type?: 'redirect' | 'qrcode' | 'form'
  extra?: Record<string, any>
}

export interface RechargeOrderStatus {
  trade_no: string
  status: number
  amount: number
  actual_amount: number
  payment_id?: number
  external_trade_no?: string
  created_at?: string
  paid_at?: string
}

// 获取我的订单
export const getMyOrders = (params: {
  status?: number
  page?: number
  limit?: number
}): Promise<{ total: number; items: UserOrder[] }> => {
  return api.get('/users/me/orders', { params })
}

// 获取我的账单
export const getMyBills = (params: {
  type?: number
  page?: number
  limit?: number
}): Promise<{ total: number; items: Bill[] }> => {
  return api.get('/users/me/bills', { params })
}

export const getRechargeOptions = (): Promise<RechargeOptions> => {
  return api.get('/users/me/recharge/options')
}

export const createRecharge = (data: {
  amount: number
  payment_id: number
}): Promise<RechargeCreateResponse> => {
  return api.post('/users/me/recharge', data)
}

export const getRechargeOrderStatus = (tradeNo: string): Promise<RechargeOrderStatus> => {
  return api.get(`/users/me/recharge/${tradeNo}`)
}

// 更新用户信息
export const updateProfile = (data: {
  avatar?: string
  alipay?: string
  wechat?: string
}): Promise<{ message: string }> => {
  return api.put('/users/me', data)
}

// 修改密码
export const changePassword = (data: {
  old_password: string
  new_password: string
}): Promise<{ message: string }> => {
  return api.post('/users/me/password', data)
}

// 获取推广链接
export const getInviteLink = (): Promise<{ invite_code: string; invite_link: string }> => {
  return api.get('/users/me/invite-link')
}
