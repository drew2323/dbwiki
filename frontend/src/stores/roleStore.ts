/**
 * Role Store
 * Manages roles and permissions
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { roleService } from '@/services/roleService'
import type { Role, CreateRole, UpdateRole } from '@/types/admin'

export const useRoleStore = defineStore('role', () => {
  // State
  const roles = ref<Role[]>([])
  const selectedRole = ref<Role | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const rolesByTenant = computed(() => {
    const grouped: Record<string, Role[]> = {}
    roles.value.forEach(role => {
      if (!grouped[role.tenant_id]) {
        grouped[role.tenant_id] = []
      }
      grouped[role.tenant_id].push(role)
    })
    return grouped
  })

  const roleCount = computed(() => roles.value.length)

  // Actions
  async function fetchRoles(tenantId?: string) {
    loading.value = true
    error.value = null
    try {
      roles.value = await roleService.getRoles(tenantId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch roles'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function getRoleById(roleId: string) {
    loading.value = true
    error.value = null
    try {
      const role = await roleService.getRoleById(roleId)
      selectedRole.value = role
      return role
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch role'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createRole(data: CreateRole) {
    loading.value = true
    error.value = null
    try {
      const newRole = await roleService.createRole(data)
      roles.value.push(newRole)
      return newRole
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create role'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateRole(roleId: string, data: UpdateRole) {
    loading.value = true
    error.value = null
    try {
      const updatedRole = await roleService.updateRole(roleId, data)
      // Update in local state
      const index = roles.value.findIndex(r => r.id === roleId)
      if (index !== -1) {
        roles.value[index] = updatedRole
      }
      if (selectedRole.value?.id === roleId) {
        selectedRole.value = updatedRole
      }
      return updatedRole
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update role'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteRole(roleId: string) {
    loading.value = true
    error.value = null
    try {
      await roleService.deleteRole(roleId)
      // Remove from local state
      roles.value = roles.value.filter(r => r.id !== roleId)
      if (selectedRole.value?.id === roleId) {
        selectedRole.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to delete role'
      throw err
    } finally {
      loading.value = false
    }
  }

  function setSelectedRole(role: Role | null) {
    selectedRole.value = role
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    roles,
    selectedRole,
    loading,
    error,
    // Computed
    rolesByTenant,
    roleCount,
    // Actions
    fetchRoles,
    getRoleById,
    createRole,
    updateRole,
    deleteRole,
    setSelectedRole,
    clearError
  }
})
