import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/',               component: () => import('../views/GasteView.vue'),           meta: { public: true } },
  { path: '/login',          component: () => import('../views/LoginView.vue'),            meta: { public: true } },
  { path: '/livetiming',     component: () => import('../views/LivetimingView.vue'),       meta: { public: true } },
  { path: '/nennen',         component: () => import('../views/SelbstnennungView.vue'),    meta: { public: true } },
  { path: '/zeitnahme',      component: () => import('../views/ZeitnahmeView.vue'),        meta: { roles: ['admin', 'zeitnahme'] } },
  { path: '/training',       component: () => import('../views/TrainingView.vue'),          meta: { roles: ['admin', 'zeitnahme'] } },
  { path: '/nennung',        component: () => import('../views/NennungView.vue'),          meta: { roles: ['admin', 'nennung'] } },
  { path: '/schiedsrichter', component: () => import('../views/SchiedsrichterView.vue'),   meta: { roles: ['admin', 'schiedsrichter'] } },
  { path: '/admin',          component: () => import('../views/AdminView.vue'),            meta: { roles: ['admin'] } },
  { path: '/lizenz',         component: () => import('../views/LizenzView.vue'),            meta: { public: true } },
  { path: '/speaker',        component: () => import('../views/SpeakerView.vue'),            meta: { public: true } },
  { path: '/nachrichten',   component: () => import('../views/NachrichtenView.vue'),         meta: { roles: ['admin', 'zeitnahme', 'nennung', 'schiedsrichter'] } },
  { path: '/dokumente',     component: () => import('../views/DokumenteView.vue'),            meta: { public: true } },
  { path: '/marshal',       component: () => import('../views/MarshalView.vue'),              meta: { roles: ['marshal', 'admin'] } },
  { path: '/auswertung',   component: () => import('../views/AuswertungView.vue'),            meta: { roles: ['admin', 'schiedsrichter', 'zeitnahme', 'nennung', 'viewer'] } },
]

const roleHome = {
  admin:          '/zeitnahme',
  zeitnahme:      '/zeitnahme',
  nennung:        '/nennung',
  schiedsrichter: '/schiedsrichter',
  marshal:        '/marshal',
  viewer:         '/livetiming',
}

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    // Logged-in staff landing on '/' → send to their home screen
    if (to.path === '/' && auth.isLoggedIn && auth.role !== 'viewer') {
      return roleHome[auth.role] || '/zeitnahme'
    }
    return true
  }
  if (!auth.isLoggedIn) return '/login'
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) {
    return roleHome[auth.role] || '/'
  }
  return true
})

export default router
