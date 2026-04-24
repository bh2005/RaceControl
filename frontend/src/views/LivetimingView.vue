<template>
  <div class="min-h-screen bg-gray-950 text-white pb-16">

    <!-- Header (eigenständig, kein AppHeader) -->
    <header class="bg-msc-blue shadow-xl sticky top-0 z-10">
      <div class="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <img src="/msc-logo.svg" alt="MSC" class="h-9 w-9 rounded-full border-2 border-white/30">
          <div>
            <div class="font-bold text-sm leading-tight">Livetiming</div>
            <div class="text-blue-200 text-xs">
              {{ store.activeEvent?.name || 'RaceControl Pro' }}
            </div>
          </div>
        </div>
        <span class="flex items-center gap-1.5 text-xs font-bold rounded-full px-2.5 py-1 border transition"
          :class="wsConnected
            ? 'bg-green-500/20 text-green-300 border-green-500/30'
            : 'bg-gray-600/20 text-gray-400 border-gray-600/30'">
          <span class="h-2 w-2 rounded-full inline-block"
            :class="wsConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-500'"></span>
          {{ wsConnected ? 'LIVE' : 'Verbinde…' }}
        </span>
      </div>

      <!-- Klassen-Tabs -->
      <div class="max-w-lg mx-auto px-4 pb-2 flex gap-2 overflow-x-auto">
        <button
          @click="selectedClassId = null"
          class="shrink-0 text-xs font-bold rounded-full px-3 py-1 transition"
          :class="selectedClassId === null ? 'bg-white text-msc-blue' : 'bg-white/10 text-white border border-white/20'"
        >
          Alle
        </button>
        <button
          v-for="c in store.classes"
          :key="c.id"
          @click="selectedClassId = c.id"
          class="shrink-0 text-xs font-semibold rounded-full px-3 py-1 transition border"
          :class="selectedClassId === c.id
            ? 'bg-msc-red text-white border-msc-red font-bold'
            : 'bg-white/10 text-white border-white/20'"
        >
          {{ c.short_name || c.name }}
          <span v-if="c.run_status === 'running'" class="ml-1">▶</span>
        </button>
      </div>
    </header>

    <div class="max-w-lg mx-auto px-4 pt-4 space-y-6">

      <div v-for="cls in visibleClasses" :key="cls.id">

        <!-- Klassen-Header -->
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-bold uppercase tracking-widest text-gray-400">
            {{ cls.name }}
          </span>
          <span
            class="text-xs font-bold rounded px-1.5 py-0.5"
            :class="{
              'bg-green-900/50 text-green-400 border border-green-800':   cls.run_status === 'official',
              'bg-blue-900/50 text-blue-300 border border-blue-700':      cls.run_status === 'running',
              'bg-orange-900/50 text-orange-400 border border-orange-700':cls.run_status === 'paused',
              'bg-amber-900/50 text-amber-400 border border-amber-700':   cls.run_status === 'preliminary',
              'bg-gray-800 text-gray-500':                                 cls.run_status === 'planned',
            }"
          >
            {{ statusLabel(cls.run_status) }}
          </span>
        </div>

        <!-- Ergebnis-Cards -->
        <div class="space-y-2">
          <div
            v-for="(row, i) in standingsByClass[cls.id] || []"
            :key="row.participant_id"
            class="rounded-2xl p-4 flex items-center gap-4"
            :class="rankClass(i + 1)"
          >
            <div
              class="h-12 w-12 rounded-full flex items-center justify-center font-black text-2xl shrink-0"
              :class="i < 3 ? 'bg-black/15' : 'bg-white/5'"
            >
              {{ i + 1 }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="font-black text-xl">#{{ row.start_number }}</span>
                <span class="font-bold text-lg truncate">
                  {{ row.first_name }} {{ row.last_name }}
                </span>
              </div>
              <div class="text-sm opacity-70 mb-1">{{ row.club || 'n.N.' }}</div>
              <!-- Lauf-Details -->
              <div v-for="run in runsFor(cls.id, row.start_number)" :key="run.run_number"
                   class="flex items-center gap-1.5 text-xs font-mono leading-5">
                <span class="opacity-50 w-14 shrink-0">
                  {{ run.run_number === 0 ? 'Training' : 'Lauf ' + run.run_number }}
                </span>
                <template v-if="run.status === 'valid' && run.raw_time !== null">
                  <span class="font-bold">{{ run.raw_time.toFixed(2) }}</span>
                  <template v-if="run.run_number > 0">
                    <span :class="run.total_penalties > 0 ? 'text-red-400 font-bold' : 'opacity-40'">
                      +{{ run.total_penalties.toFixed(1) }}s
                    </span>
                    <template v-if="run.total_penalties > 0">
                      <span class="opacity-40">=</span>
                      <span class="font-bold">{{ run.total_time.toFixed(2) }}</span>
                    </template>
                  </template>
                </template>
                <span v-else class="opacity-40 uppercase">{{ run.status }}</span>
              </div>
            </div>
            <div class="text-right shrink-0">
              <div v-if="row.total_time" class="font-black text-2xl tabnum">
                {{ row.total_time.toFixed(2) }}
              </div>
              <div v-else class="text-gray-500 font-mono">–</div>
              <div v-if="i > 0 && row.total_time && (standingsByClass[cls.id]||[])[0]?.total_time" class="text-xs opacity-60">
                +{{ (row.total_time - (standingsByClass[cls.id]||[])[0].total_time).toFixed(2) }} s
              </div>
              <div v-if="row.valid_runs < totalRuns" class="text-xs opacity-50 mt-0.5">
                Lauf {{ row.valid_runs }}/{{ totalRuns }} *
              </div>
            </div>
          </div>

          <div v-if="!(standingsByClass[cls.id]?.length)" class="text-center text-gray-600 text-sm py-4">
            Noch keine Ergebnisse
          </div>
        </div>
      </div>

      <div v-if="visibleClasses.length === 0" class="text-center text-gray-600 py-12">
        Keine Veranstaltung aktiv
      </div>
    </div>

    <!-- Footer -->
    <div class="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur border-t border-gray-700">
      <div class="max-w-lg mx-auto px-4 py-2 flex items-center justify-between text-xs text-gray-400">
        <span>* = nicht alle Läufe abgeschlossen</span>
        <span>RaceControl Pro</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'
import { useRealtimeUpdate } from '../composables/useRealtimeUpdate'

const store = useEventStore()
const selectedClassId  = ref(null)
const standingsByClass = ref({})
const runsByKey        = ref({})   // `${class_id}_${start_number}` → runs[]
const totalRuns = ref(2)

const visibleClasses = computed(() => {
  const cls = store.classes
  if (selectedClassId.value) return cls.filter(c => c.id === selectedClassId.value)
  return cls
})

function runsFor(classId, startNumber) {
  return runsByKey.value[`${classId}_${startNumber}`] || []
}

async function loadStandings() {
  if (!store.activeEvent) return
  const [stRes, runRes] = await Promise.all([
    api.get(`/events/${store.activeEvent.id}/standings`),
    api.get(`/events/${store.activeEvent.id}/run-results`),
  ])

  const grouped = {}
  for (const row of stRes.data) {
    ;(grouped[row.class_id] ??= []).push(row)
  }
  standingsByClass.value = grouped

  const runMap = {}
  for (const r of runRes.data) {
    const key = `${r.class_id}_${r.start_number}`
    ;(runMap[key] ??= []).push(r)
  }
  for (const key in runMap) {
    runMap[key].sort((a, b) => a.run_number - b.run_number)
  }
  runsByKey.value = runMap
}

// WebSocket — sofortige Updates bei neuen Ergebnissen oder Statuswechseln
const { connected: wsConnected } = useRealtimeUpdate(async (msg) => {
  if (!store.activeEvent) return
  if (msg.event_id && msg.event_id !== store.activeEvent.id) return
  if (msg.type === 'results') await loadStandings()
  if (msg.type === 'classes') await store.loadEvents()
})

// Fallback-Polling (30 s) — fängt Änderungen auf, die ohne WS-Trigger passieren
let fallback = null
onMounted(async () => {
  if (!store.classes.length) await store.loadEvents()
  await loadStandings()
  fallback = setInterval(async () => {
    await store.loadEvents()
    await loadStandings()
  }, 30000)
})
onUnmounted(() => clearInterval(fallback))

function rankClass(rank) {
  if (rank === 1) return 'bg-gradient-to-r from-yellow-400 to-amber-400 text-gray-900'
  if (rank === 2) return 'bg-gradient-to-r from-slate-300 to-slate-400 text-gray-900'
  if (rank === 3) return 'bg-gradient-to-r from-amber-700 to-amber-800 text-white'
  return 'bg-gray-800 text-gray-200'
}

function statusLabel(s) {
  return { planned: 'Geplant', running: 'Läuft ▶', paused: 'Unterbrochen ⏸', preliminary: 'Vorläufig', official: 'Offiziell' }[s] || s
}
</script>
