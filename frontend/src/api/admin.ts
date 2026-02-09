import api, { PaginatedResponse } from './index'

// ============== 仪表盘 ==============

export interface DashboardData {
  orders: {
    total: number
    paid: number
    today: number
    pending: number
  }
  sales: {
    today: number
    yesterday: number
    week: number
    month: number
    total: number
  }
  users: {
    total: number
    today: number
    merchants: number
    total_balance: number
    total_recharge: number
  }
  commodities: {
    total: number
    online: number
  }
  cards: {
    stock: number
    sold: number
  }
  withdrawals: {
    pending: number
    pending_amount: number
  }
  recharge: {
    today: number
  }
}

export const getDashboard = (): Promise<DashboardData> => {
  return api.get('/admin/dashboard')
}

// ============== 分类管理 ==============

export interface Category {
  id: number
  name: string
  icon?: string
  description?: string
  sort: number
  status: number
  owner_id?: number
  owner_name?: string
  level_config?: string
  created_at?: string
}

export interface CategoryForm {
  name: string
  icon?: string
  description?: string
  sort?: number
  status?: number
  level_config?: string
}

export const getCategories = (params?: { status?: number; keyword?: string }): Promise<{ items: Category[] }> => {
  return api.get('/admin/commodities/categories', { params })
}

export const createCategory = (data: CategoryForm): Promise<{ id: number }> => {
  return api.post('/admin/commodities/categories', data)
}

export const updateCategory = (id: number, data: Partial<CategoryForm>): Promise<void> => {
  return api.put(`/admin/commodities/categories/${id}`, data)
}

export const deleteCategory = (id: number): Promise<void> => {
  return api.delete(`/admin/commodities/categories/${id}`)
}

export const batchUpdateCategories = (data: { ids: number[]; action: string }): Promise<{ message: string }> => {
  return api.post('/admin/commodities/categories/batch', data)
}

// ============== 商品管理 ==============

export interface Commodity {
  id: number
  name: string
  cover?: string
  category_id: number
  price: number
  user_price: number
  stock: number
  delivery_way: number
  status: number
  sort: number
  created_at?: string
}

export interface CommodityDetail extends Commodity {
  description?: string
  factory_price: number
  delivery_auto_mode: number
  delivery_message?: string
  contact_type: number
  password_status: number
  draft_status: number
  draft_premium: number
  minimum: number
  maximum: number
  only_user: number
  widget?: string
  leave_message?: string
  send_email: number
  coupon: number
  api_status: number
  recommend: number
  hide: number
  inventory_hidden: number
  seckill_status: number
  level_disable: number
}

export interface CommodityForm {
  name: string
  description?: string
  cover?: string
  category_id: number
  price: number
  user_price: number
  factory_price?: number
  delivery_way?: number
  contact_type?: number
  password_status?: number
  draft_status?: number
  minimum?: number
  maximum?: number
  only_user?: number
  sort?: number
  status?: number
}

export const getCommodities = (params: {
  category_id?: number
  status?: number
  keywords?: string
  page?: number
  limit?: number
}): Promise<PaginatedResponse<Commodity>> => {
  return api.get('/admin/commodities', { params })
}

export const getCommodity = (id: number): Promise<CommodityDetail> => {
  return api.get(`/admin/commodities/${id}`)
}

export const createCommodity = (data: CommodityForm): Promise<{ id: number }> => {
  return api.post('/admin/commodities', data)
}

export const updateCommodity = (id: number, data: Partial<CommodityForm>): Promise<void> => {
  return api.put(`/admin/commodities/${id}`, data)
}

export const deleteCommodity = (id: number): Promise<void> => {
  return api.delete(`/admin/commodities/${id}`)
}

// ============== 卡密管理 ==============

export interface Card {
  id: number
  commodity_id: number
  commodity_name?: string
  commodity_cover?: string
  secret: string
  draft?: string
  draft_premium: number
  race?: string
  sku?: string
  note?: string
  status: number
  order_id?: number
  order_trade_no?: string
  owner_id?: number
  created_at?: string
  sold_at?: string
}

export interface CardForm {
  secret?: string
  draft?: string
  draft_premium?: number
  race?: string
  note?: string
}

export interface CardImport {
  commodity_id: number
  cards: string
  race?: string
  draft?: string
  draft_premium?: number
  note?: string
  delimiter?: string
}

export interface CardFilters {
  commodity_id?: number
  status?: number
  race?: string
  secret?: string
  secret_fuzzy?: string
  note?: string
  owner_id?: number
  start_time?: string
  end_time?: string
  page?: number
  limit?: number
}

export const getCards = (params: CardFilters): Promise<PaginatedResponse<Card>> => {
  return api.get('/admin/cards', { params })
}

export const importCards = (data: CardImport): Promise<{ count: number; message: string }> => {
  return api.post('/admin/cards/import', data)
}

export const updateCard = (id: number, data: CardForm): Promise<void> => {
  return api.put(`/admin/cards/${id}`, data)
}

export const deleteCard = (id: number): Promise<void> => {
  return api.delete(`/admin/cards/${id}`)
}

export const batchDeleteCards = (ids: number[]): Promise<{ count: number }> => {
  return api.post('/admin/cards/batch-delete', ids)
}

export const batchUpdateCardsStatus = (ids: number[], status: number): Promise<{ count: number; message: string }> => {
  return api.post('/admin/cards/batch-update-status', { ids, status })
}

// ============== 订单管理 ==============

export interface Order {
  id: number
  trade_no: string
  commodity_id: number
  commodity_name?: string
  payment_name?: string
  amount: number
  quantity: number
  contact: string
  status: number
  delivery_status: number
  created_at?: string
  paid_at?: string
}

export interface OrderDetail extends Order {
  user_id: number
  payment_id?: number
  cost: number
  race?: string
  password?: string
  secret?: string
  widget?: string
  create_ip?: string
  external_trade_no?: string
}

export const getOrders = (params: {
  status?: number
  delivery_status?: number
  trade_no?: string
  contact?: string
  page?: number
  limit?: number
}): Promise<PaginatedResponse<Order>> => {
  return api.get('/admin/orders', { params })
}

export const getOrder = (id: number): Promise<OrderDetail> => {
  return api.get(`/admin/orders/${id}`)
}

export const deliverOrder = (id: number, secret: string): Promise<void> => {
  return api.post(`/admin/orders/${id}/deliver`, { secret })
}

export const refundOrder = (id: number): Promise<void> => {
  return api.post(`/admin/orders/${id}/refund`)
}

// ============== 用户管理 ==============

export interface User {
  id: number
  username: string
  email?: string
  phone?: string
  balance: number
  coin: number
  total_recharge: number
  status: number
  is_admin: boolean
  business_level: number
  created_at?: string
  last_login_at?: string
}

export interface UserDetail extends User {
  avatar?: string
  parent_id?: number
  alipay?: string
  wechat?: string
  last_login_ip?: string
}

export const getUsers = (params: {
  status?: number
  keywords?: string
  page?: number
  limit?: number
}): Promise<PaginatedResponse<User>> => {
  return api.get('/admin/users', { params })
}

export const getUser = (id: number): Promise<UserDetail> => {
  return api.get(`/admin/users/${id}`)
}

export const updateUser = (id: number, data: {
  status?: number
  balance?: number
  is_admin?: boolean
  business_level?: number
}): Promise<void> => {
  return api.put(`/admin/users/${id}`, data)
}

export const resetUserPassword = (id: number, password: string): Promise<void> => {
  return api.post(`/admin/users/${id}/reset-password`, { password })
}

export const adjustUserBalance = (id: number, amount: number, description: string): Promise<void> => {
  return api.post(`/admin/users/${id}/adjust-balance`, { amount, description })
}

// ============== 系统设置 ==============

export interface PaymentConfig {
  id: number
  name: string
  icon?: string
  handler: string
  code?: string
  config: Record<string, any>
  cost: number
  cost_type: number
  commodity: number
  recharge: number
  equipment: number
  sort: number
  status: number
}

export const getPaymentConfigs = (): Promise<{ items: PaymentConfig[] }> => {
  return api.get('/admin/settings/payments')
}

export const createPaymentConfig = (data: Omit<PaymentConfig, 'id'>): Promise<{ id: number }> => {
  return api.post('/admin/settings/payments', data)
}

export const updatePaymentConfig = (id: number, data: Partial<PaymentConfig>): Promise<void> => {
  return api.put(`/admin/settings/payments/${id}`, data)
}

export const deletePaymentConfig = (id: number): Promise<void> => {
  return api.delete(`/admin/settings/payments/${id}`)
}

export const getSystemConfigs = (): Promise<Record<string, any[]>> => {
  return api.get('/admin/settings')
}

export const updateSystemConfigs = (configs: Record<string, any>): Promise<void> => {
  return api.put('/admin/settings', { configs })
}

// ============== 公告管理 ==============

export interface Announcement {
  id: number
  title: string
  content: string
  type: number
  is_top: number
  sort: number
  status: number
  created_at?: string
}

export const getAnnouncements = (params?: {
  status?: number
  page?: number
  limit?: number
}): Promise<PaginatedResponse<Announcement>> => {
  return api.get('/admin/announcements', { params })
}

export const createAnnouncement = (data: Omit<Announcement, 'id' | 'created_at'>): Promise<{ id: number }> => {
  return api.post('/admin/announcements', data)
}

export const updateAnnouncement = (id: number, data: Partial<Announcement>): Promise<void> => {
  return api.put(`/admin/announcements/${id}`, data)
}

export const deleteAnnouncement = (id: number): Promise<void> => {
  return api.delete(`/admin/announcements/${id}`)
}

// ============== 会员等级 ==============

export interface UserGroup {
  id: number
  name: string
  icon?: string
  color?: string
  min_recharge: number
  discount: number
  sort: number
  status: number
  created_at?: string
}

export const getUserGroups = (): Promise<{ items: UserGroup[] }> => {
  return api.get('/admin/user-groups')
}

export const createUserGroup = (data: Omit<UserGroup, 'id' | 'created_at'>): Promise<{ id: number }> => {
  return api.post('/admin/user-groups', data)
}

export const updateUserGroup = (id: number, data: Partial<UserGroup>): Promise<void> => {
  return api.put(`/admin/user-groups/${id}`, data)
}

export const deleteUserGroup = (id: number): Promise<void> => {
  return api.delete(`/admin/user-groups/${id}`)
}

// ============== 商户等级 ==============

export interface BusinessLevel {
  id: number
  name: string
  icon?: string
  price: number
  supplier_fee: number
  can_supply: number
  can_substation: number
  can_bindomain: number
  max_commodities: number
  max_substations: number
  description?: string
  sort: number
  status: number
  created_at?: string
}

export const getBusinessLevels = (): Promise<{ items: BusinessLevel[] }> => {
  return api.get('/admin/business-levels')
}

export const createBusinessLevel = (data: Omit<BusinessLevel, 'id' | 'created_at'>): Promise<{ id: number }> => {
  return api.post('/admin/business-levels', data)
}

export const updateBusinessLevel = (id: number, data: Partial<BusinessLevel>): Promise<void> => {
  return api.put(`/admin/business-levels/${id}`, data)
}

export const deleteBusinessLevel = (id: number): Promise<void> => {
  return api.delete(`/admin/business-levels/${id}`)
}

// ============== 充值订单 ==============

export interface RechargeOrder {
  id: number
  trade_no: string
  user_id: number
  username?: string
  payment_id?: number
  payment_name?: string
  amount: number
  actual_amount: number
  status: number
  create_ip?: string
  created_at?: string
  paid_at?: string
}

export const getRechargeOrders = (params?: {
  status?: number
  user_id?: number
  trade_no?: string
  page?: number
  limit?: number
}): Promise<PaginatedResponse<RechargeOrder>> => {
  return api.get('/admin/recharge', { params })
}

export const getRechargeStats = (): Promise<{
  total_count: number
  total_amount: number
  today_count: number
  today_amount: number
}> => {
  return api.get('/admin/recharge/stats')
}

export const completeRecharge = (id: number): Promise<void> => {
  return api.post(`/admin/recharge/${id}/complete`)
}

// ============== 提现管理 ==============

export interface Withdrawal {
  id: number
  withdraw_no: string
  user_id: number
  username?: string
  amount: number
  fee: number
  actual_amount: number
  method: string
  account: string
  account_name?: string
  status: number
  user_remark?: string
  admin_remark?: string
  created_at?: string
  reviewed_at?: string
  paid_at?: string
}

export const getWithdrawals = (params?: {
  status?: number
  user_id?: number
  page?: number
  limit?: number
}): Promise<PaginatedResponse<Withdrawal>> => {
  return api.get('/admin/withdrawals', { params })
}

export const getWithdrawalStats = (): Promise<{
  pending_count: number
  approved_count: number
  completed_amount: number
}> => {
  return api.get('/admin/withdrawals/stats')
}

export const reviewWithdrawal = (id: number, action: 'approve' | 'reject', remark?: string): Promise<void> => {
  return api.post(`/admin/withdrawals/${id}/review`, { action, remark })
}

export const paidWithdrawal = (id: number, remark?: string): Promise<void> => {
  return api.post(`/admin/withdrawals/${id}/paid`, { remark })
}

// ============== 仪表盘扩展 ==============

export const getDashboardAnnouncements = (): Promise<{ items: Announcement[] }> => {
  return api.get('/admin/dashboard/announcements')
}

export const getDashboardChart = (days?: number): Promise<{
  data: Array<{
    date: string
    sales: number
    recharge: number
    withdrawal: number
  }>
}> => {
  return api.get('/admin/dashboard/chart', { params: { days } })
}

// ============== 优惠券管理 ==============

export interface Coupon {
  id: number
  code: string
  money: number
  mode: number
  life: number
  use_life: number
  status: number
  remark?: string
  commodity_id?: number
  commodity_name?: string
  category_id?: number
  category_name?: string
  expires_at?: string
  created_at?: string
  used_at?: string
}

export const getCoupons = (params?: {
  status?: number
  code?: string
  commodity_id?: number
  category_id?: number
  page?: number
  limit?: number
}): Promise<PaginatedResponse<Coupon>> => {
  return api.get('/admin/coupons', { params })
}

export const getCouponStats = (): Promise<{
  total: number
  available: number
  expired: number
  locked: number
}> => {
  return api.get('/admin/coupons/stats')
}

export const createCoupons = (data: {
  count: number
  money: number
  mode?: number
  life?: number
  commodity_id?: number
  category_id?: number
  expires_days?: number
  remark?: string
}): Promise<{ count: number; codes: string[] }> => {
  return api.post('/admin/coupons', data)
}

export const updateCoupon = (id: number, data: Partial<Coupon>): Promise<void> => {
  return api.put(`/admin/coupons/${id}`, data)
}

export const deleteCoupon = (id: number): Promise<void> => {
  return api.delete(`/admin/coupons/${id}`)
}

export const batchCoupons = (ids: number[], action: 'delete' | 'lock' | 'unlock'): Promise<void> => {
  return api.post('/admin/coupons/batch', { ids, action })
}

export const exportCoupons = (ids: number[]): Promise<{ items: Coupon[] }> => {
  return api.get('/admin/coupons/export', { params: { ids: ids.join(',') } })
}

// ============== 账单管理 ==============

export interface Bill {
  id: number
  user_id: number
  username?: string
  avatar?: string
  amount: number
  balance: number
  type: number
  currency: number
  description: string
  order_trade_no?: string
  created_at?: string
}

export const getBills = (params?: {
  user_id?: number
  type?: number
  currency?: number
  page?: number
  limit?: number
}): Promise<PaginatedResponse<Bill>> => {
  return api.get('/admin/bills', { params })
}

export const getBillStats = (): Promise<{
  today_income: number
  today_expense: number
  total_income: number
  total_expense: number
}> => {
  return api.get('/admin/bills/stats')
}

// ============== 操作日志 ==============

export interface OperationLog {
  id: number
  user_id?: number
  email?: string
  action: string
  ip?: string
  user_agent?: string
  risk_level: number
  created_at?: string
}

export const getLogs = (params?: {
  user_id?: number
  email?: string
  risk_level?: number
  action?: string
  ip?: string
  page?: number
  limit?: number
}): Promise<PaginatedResponse<OperationLog>> => {
  return api.get('/admin/logs', { params })
}

export const getLogStats = (): Promise<{
  total: number
  today: number
  high_risk: number
}> => {
  return api.get('/admin/logs/stats')
}

// ============== 文件上传 ==============

export const uploadFile = (file: File, category: string = 'images'): Promise<{
  url: string
  filename: string
  size: number
  content_type: string
}> => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('category', category)
  return api.post('/admin/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const deleteUploadedFile = (category: string, filename: string): Promise<void> => {
  return api.delete(`/admin/upload/${category}/${filename}`)
}

// ============== 系统设置 ==============

export interface SystemConfig {
  key: string
  value: string
  type: string
  description: string
}

export interface GroupedSettings {
  [group: string]: SystemConfig[]
}

export const getSettings = (): Promise<GroupedSettings> => {
  return api.get('/admin/settings')
}

export const getSettingsFlat = (): Promise<Record<string, string>> => {
  return api.get('/admin/settings/flat')
}

export const updateSettings = (configs: Record<string, any>): Promise<void> => {
  return api.put('/admin/settings', { configs })
}

export const initSettings = (): Promise<{ message: string }> => {
  return api.post('/admin/settings/init')
}

// ============== 支付设置（别名，兼容新页面命名） ==============

export const getPaymentSettings = getPaymentConfigs
export const createPaymentSetting = createPaymentConfig
export const updatePaymentSetting = updatePaymentConfig
export const deletePaymentSetting = deletePaymentConfig

// ============== 插件管理扩展 ==============

export const getPlugins = (type?: string): Promise<{ items: any[]; total: number }> => {
  return api.get('/admin/plugins', { params: type ? { type } : {} })
}

export const enablePlugin = (pluginId: string): Promise<{ message: string }> => {
  return api.post(`/admin/plugins/${pluginId}/enable`)
}

export const disablePlugin = (pluginId: string): Promise<{ message: string }> => {
  return api.post(`/admin/plugins/${pluginId}/disable`)
}

export const updatePluginConfig = (pluginId: string, config: Record<string, any>): Promise<{ message: string }> => {
  return api.put(`/admin/plugins/${pluginId}/config`, config)
}

export const installPlugin = (file: File): Promise<{ message: string; plugin_id?: string }> => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/admin/plugins/install', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export const uninstallPlugin = (pluginId: string): Promise<{ message: string }> => {
  return api.delete(`/admin/plugins/${pluginId}`)
}

export const activateLicense = (pluginId: string, licenseKey: string): Promise<{ message: string }> => {
  return api.post(`/admin/plugins/${pluginId}/license`, { license_key: licenseKey })
}

export const getStorePlugins = (params?: { type?: string; keyword?: string; category?: string }): Promise<{ items: any[] }> => {
  return api.get('/admin/plugins/store', { params })
}

export const installFromStore = (pluginId: string, licenseKey?: string): Promise<{ message: string }> => {
  return api.post('/admin/plugins/store/install', null, { params: { plugin_id: pluginId, license_key: licenseKey || '' } })
}
