import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('rc_token') || null)
  const user  = ref(JSON.parse(localStorage.getItem('rc_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const role       = computed(() => user.value?.role || null)

  async function login(username, password) {
    const params = new URLSearchParams({ username, password })
    const { data } = await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    token.value = data.access_token
    localStorage.setItem('rc_token', data.access_token)

    // Benutzerdaten aus Token dekodieren (payload ist base64)
    const payload = JSON.parse(atob(data.access_token.split('.')[1]))
    user.value = { id: payload.sub, role: payload.role }
    localStorage.setItem('rc_user', JSON.stringify(user.value))
  }

  function logout() {
    token.value = null
    user.value  = null
    localStorage.removeItem('rc_token')
    localStorage.removeItem('rc_user')
  }

  return { token, user, isLoggedIn, role, login, logout }
})
