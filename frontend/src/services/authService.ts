import { api } from './api'
import type { User } from '@/types/auth'

export const authService = {
  // Register new user
  register: async (userData: { email: string; username: string; password: string; name?: string }): Promise<User> => {
    const response = await api.post<User>('/auth/register', userData)
    return response.data
  },

  // Login with email and password
  login: async (email: string, password: string): Promise<void> => {
    await api.post('/auth/login', { email, password })
  },

  // Get current authenticated user
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  // Logout
  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
  },

  // Get Google login URL
  getGoogleLoginUrl: (): string => {
    // Use current origin + /api for production compatibility
    // In development with Vite proxy, /api routes to localhost:8000
    // In production with Nginx, /api routes to backend container
    return `${window.location.origin}/api/auth/google`
  },

  // Request password reset
  requestPasswordReset: async (email: string): Promise<void> => {
    await api.post('/auth/request-password-reset', { email })
  },

  // Reset password with token
  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    await api.post('/auth/reset-password', { token, new_password: newPassword })
  },

  // Verify email
  verifyEmail: async (token: string): Promise<void> => {
    await api.post('/auth/verify-email', { token })
  },
}
