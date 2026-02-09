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
