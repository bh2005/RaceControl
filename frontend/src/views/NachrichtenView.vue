<template>
  <div class="max-w-xl mx-auto p-4 pt-6 space-y-4">

    <div class="flex items-center gap-2">
      <span class="text-2xl">📢</span>
      <h1 class="text-xl font-bold text-gray-800">Nachrichten senden</h1>
    </div>
    <p class="text-sm text-gray-500">
      Nachricht wird sofort als Banner auf allen verbundenen Geräten angezeigt
      (Sprecher, Zeitnahme, Livetiming, …)
    </p>

    <!-- Eingabe-Card -->
    <div class="card p-4 space-y-3">
      <textarea
        ref="inputRef"
        v-model="message"
        rows="3"
        maxlength="300"
        placeholder="Nachricht eingeben …"
        class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-msc-blue"
        @keydown.ctrl.enter.prevent="send"
      />
      <div class="flex justify-between text-xs text-gray-400">
        <span>Strg + Enter zum Senden</span>
        <span :class="message.length > 270 ? 'text-orange-500 font-bold' : ''">
          {{ message.length }}/300
        </span>
      </div>

      <!-- Schnell-Nachrichten -->
      <div class="flex flex-wrap gap-2">
        <button
          v-for="q in quickMessages"
          :key="q.text"
          @click="message = q.text; $nextTick(() => inputRef?.focus())"
          class="text-xs px-2 py-1 rounded-full border border-gray-300 bg-gray-50 hover:bg-gray-100 text-gray-700 transition"
        >
          {{ q.icon }} {{ q.text }}
        </button>
      </div>

      <button
        @click="send"
        :disabled="!message.trim() || sending"
        class="btn-primary w-full py-2.5 text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {{ sending ? 'Wird gesendet …' : '📤 An alle senden' }}
      </button>

      <div v-if="errorMsg" class="text-sm text-red-600 font-medium">{{ errorMsg }}</div>
    </div>

    <!-- Verlauf dieser Sitzung -->
    <div v-if="log.length" class="card p-4">
      <h2 class="text-sm font-bold text-gray-600 mb-2">Gesendet (diese Sitzung)</h2>
      <ul class="space-y-1.5">
        <li
          v-for="entry in log"
          :key="entry.id"
          class="flex items-start gap-2 text-sm"
        >
          <span class="text-gray-400 tabnum shrink-0 text-xs pt-0.5">{{ entry.time }}</span>
          <span class="text-gray-800">{{ entry.message }}</span>
          <span class="ml-auto text-green-500 text-xs shrink-0">✓ gesendet</span>
        </li>
      </ul>
    </div>

  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import api from '../api/client'

const message   = ref('')
const sending   = ref(false)
const errorMsg  = ref('')
const log       = ref([])
const inputRef  = ref(null)
let   logId     = 0

const quickMessages = [
  { icon: '🌭', text: 'Bratwurst jetzt am Grill – bitte anstellen!' },
  { icon: '👥', text: 'Alle JL bitte sofort zur Besprechung' },
  { icon: '⏸',  text: 'Kurze Pause – Strecke wird freigemacht' },
  { icon: '🏆', text: 'Siegerehrung beginnt in 10 Minuten' },
  { icon: '🔇', text: 'Bitte Ruhe im Fahrerlager' },
]

async function send() {
  const text = message.value.trim()
  if (!text || sending.value) return
  sending.value  = true
  errorMsg.value = ''
  try {
    await api.post('/notifications', { message: text })
    log.value.unshift({
      id: ++logId,
      time: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      message: text,
    })
    message.value = ''
    await nextTick()
    inputRef.value?.focus()
  } catch (e) {
    errorMsg.value = e.response?.data?.detail ?? 'Fehler beim Senden'
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.tabnum { font-variant-numeric: tabular-nums; }
</style>
