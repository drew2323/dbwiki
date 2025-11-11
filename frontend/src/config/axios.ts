import axios from 'axios'
import { useTenantStore } from '@/stores/tenantStore'

// Add request interceptor to include tenant context
axios.interceptors.request.use(
  (config) => {
    // Add tenant ID to headers if available
    const tenantStore = useTenantStore()
    if (tenantStore.currentTenantId) {
      config.headers['X-Tenant-Id'] = tenantStore.currentTenantId
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default axios
