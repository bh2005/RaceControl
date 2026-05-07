import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      include: ['src/**/*.{js,vue}'],
      exclude: [
        'src/main.js',
        'src/router/**',
        // Views sind App-Level-Komponenten → gehören in E2E-Tests (Cypress/Playwright)
        'src/views/**',
        'src/App.vue',
        // Navigation-Shell: Router + Auth-Store abhängig, Integration-Bereich
        'src/components/AppHeader.vue',
        // Komplexe HTML-Generatoren → E2E-Bereich
        'src/utils/printNennung.js',
        'src/utils/printSchiedsrichter.js',
      ],
      thresholds: {
        statements: 60,
        branches:   60,
        functions:  60,
        lines:      60,
      },
    },
  },
})
