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

    <!-- Log -->
    <div v-if="log.length" class="bg-gray-900 px-4 py-3 space-y-1 max-h-44 overflow-y-auto">
      <div class="text-xs text-gray-500 font-semibold uppercase tracking-widest mb-1">Letzte Meldungen</div>
      <div
        v-for="(entry, i) in [...log].reverse()"
        :key="i"
        class="flex items-center gap-3 text-sm"
      >
        <span class="text-gray-500 font-mono text-xs w-16 shrink-0">{{ entry.time }}</span>
        <span class="font-black text-yellow-400 tabnum">{{ entry.points }} Pkt</span>
        <span class="text-gray-500 text-xs">{{ entry.station }}</span>
      </div>
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
let sentTimer      = null
const log          = ref([])

const canSend = computed(() => !sending.value && Number(points.value) > 0)

function startEditStation() {
  editStation.value = true
  nextTick(() => stationInput.value?.focus())
}

function saveStation() {
  editStation.value = false
  localStorage.setItem('marshal_station', station.value.trim() || 'Posten 1')
}

async function send() {
  if (!canSend.value) return
  const pts = Number(points.value)
  sending.value = true
  try {
    await api.post('/marshal/report', {
      penalty_seconds: pts,
      station:         station.value,
    })
    clearTimeout(sentTimer)
    sentFlash.value = pts
    sentTimer = setTimeout(() => { sentFlash.value = null }, 2000)
    const now = new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    log.value.push({ time: now, points: pts, station: station.value })
    if (log.value.length > 20) log.value.shift()
    points.value = ''
    nextTick(() => pointsInput.value?.focus())
  } catch {
    // silent
  } finally {
    sending.value = false
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
</style>
