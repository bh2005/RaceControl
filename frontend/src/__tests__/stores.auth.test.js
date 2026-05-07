import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '../stores/auth.js'

// Mock des API-Clients — muss vor dem Store-Import gehoisted werden
vi.mock('../api/client.js', () => ({
  default: { post: vi.fn(), get: vi.fn() },
}))

import api from '../api/client.js'

function makeToken(payload) {
  // Minimal-JWT: header.payload.signature (nur payload wird dekodiert)
  return 'eyJhbGciOiJIUzI1NiJ9.' + btoa(JSON.stringify(payload)) + '.sig'
}

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('isLoggedIn ist false wenn kein Token gespeichert', () => {
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(false)
  })

  it('role ist null wenn kein User gespeichert', () => {
    const store = useAuthStore()
    expect(store.role).toBeNull()
  })

  it('liest gespeichertes Token aus localStorage', () => {
    localStorage.setItem('rc_token', 'existing-token')
    localStorage.setItem('rc_user', JSON.stringify({ id: '5', role: 'zeitnahme' }))
    const store = useAuthStore()
    expect(store.isLoggedIn).toBe(true)
    expect(store.role).toBe('zeitnahme')
  })

  it('logout löscht Token und User', () => {
    const store = useAuthStore()
    store.token = 'some-token'
    store.user = { id: '1', role: 'admin' }
    localStorage.setItem('rc_token', 'some-token')
    localStorage.setItem('rc_user', JSON.stringify({ id: '1', role: 'admin' }))

    store.logout()

    expect(store.isLoggedIn).toBe(false)
    expect(store.role).toBeNull()
    expect(localStorage.getItem('rc_token')).toBeNull()
    expect(localStorage.getItem('rc_user')).toBeNull()
  })

  it('login speichert Token und User aus JWT-Payload', async () => {
    const payload = { sub: '42', role: 'admin' }
    const token   = makeToken(payload)
    api.post.mockResolvedValueOnce({ data: { access_token: token } })

    const store = useAuthStore()
    await store.login('admin', 'secret')

    expect(store.token).toBe(token)
    expect(store.isLoggedIn).toBe(true)
    expect(store.role).toBe('admin')
    expect(localStorage.getItem('rc_token')).toBe(token)
    expect(JSON.parse(localStorage.getItem('rc_user'))).toEqual({ id: '42', role: 'admin' })
  })

  it('login sendet korrekte URL-Form-Daten', async () => {
    const token = makeToken({ sub: '1', role: 'viewer' })
    api.post.mockResolvedValueOnce({ data: { access_token: token } })
    const store = useAuthStore()

    await store.login('user', 'pass')

    expect(api.post).toHaveBeenCalledWith(
      '/auth/login',
      expect.any(URLSearchParams),
      expect.objectContaining({ headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
    )
  })
})
