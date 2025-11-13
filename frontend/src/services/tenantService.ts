import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || '/api/tenants'

export interface Tenant {
  id: string
  name: string
  subdomain: string | null
  is_active: boolean
}

export interface Role {
  id: string
  name: string
  permissions: Record<string, boolean>
}

export interface UserTenantAccess {
  tenant: Tenant
  role: Role
  is_active: boolean
  created_at: string
  expires_at: string | null
}

export const tenantService = {
  /**
   * Get all tenants the current user has access to
   */
  getMyTenants: async (): Promise<UserTenantAccess[]> => {
    const response = await axios.get(`${API_URL}/me`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get current user's role in a specific tenant
   */
  getMyRoleInTenant: async (tenantId: string): Promise<Role> => {
    const response = await axios.get(`${API_URL}/${tenantId}/role`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get current user's permissions in a specific tenant
   */
  getMyPermissionsInTenant: async (tenantId: string): Promise<Record<string, boolean>> => {
    const response = await axios.get(`${API_URL}/${tenantId}/permissions`, {
      withCredentials: true
    })
    return response.data.permissions
  },

  /**
   * Get all users who have access to a specific tenant
   */
  getTenantUsers: async (tenantId: string, includeInactive: boolean = false) => {
    const response = await axios.get(`${API_URL}/${tenantId}/users`, {
      params: { include_inactive: includeInactive },
      withCredentials: true
    })
    return response.data
  },

  /**
   * Add a user to a tenant with a specific role (admin only)
   */
  addUserToTenant: async (
    userId: string,
    tenantId: string,
    roleId: string,
    expiresAt?: string
  ) => {
    const response = await axios.post(
      `${API_URL}/users/${userId}/tenants`,
      { tenant_id: tenantId, role_id: roleId, expires_at: expiresAt },
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Update a user's role in a tenant (admin only)
   */
  updateUserRoleInTenant: async (
    userId: string,
    tenantId: string,
    roleId: string
  ) => {
    const response = await axios.put(
      `${API_URL}/users/${userId}/tenants/${tenantId}/role`,
      { role_id: roleId },
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Remove a user's access to a tenant (admin only)
   */
  removeUserFromTenant: async (userId: string, tenantId: string) => {
    const response = await axios.delete(
      `${API_URL}/users/${userId}/tenants/${tenantId}`,
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Deactivate a user in a tenant (admin only)
   */
  deactivateUserInTenant: async (userId: string, tenantId: string) => {
    const response = await axios.post(
      `${API_URL}/users/${userId}/tenants/${tenantId}/deactivate`,
      {},
      { withCredentials: true }
    )
    return response.data
  },

  // Tenant CRUD operations
  /**
   * Get all tenants in the system
   */
  getAllTenants: async (skip: number = 0, limit: number = 100): Promise<Tenant[]> => {
    const response = await axios.get(`${API_URL}`, {
      params: { skip, limit },
      withCredentials: true
    })
    return response.data
  },

  /**
   * Get a specific tenant by ID
   */
  getTenantById: async (tenantId: string): Promise<Tenant> => {
    const response = await axios.get(`${API_URL}/${tenantId}`, {
      withCredentials: true
    })
    return response.data
  },

  /**
   * Create a new tenant
   */
  createTenant: async (name: string, subdomain?: string): Promise<Tenant> => {
    const response = await axios.post(
      `${API_URL}`,
      { name, subdomain },
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Update a tenant
   */
  updateTenant: async (
    tenantId: string,
    data: { name?: string; subdomain?: string; is_active?: boolean }
  ): Promise<Tenant> => {
    const response = await axios.put(
      `${API_URL}/${tenantId}`,
      data,
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Deactivate a tenant
   */
  deactivateTenant: async (tenantId: string) => {
    const response = await axios.post(
      `${API_URL}/${tenantId}/deactivate`,
      {},
      { withCredentials: true }
    )
    return response.data
  },

  /**
   * Activate a tenant
   */
  activateTenant: async (tenantId: string) => {
    const response = await axios.post(
      `${API_URL}/${tenantId}/activate`,
      {},
      { withCredentials: true }
    )
    return response.data
  }
}
