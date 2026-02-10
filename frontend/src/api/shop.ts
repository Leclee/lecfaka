import api, { PaginatedResponse } from './index'

export interface Category {
  id: number
  name: string
  icon?: string
  sort: number
}

export interface Commodity {
  id: number
  name: string
  cover?: string
  price: number
  user_price: number
  category_id: number
  stock: number
  sold_count: number
  delivery_way: number
  recommend: number
}

export interface CategoryConfig {
  name: string
  price: number
}

export interface WholesaleConfig {
  quantity: number
  price?: number  // 固定价格
  discount_percent?: number  // 百分比折扣（如90表示9折）
  type: 'fixed' | 'percent'  // 类型
}

export interface SkuConfig {
  group: string
  option: string
  extra_price: number
}

export interface CommodityDetail {
  id: number
  name: string
  description?: string
  cover?: string
  price: number
  user_price: number
  category_id: number
  stock: number
  sold_count?: number
  delivery_way: number
  contact_type: number
  password_status: number
  draft_status: number
  draft_premium: number
  minimum: number
  maximum: number
  only_user: number
  widget?: string
  leave_message?: string
  wholesale_config?: string
  // 解析后的配置参数
  categories?: CategoryConfig[] | null
  wholesale?: WholesaleConfig[] | null
  sku_config?: SkuConfig[] | null
  category_wholesale?: Record<string, WholesaleConfig[]> | null
}

export interface CardDraft {
  id: number
  draft?: string
  draft_premium: number
}

export interface PaymentMethod {
  id: number
  name: string
  icon?: string
  handler: string
  code?: string
}

// 获取分类列表
export const getCategories = (): Promise<Category[]> => {
  return api.get('/shop/categories')
}

// 获取商品列表
export const getCommodities = (params: {
  category_id?: number
  keywords?: string
  recommend?: number
  page?: number
  limit?: number
}): Promise<PaginatedResponse<Commodity>> => {
  return api.get('/shop/commodities', { params })
}

// 获取商品详情
export const getCommodityDetail = (id: number): Promise<CommodityDetail> => {
  return api.get(`/shop/commodities/${id}`)
}

// 获取预选卡密
export const getCommodityCards = (id: number, params: {
  race?: string
  page?: number
  limit?: number
}): Promise<{ total: number; items: CardDraft[] }> => {
  return api.get(`/shop/commodities/${id}/cards`, { params })
}

// 获取支付方式
export const getPayments = (): Promise<PaymentMethod[]> => {
  return api.get('/shop/payments')
}

// ============== 主题相关 ==============

/** 主题配置响应类型 */
export interface ThemeResponse {
  theme: ThemeData | null
}

/** 主题配置数据 */
export interface ThemeData {
  name: string
  mode: string  // 'light' | 'dark' | 'auto'
  css_variables: Record<string, string>
  css_variables_dark: Record<string, string> | null
  antd_token: Record<string, any>
  antd_token_dark: Record<string, any> | null
  font_import_url: string | null
  supports_dark_mode: boolean
}

/** 获取当前激活主题配置 */
export const getTheme = (): Promise<ThemeResponse> => {
  return api.get('/shop/theme')
}

