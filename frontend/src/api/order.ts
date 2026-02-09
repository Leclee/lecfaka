import api from './index'

export interface CreateOrderRequest {
  commodity_id: number
  quantity: number
  payment_id: number
  contact: string
  password?: string
  race?: string
  card_id?: number
  coupon?: string
  widget?: Record<string, any>
}

export interface CreateOrderResponse {
  trade_no: string
  amount: number
  status: number
  payment_url?: string
  payment_type?: string  // redirect | qrcode | form
  extra?: Record<string, any>  // form_data, qrcode_url, etc.
  secret?: string  // 余额支付成功时返回卡密
}

export interface OrderDetail {
  id: number
  trade_no: string
  amount: number
  quantity: number
  status: number
  delivery_status: number
  contact: string
  secret?: string
  created_at: string
  paid_at?: string
  commodity_name?: string
  payment_name?: string
  has_password?: boolean
}

// 创建订单
export const createOrder = (data: CreateOrderRequest): Promise<CreateOrderResponse> => {
  return api.post('/orders/create', data)
}

// 查询订单
export const getOrder = (tradeNo: string): Promise<OrderDetail> => {
  return api.get(`/orders/${tradeNo}`)
}

// 获取卡密
export const getOrderSecret = (tradeNo: string, password?: string): Promise<{ secret: string }> => {
  return api.post(`/orders/${tradeNo}/secret`, { password })
}

// 按联系方式查询订单
export const queryOrders = (contact: string, page = 1, limit = 10): Promise<{ items: OrderDetail[] }> => {
  return api.post('/orders/query', { contact }, { params: { page, limit } })
}
