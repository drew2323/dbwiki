export interface User {
  id: string
  email: string
  username: string
  name: string
  picture?: string
  google_id?: string
  is_active: boolean
  is_verified: boolean
  default_tenant_id: string
  created_at: string
  last_login?: string
}
