import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Connects to the backend WebSocket at /ws and calls onMessage(data) on
 * each inbound JSON message. Reconnects automatically on disconnect.
 *
 * @param {(data: object) => void} onMessage  – called with parsed JSON payload
 * @returns {{ connected: Ref<boolean> }}
 */
export function useRealtimeUpdate(onMessage) {
  const connected = ref(false)
  let ws = null
  let reconnectTimer = null
  let active = true

  function connect() {
    if (!active) return
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${proto}//${location.host}/ws`)

    ws.onopen = () => {
      connected.value = true
    }

    ws.onmessage = (e) => {
      try { onMessage(JSON.parse(e.data)) } catch { /* ignore malformed */ }
    }

    ws.onclose = () => {
      connected.value = false
      ws = null
      if (active) reconnectTimer = setTimeout(connect, 2500)
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  onMounted(connect)

  onUnmounted(() => {
    active = false
    clearTimeout(reconnectTimer)
    ws?.close()
  })

  return { connected }
}
