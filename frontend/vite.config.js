import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,svg,png,ico,woff2}'],
        runtimeCaching: [
          {
            // Public event + standings endpoints — serve cached copy when offline
            urlPattern: /\/api\/public\//,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'public-api',
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 10, maxAgeSeconds: 3600 },
            },
          },
          {
            urlPattern: /\/api\/events\/\d+\/standings/,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'standings-api',
              networkTimeoutSeconds: 5,
              expiration: { maxEntries: 20, maxAgeSeconds: 3600 },
            },
          },
        ],
      },
      manifest: {
        name: 'RaceControl Pro',
        short_name: 'RaceControl',
        description: 'Kart-Slalom Livetiming – MSC Braach e.V. im ADAC',
        theme_color: '#1a3fa0',
        background_color: '#030712',
        display: 'standalone',
        start_url: '/',
        icons: [
          {
            src: '/msc-logo.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any maskable',
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // no rewrite — /api prefix is now part of the FastAPI routes
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
