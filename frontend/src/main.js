import { createApp } from 'vue'
import './style.css'  
import App from './App.vue'
import router from './router' // NEU

const app = createApp(App)
app.use(router) // NEU
app.mount('#app')