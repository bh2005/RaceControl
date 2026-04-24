import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createApp, nextTick } from 'vue'
import { useRealtimeUpdate } from '../composables/useRealtimeUpdate'

class MockWebSocket {
  static instances = []
  static reset() { MockWebSocket.instances = [] }

  constructor(url) {
    this.url = url
    this.readyState = 0
    MockWebSocket.instances.push(this)
  }

  close() {
    if (this.onclose) this.onclose({ code: 1000 })
  }

  simulateOpen() {
    this.readyState = 1
    if (this.onopen) this.onopen()
  }

  simulateMessage(data) {
    if (this.onmessage) this.onmessage({ data: JSON.stringify(data) })
  }

  simulateError() {
    if (this.onerror) this.onerror()
  }
}

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

describe('useRealtimeUpdate', () => {
  beforeEach(() => {
    MockWebSocket.reset()
    vi.stubGlobal('WebSocket', MockWebSocket)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('creates a WebSocket on mount', () => {
    const { app } = withSetup(() => useRealtimeUpdate(() => {}))
    expect(MockWebSocket.instances).toHaveLength(1)
    app.unmount()
  })

  it('returns connected ref starting as false', () => {
    const { result, app } = withSetup(() => useRealtimeUpdate(() => {}))
    expect(result.connected.value).toBe(false)
    app.unmount()
  })

  it('sets connected = true on open', async () => {
    const { result, app } = withSetup(() => useRealtimeUpdate(() => {}))
    MockWebSocket.instances[0].simulateOpen()
    await nextTick()
    expect(result.connected.value).toBe(true)
    app.unmount()
  })

  it('calls onMessage with parsed JSON data', () => {
    const onMessage = vi.fn()
    const { app } = withSetup(() => useRealtimeUpdate(onMessage))

    MockWebSocket.instances[0].simulateMessage({ type: 'results', event_id: 1 })

    expect(onMessage).toHaveBeenCalledOnce()
    expect(onMessage).toHaveBeenCalledWith({ type: 'results', event_id: 1 })
    app.unmount()
  })

  it('ignores malformed JSON without throwing', () => {
    const onMessage = vi.fn()
    const { app } = withSetup(() => useRealtimeUpdate(onMessage))

    const ws = MockWebSocket.instances[0]
    ws.onmessage?.({ data: 'not-json' })

    expect(onMessage).not.toHaveBeenCalled()
    app.unmount()
  })

  it('sets connected = false on close', async () => {
    const { result, app } = withSetup(() => useRealtimeUpdate(() => {}))
    const ws = MockWebSocket.instances[0]
    ws.simulateOpen()
    await nextTick()

    ws.close()
    await nextTick()

    expect(result.connected.value).toBe(false)
    app.unmount()
  })

  it('closes the WebSocket on unmount', () => {
    const { app } = withSetup(() => useRealtimeUpdate(() => {}))
    const ws = MockWebSocket.instances[0]
    const closeSpy = vi.spyOn(ws, 'close')

    app.unmount()

    expect(closeSpy).toHaveBeenCalled()
  })
})
