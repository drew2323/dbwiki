import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/authService'
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
    login,
    logout,
    clearError,
  }
})
