import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import App from './App.vue'
import router from './router/index.js'

import Aura from '@primeuix/themes/aura'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import StyleClass from 'primevue/styleclass'

import '@/assets/styles.scss'
import { useLayoutStore } from '@/stores/layoutStore'

const app = createApp(App)

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

app.use(pinia)

// Initialize dark mode class on app load
const layoutStore = useLayoutStore()
layoutStore.applyDarkModeClass()

app.use(router)
app.use(PrimeVue, {
    theme: {
        preset: Aura,
        options: {
            darkModeSelector: '.app-dark'
        }
    }
})
app.use(ToastService)
app.use(ConfirmationService)
app.directive('styleclass', StyleClass)

app.mount('#app')
