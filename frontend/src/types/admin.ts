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
  permissions: Record<string, boolean | any>
  created_at: string
}

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

export interface UserSpaceRole {
  id: string
  user_id: string
  space_id: string
  role_id: string
  is_active: boolean
  created_at: string
  expires_at?: string
  // Populated relationships
  user?: User
  space?: Space
  role?: Role
}

// Request/Update types
export interface CreateUser {
  email: string
  username: string
  name?: string
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
  permissions?: Record<string, boolean | any>
}

export interface UpdateRole {
  name?: string
  permissions?: Record<string, boolean | any>
}

export interface CreateSpace {
  key: string
  name: string
  description?: string
  visibility?: 'private' | 'public'
}

export interface UpdateSpace {
  key?: string
  name?: string
  description?: string
  visibility?: 'private' | 'public'
  home_page_id?: string
}

export interface CreateUserSpaceRole {
  user_id: string
  space_id: string
  role_id: string
  expires_at?: string
}

export interface UpdateUserSpaceRole {
  role_id: string
}

// Display/Enhanced types
export interface UserWithDetails extends User {
  auth_identities?: AuthIdentity[]
  space_roles?: UserSpaceRole[]
}

export interface SpaceWithUserCount extends Space {
  user_count?: number
}

export interface UserSpaceRoleDisplay extends UserSpaceRole {
  user_name?: string
  user_email?: string
  space_name?: string
  role_name?: string
}
