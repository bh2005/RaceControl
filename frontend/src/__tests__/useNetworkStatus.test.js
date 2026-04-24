import { describe, it, expect, beforeEach } from 'vitest'
import { createApp, nextTick } from 'vue'
import { useNetworkStatus } from '../composables/useNetworkStatus'

function withSetup(composable) {
  let result
  const app = createApp({
    setup() {
      result = composable()
      return () => {}
    },
  })
  app.mount(document.createElement('div'))
  return { result, app }
}

describe('useNetworkStatus', () => {
  beforeEach(() => {
    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true, writable: true })
  })

  it('reflects navigator.onLine = true on mount', () => {
    const { result, app } = withSetup(() => useNetworkStatus())
    expect(result.isOnline.value).toBe(true)
    app.unmount()
  })

  it('reflects navigator.onLine = false on mount', () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true, writable: true })
    const { result, app } = withSetup(() => useNetworkStatus())
    expect(result.isOnline.value).toBe(false)
    app.unmount()
  })

  it('updates to false when offline event fires', async () => {
    const { result, app } = withSetup(() => useNetworkStatus())

    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true, writable: true })
    window.dispatchEvent(new Event('offline'))
    await nextTick()

    expect(result.isOnline.value).toBe(false)
    app.unmount()
  })

  it('updates to true when online event fires', async () => {
    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true, writable: true })
    const { result, app } = withSetup(() => useNetworkStatus())

    Object.defineProperty(navigator, 'onLine', { value: true, configurable: true, writable: true })
    window.dispatchEvent(new Event('online'))
    await nextTick()

    expect(result.isOnline.value).toBe(true)
    app.unmount()
  })

  it('removes event listeners on unmount', async () => {
    const { result, app } = withSetup(() => useNetworkStatus())
    app.unmount()

    Object.defineProperty(navigator, 'onLine', { value: false, configurable: true, writable: true })
    window.dispatchEvent(new Event('offline'))
    await nextTick()

    // After unmount the ref is no longer updated (listener was removed)
    expect(result.isOnline.value).toBe(true)
  })
})
