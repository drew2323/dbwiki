import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { spaceService, type UserSpaceAccess, type Space, type Role } from '@/services/spaceService'

export const useSpaceStore = defineStore('space', () => {
  // State
  const userSpaces = ref<UserSpaceAccess[]>([])
  const currentSpaceId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const currentSpace = computed(() => {
    if (!currentSpaceId.value) return null
    const access = userSpaces.value.find(
      (us) => us.space.id === currentSpaceId.value
    )
    return access?.space || null
  })

  const currentRole = computed(() => {
    if (!currentSpaceId.value) return null
    const access = userSpaces.value.find(
      (us) => us.space.id === currentSpaceId.value
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
  const fetchUserSpaces = async () => {
    loading.value = true
    error.value = null
    try {
      const data = await spaceService.getMySpaces()
      userSpaces.value = data

      // Set current space from localStorage or use first space
      const savedSpaceId = localStorage.getItem('currentSpaceId')
      if (savedSpaceId && data.some((us) => us.space.id === savedSpaceId)) {
        currentSpaceId.value = savedSpaceId
      } else if (data.length > 0) {
        // Default to first space
        currentSpaceId.value = data[0].space.id
        localStorage.setItem('currentSpaceId', data[0].space.id)
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch spaces'
      console.error('Error fetching spaces:', err)
    } finally {
      loading.value = false
    }
  }

  const switchSpace = (spaceId: string) => {
    const access = userSpaces.value.find((us) => us.space.id === spaceId)
    if (!access) {
      error.value = 'You do not have access to this space'
      return
    }

    currentSpaceId.value = spaceId
    localStorage.setItem('currentSpaceId', spaceId)
    error.value = null

    // Emit event for components to react to space switch
    window.dispatchEvent(new CustomEvent('space-switched', { detail: { spaceId } }))
  }

  const clearSpaceData = () => {
    userSpaces.value = []
    currentSpaceId.value = null
    localStorage.removeItem('currentSpaceId')
    error.value = null
  }

  return {
    // State
    userSpaces,
    currentSpaceId,
    loading,
    error,

    // Computed
    currentSpace,
    currentRole,
    currentPermissions,
    isAdmin,
    isEditor,
    isViewer,

    // Actions
    fetchUserSpaces,
    switchSpace,
    hasPermission,
    clearSpaceData
  }
})
