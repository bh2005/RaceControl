<template>
  <div class="min-h-screen bg-gray-950 text-white flex flex-col">

    <!-- Header -->
    <div class="bg-msc-blue px-4 py-3 flex items-center justify-between shadow-lg">
      <div>
        <div class="text-xs text-blue-200 font-semibold uppercase tracking-widest">Streckenposten</div>
        <div v-if="!editStation" class="font-black text-xl leading-tight cursor-pointer" @click="startEditStation">
          {{ station }} <span class="text-blue-300 text-sm font-normal ml-1">✎</span>
        </div>
        <input
          v-else
          v-model="station"
          @blur="saveStation"
          @keydown.enter="saveStation"
          class="bg-white/20 rounded px-2 py-0.5 text-white font-black text-xl w-48 outline-none"
          ref="stationInput"
        >
      </div>
      <div class="text-right text-xs text-blue-300">
        {{ store.activeEvent?.name || '–' }}
      </div>
    </div>

    <!-- Sent flash -->
    <Transition name="slide-down">
      <div v-if="sentFlash" class="bg-green-600 text-white text-center font-black py-4 text-2xl tracking-wide">
        ✓ {{ sentFlash }} Punkte gesendet
      </div>
    </Transition>

    <!-- Error banner -->
    <Transition name="slide-down">
      <div v-if="errorMsg" class="bg-red-600 text-white text-center font-bold py-3 text-base px-4">
        ⚠ {{ errorMsg }}
      </div>
    </Transition>

    <!-- Eingabe -->
    <div class="flex-1 flex flex-col items-center justify-center px-8 gap-6">

      <div class="text-gray-400 text-sm font-semibold uppercase tracking-widest">Fehlerpunkte (Sekunden)</div>

      <input
        ref="pointsInput"
        v-model="points"
        type="number"
        inputmode="numeric"
        min="1"
        placeholder="0"
        class="w-52 text-center bg-gray-800 border-2 rounded-2xl px-6 py-4 text-8xl font-black tabnum focus:outline-none focus:ring-4 focus:ring-msc-blue focus:border-msc-blue border-gray-600 text-white"
        @keydown.enter="send"
      >

      <button
        @click="send"
        :disabled="!canSend"
        class="w-52 py-5 rounded-2xl font-black text-2xl transition active:scale-95 disabled:opacity-40"
        :class="canSend
          ? 'bg-msc-blue hover:bg-msc-bluedark text-white shadow-lg shadow-blue-900/50'
          : 'bg-gray-700 text-gray-500'"
      >
        📤 Senden
      </button>

    </div>

    <!-- History der letzten 3 Meldungen -->
    <div v-if="history.length" class="bg-gray-900 px-4 py-3 space-y-2">
      <div class="text-xs text-gray-500 font-semibold uppercase tracking-widest mb-2">
        Letzte Meldungen
      </div>
      <TransitionGroup name="history-list" tag="div" class="space-y-2">
        <div
          v-for="entry in historyVisible"
          :key="entry.ts"
          class="flex items-center gap-3 rounded-xl px-3 py-2 border transition-all"
          :class="entry.cancelled
            ? 'bg-gray-800/40 border-gray-700 opacity-50'
            : 'bg-gray-800 border-gray-700'"
        >
          <span class="text-gray-500 font-mono text-xs w-16 shrink-0">{{ entry.time }}</span>
          <span
            class="font-black tabnum text-lg"
            :class="entry.cancelled ? 'line-through text-gray-500' : 'text-yellow-400'"
          >{{ entry.points }} Pkt</span>
          <span class="text-gray-500 text-xs flex-1">{{ entry.station }}</span>
          <button
            v-if="!entry.cancelled"
            @click="storno(entry)"
            :disabled="entry.cancelling"
            class="text-xs font-bold rounded-lg px-3 py-1.5 transition active:scale-95 disabled:opacity-40"
            :class="entry.cancelling
              ? 'bg-gray-700 text-gray-500'
              : 'bg-red-900/80 hover:bg-red-800 text-red-300 border border-red-700'"
          >
            {{ entry.cancelling ? '…' : '✕ Storno' }}
          </button>
          <span v-else class="text-xs text-gray-600 font-semibold">Storniert</span>
        </div>
      </TransitionGroup>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'

const store = useEventStore()

const station      = ref(localStorage.getItem('marshal_station') || 'Posten 1')
const editStation  = ref(false)
const stationInput = ref(null)
const pointsInput  = ref(null)
const points       = ref('')
const sending      = ref(false)
const sentFlash    = ref(null)
const errorMsg     = ref(null)
let sentTimer      = null
let errTimer       = null
const history      = ref([])  // { ts, time, points, station, cancelled, cancelling }

const historyVisible = computed(() => [...history.value].reverse().slice(0, 3))
const canSend = computed(() => !sending.value && Number(points.value) > 0)

function startEditStation() {
  editStation.value = true
  nextTick(() => stationInput.value?.focus())
}

function saveStation() {
  editStation.value = false
  localStorage.setItem('marshal_station', station.value.trim() || 'Posten 1')
}

function showError(msg) {
  errorMsg.value = msg
  clearTimeout(errTimer)
  errTimer = setTimeout(() => { errorMsg.value = null }, 4000)
}

async function send() {
  if (!canSend.value) return
  const pts = Number(points.value)
  sending.value = true
  try {
    const { data } = await api.post('/marshal/report', {
      penalty_seconds: pts,
      station:         station.value,
      event_id:        store.activeEvent?.id ?? null,
    })
    clearTimeout(sentTimer)
    sentFlash.value = pts
    sentTimer = setTimeout(() => { sentFlash.value = null }, 2000)
    const now = new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    history.value.push({ ts: data.ts, id: data.id, time: now, points: pts, station: station.value, cancelled: false, cancelling: false })
    points.value = ''
    nextTick(() => pointsInput.value?.focus())
  } catch (e) {
    const detail = e.response?.data?.detail
    if (e.response?.status === 401) showError('Nicht angemeldet – bitte neu einloggen')
    else if (e.response?.status === 403) showError('Keine Berechtigung (Rolle prüfen)')
    else showError(detail || 'Senden fehlgeschlagen')
  } finally {
    sending.value = false
  }
}

async function storno(entry) {
  entry.cancelling = true
  try {
    await api.post('/marshal/cancel', { ts: entry.ts, report_id: entry.id ?? null })
    entry.cancelled = true
  } catch (e) {
    showError('Storno fehlgeschlagen')
  } finally {
    entry.cancelling = false
  }
}

onMounted(() => {
  pointsInput.value?.focus()
})
</script>

<style scoped>
.tabnum { font-variant-numeric: tabular-nums; }
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.25s ease; }
.slide-down-enter-from, .slide-down-leave-to { transform: translateY(-100%); opacity: 0; }

.history-list-enter-active { transition: all 0.3s ease; }
.history-list-leave-active { transition: all 0.2s ease; }
.history-list-enter-from   { opacity: 0; transform: translateY(10px); }
.history-list-leave-to     { opacity: 0; transform: translateX(-20px); }
</style>
