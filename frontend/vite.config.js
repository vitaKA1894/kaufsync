import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      includeAssets: ['favicon.svg', 'icons.svg'], // Deine SVGs nehmen
      
      // NEU: Zwingt Vite, die PWA auch im dev-Modus zu testen!
      devOptions: {
        enabled: true
      },
      
      manifest: {
        name: 'KaufSync',
        short_name: 'KaufSync',
        description: 'Private und hochperformante Einkaufsliste',
        theme_color: '#2c3e50',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: '/icons.svg', // Wir nutzen deine existierende SVG!
            sizes: '192x192',
            type: 'image/svg+xml', // Typ auf SVG geändert
            purpose: 'any maskable'
          },
          {
            src: '/icons.svg',
            sizes: '512x512',
            type: 'image/svg+xml',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
		navigateFallback: '/index.html' // NEU: Leitet alle Offline-Requests auf die App um
      }
    })
  ]
})