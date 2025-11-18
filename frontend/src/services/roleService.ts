/**
 * Role Service
 * Handles API calls for global role CRUD operations.
 * Roles are global entities (superuser, admin, edit, read) that can be assigned to users in different spaces.
 */
import { api } from './api'
import type { Role, CreateRole, UpdateRole } from '@/types/admin'

export const roleService = {
  /**
   * Get all global roles
   */
  async getRoles(): Promise<Role[]> {
    const response = await api.get<Role[]>('/roles')
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
