import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/authService'
import { useTenantStore } from './tenantStore'
import type { User } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const initialized = ref(false)

  // Computed
  const isAuthenticated = computed(() => user.value !== null)

  // Actions
  const fetchUser = async () => {
    loading.value = true
    error.value = null
    try {
      user.value = await authService.getCurrentUser()
    } catch (err: any) {
      // Not authenticated or error
      user.value = null
      if (err.response?.status !== 401) {
        error.value = err.message || 'Failed to fetch user'
      }
    } finally {
      loading.value = false
      initialized.value = true
    }
  }

  const register = async (userData: { email: string; username: string; password: string; name?: string }) => {
    loading.value = true
    error.value = null
    try {
      await authService.register(userData)
    } catch (err: any) {
      error.value = err.message || 'Failed to register'
      throw err
    } finally {
      loading.value = false
    }
  }

  const emailLogin = async (email: string, password: string) => {
    loading.value = true
    error.value = null
    try {
      await authService.login(email, password)
      await fetchUser()
      // Fetch user's tenants after successful login
      const tenantStore = useTenantStore()
      await tenantStore.fetchUserTenants()
    } catch (err: any) {
      error.value = err.message || 'Failed to login'
      throw err
    } finally {
      loading.value = false
    }
  }

  const login = () => {
    // Redirect to backend Google OAuth
    window.location.href = authService.getGoogleLoginUrl()
  }

  const logout = async () => {
    loading.value = true
    error.value = null
    try {
      await authService.logout()
      user.value = null
    } catch (err: any) {
      error.value = err.message || 'Failed to logout'
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    user,
    loading,
    error,
    initialized,

    // Computed
    isAuthenticated,

    // Actions
    fetchUser,
    register,
    emailLogin,
    login,
    logout,
    clearError,
  }
})
