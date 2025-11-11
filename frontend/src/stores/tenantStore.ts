import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tenantService, type UserTenantAccess, type Tenant, type Role } from '@/services/tenantService'

export const useTenantStore = defineStore('tenant', () => {
  // State
  const userTenants = ref<UserTenantAccess[]>([])
  const currentTenantId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const currentTenant = computed(() => {
    if (!currentTenantId.value) return null
    const access = userTenants.value.find(
      (ut) => ut.tenant.id === currentTenantId.value
    )
    return access?.tenant || null
  })

  const currentRole = computed(() => {
    if (!currentTenantId.value) return null
    const access = userTenants.value.find(
      (ut) => ut.tenant.id === currentTenantId.value
    )
    return access?.role || null
  })

  const currentPermissions = computed(() => {
    return currentRole.value?.permissions || {}
  })

  const hasPermission = (permission: string): boolean => {
    return currentPermissions.value[permission] === true
  }

  const isAdmin = computed(() => {
    return currentRole.value?.name === 'Admin'
  })

  const isEditor = computed(() => {
    return currentRole.value?.name === 'Editor' || isAdmin.value
  })

  const isViewer = computed(() => {
    return currentRole.value?.name === 'Viewer' || isEditor.value
  })

  // Actions
  const fetchUserTenants = async () => {
    loading.value = true
    error.value = null
    try {
      const data = await tenantService.getMyTenants()
      userTenants.value = data

      // Set current tenant from localStorage or use first tenant
      const savedTenantId = localStorage.getItem('currentTenantId')
      if (savedTenantId && data.some((ut) => ut.tenant.id === savedTenantId)) {
        currentTenantId.value = savedTenantId
      } else if (data.length > 0) {
        // Default to first tenant
        currentTenantId.value = data[0].tenant.id
        localStorage.setItem('currentTenantId', data[0].tenant.id)
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch tenants'
      console.error('Error fetching tenants:', err)
    } finally {
      loading.value = false
    }
  }

  const switchTenant = (tenantId: string) => {
    const access = userTenants.value.find((ut) => ut.tenant.id === tenantId)
    if (!access) {
      error.value = 'You do not have access to this tenant'
      return
    }

    currentTenantId.value = tenantId
    localStorage.setItem('currentTenantId', tenantId)
    error.value = null

    // Emit event for components to react to tenant switch
    window.dispatchEvent(new CustomEvent('tenant-switched', { detail: { tenantId } }))
  }

  const clearTenantData = () => {
    userTenants.value = []
    currentTenantId.value = null
    localStorage.removeItem('currentTenantId')
    error.value = null
  }

  return {
    // State
    userTenants,
    currentTenantId,
    loading,
    error,

    // Computed
    currentTenant,
    currentRole,
    currentPermissions,
    isAdmin,
    isEditor,
    isViewer,

    // Actions
    fetchUserTenants,
    switchTenant,
    hasPermission,
    clearTenantData
  }
})
