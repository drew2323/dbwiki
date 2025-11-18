import axios from 'axios'
import { useSpaceStore } from '@/stores/spaceStore'

// Add request interceptor to include space context
axios.interceptors.request.use(
  (config) => {
    // Add space ID to headers if available
    const spaceStore = useSpaceStore()
    if (spaceStore.currentSpaceId) {
      config.headers['X-Space-Id'] = spaceStore.currentSpaceId
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default axios
