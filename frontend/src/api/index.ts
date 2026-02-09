import axios, { AxiosError, AxiosResponse, AxiosRequestConfig } from 'axios'
import { message } from 'antd'

// 创建axios实例
const instance = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 直接返回 response.data
instance.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error: AxiosError<{ message?: string; code?: number; detail?: string | any[] }>) => {
    const { response } = error
    
    if (response) {
      const { status, data } = response
      
      // 处理认证错误
      if (status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('refreshToken')
        // 如果不在登录页，跳转到登录页
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
      }
      
      // 提取错误消息
      let errorMessage = '请求失败'
      if (data?.message) {
        errorMessage = data.message
      } else if (typeof data?.detail === 'string') {
        errorMessage = data.detail
      } else if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
        errorMessage = data.detail[0].msg
      }
      
      message.error(errorMessage)
      
      // 返回带有消息的错误
      return Promise.reject(new Error(errorMessage))
    } else {
      message.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

// 包装 api，让 TypeScript 正确推断返回类型为 response.data（而非 AxiosResponse）
const api = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return instance.get(url, config) as any
  },
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return instance.post(url, data, config) as any
  },
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return instance.put(url, data, config) as any
  },
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return instance.delete(url, config) as any
  },
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return instance.patch(url, data, config) as any
  },
  // 暴露原始 instance 用于需要完整配置的场景
  instance,
}

export default api

// 类型定义
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

export interface PaginatedResponse<T> {
  total: number
  page: number
  limit: number
  items: T[]
}
