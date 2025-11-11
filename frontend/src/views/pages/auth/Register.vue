<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()

const email = ref('')
const username = ref('')
const name = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errorMessage = ref('')
const errors = ref<Record<string, string>>({})

const validateForm = () => {
  errors.value = {}
  let isValid = true

  if (!email.value) {
    errors.value.email = 'Email is required'
    isValid = false
  } else if (!/\S+@\S+\.\S+/.test(email.value)) {
    errors.value.email = 'Email is invalid'
    isValid = false
  }

  if (!username.value) {
    errors.value.username = 'Username is required'
    isValid = false
  } else if (username.value.length < 3) {
    errors.value.username = 'Username must be at least 3 characters'
    isValid = false
  }

  if (!password.value) {
    errors.value.password = 'Password is required'
    isValid = false
  } else if (password.value.length < 8) {
    errors.value.password = 'Password must be at least 8 characters'
    isValid = false
  }

  if (password.value !== confirmPassword.value) {
    errors.value.confirmPassword = 'Passwords do not match'
    isValid = false
  }

  return isValid
}

const handleRegister = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    await authStore.register({
      email: email.value,
      username: username.value,
      password: password.value,
      name: name.value || undefined
    })

    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: 'Account created successfully! Please check your email to verify your account.',
      life: 5000
    })

    router.push('/auth/login')
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Registration failed. Please try again.'
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: errorMessage.value,
      life: 5000
    })
  } finally {
    loading.value = false
  }
}

const handleGoogleSignup = () => {
  authStore.login()
}
</script>

<template>
    <div class="min-h-screen bg-surface-50 dark:bg-surface-950 flex">
        <!-- Left Side - Form -->
        <div class="flex-1 flex items-center justify-center p-8">
            <div class="w-full max-w-md">
                <!-- Logo -->
                <div class="flex items-center mb-12">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 mr-2">
                        <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor"/>
                        <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span class="text-xl font-bold text-surface-900 dark:text-surface-0">DIAMOND</span>
                </div>

                <!-- Form -->
                <div class="space-y-6">
                    <div>
                        <h1 class="text-3xl font-bold text-surface-900 dark:text-surface-0 mb-2">Register</h1>
                        <p class="text-surface-600 dark:text-surface-400">Let's get started</p>
                    </div>

                    <!-- Social Register Buttons -->
                    <div class="space-y-3">
                        <Button
                            class="w-full h-12 bg-surface-0 dark:bg-surface-900 border border-surface-300 dark:border-surface-600 text-surface-900 dark:text-surface-0 hover:bg-surface-50 dark:hover:bg-surface-800"
                            outlined
                            @click="handleGoogleSignup"
                        >
                            <svg class="w-5 h-5 mr-3" viewBox="0 0 24 24">
                                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                            </svg>
                            Register with Google
                        </Button>
                    </div>

                    <div class="relative">
                        <div class="absolute inset-0 flex items-center">
                            <div class="w-full border-t border-surface-300 dark:border-surface-600"></div>
                        </div>
                        <div class="relative flex justify-center text-sm">
                            <span class="px-2 bg-surface-50 dark:bg-surface-950 text-surface-500 dark:text-surface-400">or</span>
                        </div>
                    </div>

                    <!-- Registration Form -->
                    <form @submit.prevent="handleRegister" class="space-y-4">
                        <div>
                            <label for="email" class="block text-sm font-medium text-surface-900 dark:text-surface-0 mb-2">Email</label>
                            <InputText
                                id="email"
                                v-model="email"
                                type="email"
                                placeholder="Enter your email"
                                class="w-full h-12"
                                fluid
                                :invalid="!!errors.email"
                            />
                            <small v-if="errors.email" class="text-red-500">{{ errors.email }}</small>
                        </div>

                        <div>
                            <label for="username" class="block text-sm font-medium text-surface-900 dark:text-surface-0 mb-2">Username</label>
                            <InputText
                                id="username"
                                v-model="username"
                                type="text"
                                placeholder="Enter your username"
                                class="w-full h-12"
                                fluid
                                :invalid="!!errors.username"
                            />
                            <small v-if="errors.username" class="text-red-500">{{ errors.username }}</small>
                        </div>

                        <div>
                            <label for="name" class="block text-sm font-medium text-surface-900 dark:text-surface-0 mb-2">Full Name (Optional)</label>
                            <InputText
                                id="name"
                                v-model="name"
                                type="text"
                                placeholder="Enter your full name"
                                class="w-full h-12"
                                fluid
                            />
                        </div>

                        <div>
                            <label for="password" class="block text-sm font-medium text-surface-900 dark:text-surface-0 mb-2">Password</label>
                            <Password
                                id="password"
                                v-model="password"
                                placeholder="Create a password"
                                :toggleMask="true"
                                class="w-full"
                                fluid
                                :feedback="true"
                                inputClass="h-12"
                                :invalid="!!errors.password"
                            />
                            <small v-if="errors.password" class="text-red-500">{{ errors.password }}</small>
                        </div>

                        <div>
                            <label for="confirmPassword" class="block text-sm font-medium text-surface-900 dark:text-surface-0 mb-2">Confirm Password</label>
                            <Password
                                id="confirmPassword"
                                v-model="confirmPassword"
                                placeholder="Confirm your password"
                                :toggleMask="true"
                                class="w-full"
                                fluid
                                :feedback="false"
                                inputClass="h-12"
                                :invalid="!!errors.confirmPassword"
                            />
                            <small v-if="errors.confirmPassword" class="text-red-500">{{ errors.confirmPassword }}</small>
                        </div>

                        <Message v-if="errorMessage" severity="error" :closable="false">{{ errorMessage }}</Message>

                        <Button type="submit" label="Register" class="w-full h-12" :loading="loading" />

                        <div class="text-center text-sm text-surface-600 dark:text-surface-400">
                            Already have an account?
                            <router-link to="/auth/login" class="text-primary hover:underline">Login</router-link>
                        </div>
                    </form>
                </div>

                <!-- Footer -->
                <div class="mt-12 text-center text-xs text-surface-500 dark:text-surface-400">
                    ©2025 PrimeTek
                </div>
            </div>
        </div>

        <!-- Right Side - Illustration -->
        <div class="hidden lg:flex flex-1 bg-blue-50 dark:bg-blue-900/20 items-center justify-center p-8">
            <div class="relative max-w-lg">
                <!-- Cloud illustration -->
                <div class="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-4">
                    <svg width="200" height="120" viewBox="0 0 200 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M60 80C40 80 25 65 25 45C25 25 40 10 60 10C70 10 78 15 82 22C87 20 93 20 98 22C110 25 120 35 120 47C135 47 147 59 147 74C147 89 135 101 120 101H60C40 101 25 86 25 66C25 46 40 31 60 31Z" fill="#3B82F6" opacity="0.8"/>
                        <path d="M140 70C125 70 113 58 113 43C113 28 125 16 140 16C148 16 155 20 158 25C162 24 167 24 171 25C180 27 187 35 187 45C198 45 207 54 207 65C207 76 198 85 187 85H140C125 85 113 73 113 58C113 43 125 31 140 31Z" fill="#60A5FA" opacity="0.9"/>
                        <!-- Arrows -->
                        <path d="M90 40L95 35L90 30" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M90 35L80 35" stroke="#6B7280" stroke-width="2" stroke-linecap="round"/>
                        <path d="M130 70L135 65L130 60" stroke="#6B7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        <path d="M130 65L120 65" stroke="#6B7280" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                </div>

                <!-- Person illustration -->
                <div class="relative z-10 flex items-center justify-center">
                    <svg width="300" height="400" viewBox="0 0 300 400" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <!-- Person -->
                        <ellipse cx="150" cy="390" rx="60" ry="8" fill="#E5E7EB" opacity="0.3"/>
                        <!-- Body -->
                        <rect x="130" y="180" width="40" height="80" rx="20" fill="#3B82F6"/>
                        <!-- Head -->
                        <circle cx="150" cy="120" r="25" fill="#F3E8D0"/>
                        <!-- Hair -->
                        <path d="M125 105C125 85 140 70 150 70C160 70 175 85 175 105C175 95 170 85 160 85C155 85 150 90 150 95C150 90 145 85 140 85C130 85 125 95 125 105Z" fill="#1F2937"/>
                        <!-- Laptop -->
                        <rect x="120" y="150" width="60" height="35" rx="3" fill="#1F2937"/>
                        <rect x="125" y="155" width="50" height="25" rx="2" fill="#374151"/>
                        <!-- Arms -->
                        <rect x="115" y="165" width="15" height="30" rx="7" fill="#F3E8D0"/>
                        <rect x="170" y="165" width="15" height="30" rx="7" fill="#F3E8D0"/>
                        <!-- Legs -->
                        <rect x="135" y="260" width="12" height="120" rx="6" fill="#1F2937"/>
                        <rect x="153" y="260" width="12" height="120" rx="6" fill="#1F2937"/>
                        <!-- Feet -->
                        <ellipse cx="141" cy="385" rx="10" ry="5" fill="#1F2937"/>
                        <ellipse cx="159" cy="385" rx="10" ry="5" fill="#1F2937"/>
                    </svg>
                </div>

                <!-- Server racks -->
                <div class="absolute right-0 top-16">
                    <svg width="120" height="280" viewBox="0 0 120 280" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <!-- Server stack -->
                        <rect x="10" y="20" width="100" height="40" rx="4" fill="#6B7280"/>
                        <rect x="15" y="25" width="90" height="30" rx="2" fill="#374151"/>
                        <circle cx="25" cy="35" r="3" fill="#10B981"/>
                        <circle cx="35" cy="35" r="3" fill="#3B82F6"/>
                        <rect x="45" y="30" width="50" height="10" rx="1" fill="#4B5563"/>
                        
                        <rect x="10" y="70" width="100" height="40" rx="4" fill="#6B7280"/>
                        <rect x="15" y="75" width="90" height="30" rx="2" fill="#374151"/>
                        <circle cx="25" cy="85" r="3" fill="#10B981"/>
                        <circle cx="35" cy="85" r="3" fill="#3B82F6"/>
                        <rect x="45" y="80" width="50" height="10" rx="1" fill="#4B5563"/>
                        
                        <rect x="10" y="120" width="100" height="40" rx="4" fill="#6B7280"/>
                        <rect x="15" y="125" width="90" height="30" rx="2" fill="#374151"/>
                        <circle cx="25" cy="135" r="3" fill="#10B981"/>
                        <circle cx="35" cy="135" r="3" fill="#3B82F6"/>
                        <rect x="45" y="130" width="50" height="10" rx="1" fill="#4B5563"/>
                        
                        <rect x="10" y="170" width="100" height="40" rx="4" fill="#6B7280"/>
                        <rect x="15" y="175" width="90" height="30" rx="2" fill="#374151"/>
                        <circle cx="25" cy="185" r="3" fill="#10B981"/>
                        <circle cx="35" cy="185" r="3" fill="#3B82F6"/>
                        <rect x="45" y="180" width="50" height="10" rx="1" fill="#4B5563"/>
                        
                        <rect x="10" y="220" width="100" height="40" rx="4" fill="#6B7280"/>
                        <rect x="15" y="225" width="90" height="30" rx="2" fill="#374151"/>
                        <circle cx="25" cy="235" r="3" fill="#10B981"/>
                        <circle cx="35" cy="235" r="3" fill="#3B82F6"/>
                        <rect x="45" y="230" width="50" height="10" rx="1" fill="#4B5563"/>
                    </svg>
                </div>

                <!-- Plant decoration -->
                <div class="absolute bottom-0 left-0">
                    <svg width="80" height="120" viewBox="0 0 80 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <!-- Pot -->
                        <path d="M20 100L60 100L55 120L25 120Z" fill="#8B5CF6"/>
                        <!-- Plant -->
                        <path d="M40 100C40 100 35 90 30 80C25 70 20 60 25 50C30 40 40 45 40 50C40 45 50 40 55 50C60 60 55 70 50 80C45 90 40 100 40 100Z" fill="#10B981"/>
                        <path d="M40 100C40 100 45 85 50 75C55 65 60 55 55 45C50 35 40 40 40 45C40 40 30 35 25 45C20 55 25 65 30 75C35 85 40 100 40 100Z" fill="#059669"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* Custom styles for better visual hierarchy */
.pi-eye,
.pi-eye-slash {
    transform: scale(1.6);
    margin-right: 1rem;
}
</style>