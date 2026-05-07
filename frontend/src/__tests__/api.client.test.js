import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Wir testen die Interceptor-Logik, indem wir die Handler direkt aufrufen.
// Das vermeidet echte HTTP-Requests.

describe('api/client.js interceptors', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('Request-Interceptor fügt Authorization-Header hinzu wenn Token vorhanden', async () => {
    localStorage.setItem('rc_token', 'test-token-123')
    // Fresh import to pick up the module state
    const { default: api } = await import('../api/client.js')

    // Access the registered request interceptor handler
    const handler = api.interceptors.request.handlers[0]?.fulfilled
    const config = { headers: {} }
    const result = handler(config)

    expect(result.headers.Authorization).toBe('Bearer test-token-123')
  })

  it('Request-Interceptor setzt keinen Header wenn kein Token', async () => {
    localStorage.removeItem('rc_token')
    const { default: api } = await import('../api/client.js')

    const handler = api.interceptors.request.handlers[0]?.fulfilled
    const config = { headers: {} }
    const result = handler(config)

    expect(result.headers.Authorization).toBeUndefined()
  })

  it('Response-Interceptor gibt Erfolgsantworten unverändert zurück', async () => {
    const { default: api } = await import('../api/client.js')
    const successHandler = api.interceptors.response.handlers[0]?.fulfilled
    const fakeResponse = { status: 200, data: { ok: true } }
    expect(successHandler(fakeResponse)).toBe(fakeResponse)
  })

  it('Response-Interceptor löscht Token bei 401 und leitet weiter', async () => {
    localStorage.setItem('rc_token', 'expired-token')
    const { default: api } = await import('../api/client.js')

    const errorHandler = api.interceptors.response.handlers[0]?.rejected
    const locationSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
      href: '',
    })
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true,
    })

    const err = { response: { status: 401 } }
    await expect(errorHandler(err)).rejects.toEqual(err)

    expect(localStorage.getItem('rc_token')).toBeNull()
    expect(window.location.href).toBe('/login')
  })

  it('Response-Interceptor rejectet Nicht-401-Fehler ohne redirect', async () => {
    const { default: api } = await import('../api/client.js')
    const errorHandler = api.interceptors.response.handlers[0]?.rejected

    const err = { response: { status: 500 } }
    await expect(errorHandler(err)).rejects.toEqual(err)
  })

  it('API-Basisurl ist /api', async () => {
    const { default: api } = await import('../api/client.js')
    expect(api.defaults.baseURL).toBe('/api')
  })
})
