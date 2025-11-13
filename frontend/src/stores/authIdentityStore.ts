/**
 * Auth Identity Store
 * Manages authentication identities for users
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authIdentityService } from '@/services/authIdentityService'
import type { AuthIdentity, AuthProvider, CreateAuthIdentity, UpdateAuthIdentity } from '@/types/admin'

export const useAuthIdentityStore = defineStore('authIdentity', () => {
  // State
  const identities = ref<AuthIdentity[]>([])
  const availableProviders = ref<AuthProvider[]>([])
  const selectedIdentity = ref<AuthIdentity | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const identitiesByProvider = computed(() => {
    const grouped: Record<string, AuthIdentity[]> = {}
    identities.value.forEach(identity => {
      if (!grouped[identity.provider]) {
        grouped[identity.provider] = []
      }
      grouped[identity.provider].push(identity)
    })
    return grouped
  })

  const identityCount = computed(() => identities.value.length)

  // Actions
  async function fetchUserIdentities(userId: string) {
    loading.value = true
    error.value = null
    try {
      identities.value = await authIdentityService.getUserIdentities(userId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch identities'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createIdentity(userId: string, data: CreateAuthIdentity) {
    loading.value = true
    error.value = null
    try {
      const newIdentity = await authIdentityService.createIdentity(userId, data)
      identities.value.push(newIdentity)
      return newIdentity
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create identity'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateIdentity(identityId: string, data: UpdateAuthIdentity) {
    loading.value = true
    error.value = null
    try {
      const updatedIdentity = await authIdentityService.updateIdentity(identityId, data)
      // Update in local state
      const index = identities.value.findIndex(i => i.id === identityId)
      if (index !== -1) {
        identities.value[index] = updatedIdentity
      }
      if (selectedIdentity.value?.id === identityId) {
        selectedIdentity.value = updatedIdentity
      }
      return updatedIdentity
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update identity'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteIdentity(identityId: string) {
    loading.value = true
    error.value = null
    try {
      await authIdentityService.deleteIdentity(identityId)
      // Remove from local state
      identities.value = identities.value.filter(i => i.id !== identityId)
      if (selectedIdentity.value?.id === identityId) {
        selectedIdentity.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to delete identity'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchProviders() {
    loading.value = true
    error.value = null
    try {
      availableProviders.value = await authIdentityService.getAvailableProviders()
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch providers'
      throw err
    } finally {
      loading.value = false
    }
  }

  function setSelectedIdentity(identity: AuthIdentity | null) {
    selectedIdentity.value = identity
  }

  function clearIdentities() {
    identities.value = []
    selectedIdentity.value = null
  }

  function clearError() {
    error.value = null
  }

  return {
    // State
    identities,
    availableProviders,
    selectedIdentity,
    loading,
    error,
    // Computed
    identitiesByProvider,
    identityCount,
    // Actions
    fetchUserIdentities,
    createIdentity,
    updateIdentity,
    deleteIdentity,
    fetchProviders,
    setSelectedIdentity,
    clearIdentities,
    clearError
  }
})
