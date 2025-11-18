import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api/spaces'

export interface Space {
  id: string
  key: string
  name: string
  description?: string
  visibility: 'private' | 'public'
  home_page_id?: string
  created_by: string
  created_at: string
  updated_at?: string
}

export interface Role {
  id: string
  name: string
  permissions: Record<string, boolean>
}

export interface UserSpaceAccess {
  space: Space
  role: Role
  is_active: boolean
  created_at: string
  expires_at: string | null
}

export const spaceService = {
  /**
   * Get all spaces the current user has access to
   */
  getMySpaces: async (): Promise<UserSpaceAccess[]> => {
    const response = await axios.get(`${API_URL}/me`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get current user's role in a specific space
   */
  getMyRoleInSpace: async (spaceId: string): Promise<Role> => {
    const response = await axios.get(`${API_URL}/${spaceId}/role`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get current user's permissions in a specific space
   */
  getMyPermissionsInSpace: async (spaceId: string): Promise<Record<string, boolean>> => {
    const response = await axios.get(`${API_URL}/${spaceId}/permissions`, {
      withCredentials: true
    })
    return response.data.permissions
  },

  /**
   * Get all users who have access to a specific space
   */
  getSpaceUsers: async (spaceId: string, includeInactive: boolean = false) => {
    const response = await axios.get(`${API_URL}/${spaceId}/users`, {
      params: { include_inactive: includeInactive },
      withCredentials: true
    })
    return response.data
  },

  /**
   * Add a user to a space with a specific role (admin only)
   */
  addUserToSpace: async (
    userId: string,
    spaceId: string,
    roleId: string,
    expiresAt?: string
  ) => {
    const response = await axios.post(
      `${API_URL}/users/${userId}/spaces`,
      { space_id: spaceId, role_id: roleId, expires_at: expiresAt },
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Update a user's role in a space (admin only)
   */
  updateUserRoleInSpace: async (
    userId: string,
    spaceId: string,
    roleId: string
  ) => {
    const response = await axios.put(
      `${API_URL}/users/${userId}/spaces/${spaceId}/role`,
      { role_id: roleId },
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Remove a user's access to a space (admin only)
   */
  removeUserFromSpace: async (userId: string, spaceId: string) => {
    const response = await axios.delete(
      `${API_URL}/users/${userId}/spaces/${spaceId}`,
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Deactivate a user in a space (admin only)
   */
  deactivateUserInSpace: async (userId: string, spaceId: string) => {
    const response = await axios.post(
      `${API_URL}/users/${userId}/spaces/${spaceId}/deactivate`,
      {},
      { withCredentials: true }
    )
    return response.data
  },

  // Space CRUD operations
  /**
   * Get all spaces in the system
   * For superusers: Returns all spaces.
   * For regular users: Returns only spaces they are members of.
   */
  getAllSpaces: async (skip: number = 0, limit: number = 100): Promise<Space[]> => {
    const response = await axios.get(`${API_URL}`, {
      params: { skip, limit },
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get spaces where current user has admin rights
   * For superusers: Returns all spaces (superusers have implicit admin rights).
   * For admins: Returns only spaces where they have the 'admin' role.
   */
  getAdminSpaces: async (): Promise<Space[]> => {
    const response = await axios.get(`${API_URL}/admin/spaces`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get a specific space by ID
   */
  getSpaceById: async (spaceId: string): Promise<Space> => {
    const response = await axios.get(`${API_URL}/${spaceId}`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Create a new space
   */
  createSpace: async (
    key: string,
    name: string,
    description?: string,
    visibility: 'private' | 'public' = 'private'
  ): Promise<Space> => {
    const response = await axios.post(
      `${API_URL}`,
      { key, name, description, visibility },
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Update a space
   */
  updateSpace: async (
    spaceId: string,
    data: {
      key?: string
      name?: string
      description?: string
      visibility?: 'private' | 'public'
      home_page_id?: string
    }
  ): Promise<Space> => {
    const response = await axios.put(
      `${API_URL}/${spaceId}`,
      data,
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Delete a space (hard delete)
   */
  deleteSpace: async (spaceId: string) => {
    const response = await axios.delete(
      `${API_URL}/${spaceId}`,
      { withCredentials: true }
    )
    return response.data
  }
}
