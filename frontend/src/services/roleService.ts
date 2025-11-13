/**
 * Role Service
 * Handles API calls for role CRUD operations
 */
import { api } from './api'
import type { Role, CreateRole, UpdateRole } from '@/types/admin'

export const roleService = {
  /**
   * Get all roles, optionally filtered by tenant
   */
  async getRoles(tenantId?: string): Promise<Role[]> {
    const response = await api.get<Role[]>('/roles', {
      params: tenantId ? { tenant_id: tenantId } : undefined
    })
    return response.data
  },

  /**
   * Get a single role by ID
   */
  async getRoleById(roleId: string): Promise<Role> {
    const response = await api.get<Role>(`/roles/${roleId}`)
    return response.data
  },

  /**
   * Create a new role
   */
  async createRole(data: CreateRole): Promise<Role> {
    const response = await api.post<Role>('/roles', data)
    return response.data
  },

  /**
   * Update an existing role
   */
  async updateRole(roleId: string, data: UpdateRole): Promise<Role> {
    const response = await api.put<Role>(`/roles/${roleId}`, data)
    return response.data
  },

  /**
   * Delete a role
   */
  async deleteRole(roleId: string): Promise<void> {
    await api.delete(`/roles/${roleId}`)
  }
}
