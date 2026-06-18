/**
 * Axios 配置 - 自动添加认证头
 */
import axios from 'axios'
import { getApiKey, clearApiKey } from './auth'
import { ElMessage } from 'element-plus'

// 创建axios实例
const instance = axios.create({
  baseURL: '/',
  timeout: 60000
})

// 请求拦截器 - 添加API密钥
instance.interceptors.request.use(
  config => {
    const apiKey = getApiKey()
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理认证错误
instance.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      const { status, data } = error.response
      
      // 处理认证相关错误
      if (status === 401 || status === 403) {
        if (data?.code === 'MISSING_KEY' || data?.code === 'INVALID_KEY') {
          ElMessage.error(data.error || '认证失败')
          clearApiKey()
          
          // 触发全局事件，要求重新认证
          window.dispatchEvent(new CustomEvent('auth-required'))
        }
      } else if (status === 429) {
        ElMessage.error('请求过于频繁，请稍后重试')
      }
    }
    
    return Promise.reject(error)
  }
)

export default instance
