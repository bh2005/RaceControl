import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { useEventStore } from '../stores/event.js'
import StatusBar from '../components/StatusBar.vue'

vi.mock('../api/client.js', () => ({
  default: { get: vi.fn(), post: vi.fn() },
}))

// RouterLink als leerer Stub
const RouterLinkStub = { template: '<a><slot /></a>', props: ['to'] }

function mkWrapper() {
  return mount(StatusBar, {
    global: {
      plugins: [createPinia()],
      components: { RouterLink: RouterLinkStub },
      stubs: { RouterLink: RouterLinkStub },
    },
  })
}

describe('StatusBar', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('rendert ohne Fehler', () => {
    const w = mkWrapper()
    expect(w.find('footer').exists()).toBe(true)
  })

  it('zeigt "Verbunden" wenn online', () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(true)
    const w = mkWrapper()
    expect(w.text()).toContain('Verbunden')
  })

  it('zeigt "Keine Verbindung" wenn offline', () => {
    vi.spyOn(navigator, 'onLine', 'get').mockReturnValue(false)
    const w = mkWrapper()
    expect(w.text()).toContain('Keine Verbindung')
  })

  it('zeigt den Event-Namen wenn activeEvent gesetzt ist', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const store = useEventStore()
    store.activeEvent = { id: 1, name: 'Testlauf 2026', status: 'active' }

    const w = mount(StatusBar, {
      global: {
        plugins: [pinia],
        stubs: { RouterLink: RouterLinkStub },
      },
    })
    expect(w.text()).toContain('Testlauf 2026')
  })

  it('reagiert auf online/offline Events', async () => {
    const w = mkWrapper()
    // Simulate going offline
    Object.defineProperty(navigator, 'onLine', { get: () => false, configurable: true })
    window.dispatchEvent(new Event('offline'))
    await w.vm.$nextTick()
    expect(w.text()).toContain('Keine Verbindung')
    // Simulate going online
    Object.defineProperty(navigator, 'onLine', { get: () => true, configurable: true })
    window.dispatchEvent(new Event('online'))
    await w.vm.$nextTick()
    expect(w.text()).toContain('Verbunden')
  })

  it('zeigt die Versionsnummer', () => {
    const w = mkWrapper()
    // version comes from package.json — just check it renders a semver-like string
    expect(w.text()).toMatch(/\d+\.\d+\.\d+/)
  })

  it('entfernt Event-Listener beim Unmount (kein Fehler)', () => {
    const w = mkWrapper()
    expect(() => w.unmount()).not.toThrow()
  })
})
