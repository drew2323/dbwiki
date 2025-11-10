import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const API_TIMEOUT = 30000

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  withCredentials: true, // Enable sending/receiving cookies
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('auth_token')
          // You can add router redirect logic here
          break
        case 403:
          console.error('Access forbidden')
          break
        case 404:
          console.error('Resource not found')
          break
        case 500:
          console.error('Server error')
          break
      }
    }
    return Promise.reject(error)
  }
)

// API helper methods
export const api = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.get<T>(url, config)
  },

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.post<T>(url, data, config)
  },

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.put<T>(url, data, config)
  },

  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.patch<T>(url, data, config)
  },

  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> => {
    return apiClient.delete<T>(url, config)
  },
}

export default apiClient
