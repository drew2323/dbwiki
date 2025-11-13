/**
 * TypeScript types for the Admin/User Management section
 */

export interface User {
  id: string
  email: string
  username: string
  name?: string
  picture?: string
  is_active: boolean
  is_verified: boolean
  default_tenant_id: string
  created_at: string
  updated_at?: string
  last_login?: string
}

export interface AuthIdentity {
  id: string
  user_id: string
  provider: 'password' | 'google' | 'github' | 'oidc' | string
  provider_subject: string
  provider_metadata: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface AuthProvider {
  name: string
  label: string
  icon: string
  description: string
}

export interface Role {
  id: string
  name: string
  tenant_id: string
  permissions: Record<string, boolean | any>
  created_at: string
}

export interface Tenant {
  id: string
  name: string
  subdomain?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface UserTenantRole {
  id: string
  user_id: string
  tenant_id: string
  role_id: string
  is_active: boolean
  created_at: string
  expires_at?: string
  // Populated relationships
  user?: User
  tenant?: Tenant
  role?: Role
}

// Request/Update types
export interface CreateUser {
  email: string
  username: string
  name?: string
  default_tenant_id: string
}

export interface UpdateUser {
  email?: string
  username?: string
  name?: string
  picture?: string
}

export interface CreateAuthIdentity {
  provider: string
  provider_subject: string
  metadata?: Record<string, any>
}

export interface UpdateAuthIdentity {
  metadata: Record<string, any>
}

export interface CreateRole {
  name: string
  tenant_id: string
  permissions?: Record<string, boolean | any>
}

export interface UpdateRole {
  name?: string
  permissions?: Record<string, boolean | any>
}

export interface CreateTenant {
  name: string
  subdomain?: string
}

export interface UpdateTenant {
  name?: string
  subdomain?: string
  is_active?: boolean
}

export interface CreateUserTenantRole {
  user_id: string
  tenant_id: string
  role_id: string
  expires_at?: string
}

export interface UpdateUserTenantRole {
  role_id: string
}

// Display/Enhanced types
export interface UserWithDetails extends User {
  auth_identities?: AuthIdentity[]
  tenant_roles?: UserTenantRole[]
}

export interface TenantWithUserCount extends Tenant {
  user_count?: number
}

export interface UserTenantRoleDisplay extends UserTenantRole {
  user_name?: string
  user_email?: string
  tenant_name?: string
  role_name?: string
}
