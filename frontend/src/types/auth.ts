export interface User {
  id: string
  email: string
  username: string
  name: string
  picture?: string
  google_id?: string
  is_active: boolean
  is_verified: boolean
  is_superuser: boolean
  created_at: string
  last_login?: string
}
