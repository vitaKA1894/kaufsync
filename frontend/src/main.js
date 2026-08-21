import { createApp } from 'vue'
import './style.css'  
import App from './App.vue'
import router from './router' // NEU

const app = createApp(App)
app.use(router) // NEU
app.mount('#app')

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').then(function(registration) {
    console.log('ServiceWorker registration successful with scope: ', registration.scope);
  }, function(err) {
    console.log('ServiceWorker registration failed: ', err);
  });
}