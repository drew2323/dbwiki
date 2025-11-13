/**
 * Auth Identity Service
 * Handles API calls for managing user authentication providers
 */
import { api } from './api'
import type { AuthIdentity, CreateAuthIdentity, UpdateAuthIdentity, AuthProvider } from '@/types/admin'

export const authIdentityService = {
  /**
   * Get all auth identities for a specific user
   */
  async getUserIdentities(userId: string): Promise<AuthIdentity[]> {
    const response = await api.get<AuthIdentity[]>(`/users/${userId}/identities`)
    return response.data
  },

  /**
   * Add a new auth identity to a user
   */
  async createIdentity(userId: string, data: CreateAuthIdentity): Promise<AuthIdentity> {
    const response = await api.post<AuthIdentity>(`/users/${userId}/identities`, data)
    return response.data
  },

  /**
   * Update an auth identity's metadata
   */
  async updateIdentity(identityId: string, data: UpdateAuthIdentity): Promise<AuthIdentity> {
    const response = await api.put<AuthIdentity>(`/identities/${identityId}`, data)
    return response.data
  },

  /**
   * Delete an auth identity
   */
  async deleteIdentity(identityId: string): Promise<void> {
    await api.delete(`/identities/${identityId}`)
  },

  /**
   * Get list of available authentication providers
   */
  async getAvailableProviders(): Promise<AuthProvider[]> {
    const response = await api.get<{ providers: AuthProvider[] }>('/identities/providers')
    return response.data.providers
  }
}
