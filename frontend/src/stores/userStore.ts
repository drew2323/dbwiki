/**
 * User Store
 * Manages user data and operations for the admin panel
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userService, type UsersQueryParams } from '@/services/userService'
import type { User, UpdateUser } from '@/types/admin'

export const useUserStore = defineStore('userManagement', () => {
  // State
  const users = ref<User[]>([])
  const selectedUser = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const activeUsers = computed(() => users.value.filter(u => u.is_active))
  const inactiveUsers = computed(() => users.value.filter(u => !u.is_active))
  const userCount = computed(() => users.value.length)

  // Actions
  async function fetchUsers(params?: UsersQueryParams) {
    loading.value = true
    error.value = null
    try {
      users.value = await userService.getUsers(params)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch users'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getUserById(userId: string) {
    loading.value = true
    error.value = null
    try {
      const user = await userService.getUserById(userId)
      selectedUser.value = user
      return user
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch user'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateUser(userId: string, data: UpdateUser) {
    loading.value = true
    error.value = null
    try {
      const updatedUser = await userService.updateUser(userId, data)
      // Update in local state
      const index = users.value.findIndex(u => u.id === userId)
      if (index !== -1) {
        users.value[index] = updatedUser
      }
      if (selectedUser.value?.id === userId) {
        selectedUser.value = updatedUser
      }
      return updatedUser
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update user'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function activateUser(userId: string) {
    loading.value = true
    error.value = null
    try {
      await userService.activateUser(userId)
      // Update local state
      const user = users.value.find(u => u.id === userId)
      if (user) {
        user.is_active = true
      }
      if (selectedUser.value?.id === userId) {
        selectedUser.value.is_active = true
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to activate user'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deactivateUser(userId: string) {
    loading.value = true
    error.value = null
    try {
      await userService.deactivateUser(userId)
      // Update local state
      const user = users.value.find(u => u.id === userId)
      if (user) {
        user.is_active = false
      }
      if (selectedUser.value?.id === userId) {
        selectedUser.value.is_active = false
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to deactivate user'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteUser(userId: string) {
    loading.value = true
    error.value = null
    try {
      await userService.deleteUser(userId)
      // Remove from local state
      users.value = users.value.filter(u => u.id !== userId)
      if (selectedUser.value?.id === userId) {
        selectedUser.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to delete user'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function grantSuperuser(userId: string) {
    loading.value = true
    error.value = null
    try {
      await userService.grantSuperuser(userId)
      // Update local state
      const user = users.value.find(u => u.id === userId)
      if (user) {
        user.is_superuser = true
      }
      if (selectedUser.value?.id === userId) {
        selectedUser.value.is_superuser = true
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to grant superuser'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function revokeSuperuser(userId: string) {
    loading.value = true
    error.value = null
    try {
      await userService.revokeSuperuser(userId)
      // Update local state
      const user = users.value.find(u => u.id === userId)
      if (user) {
        user.is_superuser = false
      }
      if (selectedUser.value?.id === userId) {
        selectedUser.value.is_superuser = false
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to revoke superuser'
      throw err
    } finally {
      loading.value = false
    }
  }

  function setSelectedUser(user: User | null) {
    selectedUser.value = user
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    users,
    selectedUser,
    loading,
    error,
    // Computed
    activeUsers,
    inactiveUsers,
    userCount,
    // Actions
    fetchUsers,
    getUserById,
    updateUser,
    activateUser,
    deactivateUser,
    deleteUser,
    grantSuperuser,
    revokeSuperuser,
    setSelectedUser,
    clearError
  }
})
