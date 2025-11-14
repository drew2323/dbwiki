/**
 * User Management Service
 * Handles API calls for user CRUD operations
 */
import { api } from './api'
import type { User, UpdateUser } from '@/types/admin'

export interface UsersQueryParams {
  tenant_id?: string
  skip?: number
  limit?: number
  search?: string
}

export const userService = {
  /**
   * Get all users with optional filtering
   */
  async getUsers(params?: UsersQueryParams): Promise<User[]> {
    const response = await api.get<User[]>('/users', { params })
    return response.data
  },

  /**
   * Get a single user by ID
   */
  async getUserById(userId: string): Promise<User> {
    const response = await api.get<User>(`/users/${userId}`)
    return response.data
  },

  /**
   * Update user details
   */
  async updateUser(userId: string, data: UpdateUser): Promise<User> {
    const response = await api.put<User>(`/users/${userId}`, data)
    return response.data
  },

  /**
   * Activate a user account
   */
  async activateUser(userId: string): Promise<void> {
    await api.post(`/users/${userId}/activate`)
  },

  /**
   * Deactivate a user account
   */
  async deactivateUser(userId: string): Promise<void> {
    await api.post(`/users/${userId}/deactivate`)
  },

  /**
   * Permanently delete a user and all associated data (CASCADE delete)
   * Note: This is a destructive operation and cannot be undone
   */
  async deleteUser(userId: string): Promise<void> {
    await api.delete(`/users/${userId}`)
  }
}
