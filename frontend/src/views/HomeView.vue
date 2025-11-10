  <!-- Pohrobek - move away -->
<template>
  <div class="home">
    <h1>Welcome to V3Trading</h1>

    <!-- Loading State -->
    <div v-if="authStore.loading" class="loading">Loading...</div>

    <!-- Not Authenticated -->
    <div v-else-if="!authStore.isAuthenticated" class="auth-section">
      <p>Please sign in to continue</p>
      <button @click="authStore.login" class="login-btn">
        <svg width="18" height="18" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
          <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
          <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
          <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
          <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          <path fill="none" d="M0 0h48v48H0z"/>
        </svg>
        Sign in with Google
      </button>
    </div>

    <!-- Authenticated -->
    <div v-else class="user-section">
      <div class="user-info">
        <img v-if="authStore.user?.picture" :src="authStore.user.picture" alt="Profile" class="profile-pic" />
        <div>
          <h2>Hello, {{ authStore.user?.name }}!</h2>
          <p class="email">{{ authStore.user?.email }}</p>
        </div>
      </div>

      <div class="actions">
        <router-link to="/api-test" class="test-link">
          <button class="primary-btn">Test API Integration</button>
        </router-link>
        <button @click="handleLogout" class="logout-btn">Logout</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

onMounted(async () => {
  await authStore.fetchUser()
})

const handleLogout = async () => {
  await authStore.logout()
  router.push('/')
}
</script>

<style scoped>
.home {
  text-align: center;
  margin-top: 60px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  padding: 20px;
}

.loading {
  font-size: 18px;
  color: #666;
}

.auth-section {
  margin-top: 40px;
}

.auth-section p {
  font-size: 18px;
  margin-bottom: 30px;
  color: #555;
}

.login-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: white;
  color: #444;
  border: 1px solid #ddd;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: box-shadow 0.2s;
}

.login-btn:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.user-section {
  margin-top: 40px;
}

.user-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 30px;
}

.profile-pic {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 3px solid #42b983;
}

.user-info h2 {
  margin: 0;
  color: #2c3e50;
}

.email {
  color: #666;
  font-size: 14px;
  margin: 5px 0 0 0;
}

.actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.primary-btn {
  background: #42b983;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
}

.primary-btn:hover {
  background: #369970;
}

.logout-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 500;
}

.logout-btn:hover {
  background: #d32f2f;
}

.test-link {
  text-decoration: none;
}
</style>
