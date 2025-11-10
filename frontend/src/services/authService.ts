import { api } from './api'
import type { User } from '@/types/auth'

export const authService = {
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
}
