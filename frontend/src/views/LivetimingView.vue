<template>
  <div class="min-h-screen bg-gray-950 text-white pb-16">

    <!-- Header (eigenständig, kein AppHeader) -->
    <header class="bg-msc-blue shadow-xl sticky top-0 z-10">
      <div class="max-w-lg md:max-w-2xl lg:max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <img src="/msc-logo.svg" alt="MSC" class="h-9 w-9 rounded-full border-2 border-white/30">
          <div>
            <div class="font-bold text-sm leading-tight">Livetiming</div>
            <div class="text-blue-200 text-xs">
              {{ store.activeEvent?.name || 'RaceControl Pro' }}
            </div>
          </div>
        </div>
        <span role="status" aria-live="polite"
          :aria-label="wsConnected ? 'Live-Verbindung aktiv' : 'Verbindung wird hergestellt'"
          class="flex items-center gap-1.5 text-xs font-bold rounded-full px-2.5 py-1 border transition"
          :class="wsConnected
            ? 'bg-green-500/20 text-green-300 border-green-500/30'
            : 'bg-gray-600/20 text-gray-400 border-gray-600/30'">
          <span aria-hidden="true" class="h-2 w-2 rounded-full inline-block"
            :class="wsConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-500'"></span>
          {{ wsConnected ? 'LIVE' : 'Verbinde…' }}
        </span>
      </div>

      <ClassTabs
        :classes="store.classes"
        :training-available="!!trainingData"
        v-model:selected-class-id="selectedClassId"
        v-model:show-training="showTraining"
      />
    </header>

    <main class="max-w-lg md:max-w-2xl lg:max-w-4xl mx-auto px-4 pt-4 space-y-6">

      <!-- ── TRAINING-ANSICHT ── -->
      <template v-if="showTraining && trainingData">
        <!-- Session-Header -->
        <div class="flex items-center gap-3 mb-2">
          <span class="text-xs font-bold uppercase tracking-widest text-gray-400">
            {{ trainingData.session.name }}
          </span>
          <span v-if="trainingData.session.discipline_name"
                class="text-xs font-bold rounded px-1.5 py-0.5 bg-cyan-900/60 text-cyan-300 border border-cyan-700">
            {{ trainingData.session.discipline_name }}
          </span>
          <span class="text-xs font-bold rounded px-1.5 py-0.5 bg-green-900/50 text-green-400 border border-green-800">
            Läuft ▶
          </span>
        </div>

        <!-- Wertungs-Cards -->
        <ul role="list" class="space-y-2">
          <li
            v-for="(row, i) in trainingData.standings"
            :key="row.trainee_id"
            :aria-label="`Platz ${i + 1}: ${row.first_name} ${row.last_name}`"
            class="rounded-2xl p-4 flex items-center gap-4"
            :class="rankClass(i + 1)"
          >
            <div class="h-12 w-12 rounded-full flex items-center justify-center font-black text-2xl shrink-0"
                 :class="i < 3 ? 'bg-black/15' : 'bg-white/5'">
              {{ i + 1 }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="font-bold text-lg truncate">
                {{ row.first_name }} {{ row.last_name }}
              </div>
              <div class="text-sm opacity-70">{{ row.club_name || 'n.N.' }}</div>
              <div class="text-xs font-mono opacity-50 mt-0.5">{{ row.run_count }}× Lauf</div>
            </div>
            <div class="text-right shrink-0">
              <div v-if="row.best_time" class="font-black text-2xl tabnum text-cyan-400">
                {{ fmtTrain(row.best_time) }} s
              </div>
              <div v-else class="text-gray-500 font-mono">–</div>
              <div v-if="i > 0 && row.best_time && trainingData.standings[0]?.best_time"
                   class="text-xs opacity-60">
                {{ fmtDeltaTrain(row.best_time, trainingData.standings[0].best_time) }} s
              </div>
              <div v-if="row.avg_time" class="text-xs opacity-40">
                Ø {{ fmtTrain(row.avg_time) }} s
              </div>
            </div>
          </li>

          <li v-if="!trainingData.standings.length"
               class="text-center text-gray-600 text-sm py-4">
            Noch keine Läufe
          </li>
        </ul>

        <!-- Letzte Läufe -->
        <div v-if="trainingData.recent_runs.length" class="mt-4">
          <div class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">
            Letzte Läufe
          </div>
          <div class="space-y-1">
            <div v-for="r in trainingData.recent_runs.slice(0, RECENT_RUNS_LIMIT)" :key="r.id"
                 class="bg-gray-800 rounded-lg px-3 py-2 flex items-center gap-3 text-sm">
              <span class="font-semibold text-gray-200 flex-1 truncate">
                {{ r.first_name }} {{ r.last_name }}
              </span>
              <span class="font-mono text-xs text-gray-400">#{{ r.run_number }}</span>
              <span v-if="r.status === 'valid' && r.total_time != null"
                    class="font-black tabnum text-cyan-400">
                {{ fmtTrain(r.total_time) }} s
              </span>
              <span v-else class="text-gray-500 text-xs">{{ r.status.toUpperCase() }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- ── RENNERGEBNISSE ── -->
      <template v-else>
      <div v-for="cls in visibleClasses" :key="cls.id">

        <!-- Klassen-Header -->
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs font-bold uppercase tracking-widest text-gray-400">
            {{ cls.name }}
          </span>
          <StatusBadge :status="cls.run_status" theme="dark" class="font-bold" />
        </div>

        <!-- Ergebnis-Cards -->
        <ul role="list" class="space-y-2">
          <li
            v-for="(row, i) in standingsByClass[cls.id] || []"
            :key="row.participant_id"
            :aria-label="`Platz ${i + 1}: ${row.first_name} ${row.last_name}`"
            class="rounded-2xl p-4 flex items-center gap-4"
            :class="rankClass(i + 1)"
          >
            <div
              class="h-12 w-12 rounded-full flex items-center justify-center font-black text-2xl shrink-0"
              :class="i < 3 ? 'bg-black/15' : 'bg-white/5'"
              aria-hidden="true"
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
                  <span class="font-bold">{{ fmtRace(run.raw_time) }}</span>
                  <template v-if="run.run_number > 0">
                    <span :class="penaltyClass(run.total_penalties)">
                      +{{ fmtPenalty(run.total_penalties) }}s
                    </span>
                    <template v-if="run.total_penalties > 0">
                      <span class="opacity-40">=</span>
                      <span class="font-bold">{{ fmtRace(run.total_time) }}</span>
                    </template>
                  </template>
                </template>
                <span v-else class="opacity-40 uppercase">{{ run.status }}</span>
              </div>
            </div>
            <div class="text-right shrink-0">
              <div v-if="row.total_time" class="font-black text-2xl tabnum"
                   :class="row._training ? 'text-cyan-400' : ''">
                {{ fmtRace(row.total_time) }}
              </div>
              <div v-else class="text-gray-500 font-mono">–</div>
              <div v-if="i > 0 && row.total_time && (standingsByClass[cls.id]||[])[0]?.total_time" class="text-xs opacity-60">
                {{ fmtDelta(row.total_time, (standingsByClass[cls.id]||[])[0].total_time) }} s
              </div>
              <div v-if="row._training" class="text-xs opacity-50 mt-0.5">Training</div>
              <div v-else-if="row.valid_runs < (runsPerClass[cls.id] ?? DEFAULT_RUNS)" class="text-xs opacity-50 mt-0.5">
                Lauf {{ row.valid_runs }}/{{ runsPerClass[cls.id] ?? DEFAULT_RUNS }} *
              </div>
            </div>
          </li>

          <li v-if="!(standingsByClass[cls.id]?.length)" class="text-center text-gray-600 text-sm py-4">
            Noch keine Ergebnisse
          </li>
        </ul>
      </div>

      <div v-if="initialLoad" class="flex justify-center py-20"
           role="status" aria-label="Lädt…">
        <div class="h-10 w-10 rounded-full border-4 border-white/10 border-t-white/60 animate-spin"></div>
      </div>
      <div v-else-if="visibleClasses.length === 0" class="text-center text-gray-600 py-12">
        Keine Veranstaltung aktiv
      </div>
      </template> <!-- end v-else (race) -->

    </main>

    <!-- Footer -->
    <footer class="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur border-t border-gray-700">
      <div class="max-w-lg md:max-w-2xl lg:max-w-4xl mx-auto px-4 py-2 flex items-center justify-between text-xs text-gray-400">
        <span v-if="hasIncompleteRuns">* = nicht alle Läufe abgeschlossen</span>
        <span v-else></span>
        <span>RaceControl Pro · v{{ version }}</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'
import { useRealtimeUpdate } from '../composables/useRealtimeUpdate'
import ClassTabs    from '../components/ClassTabs.vue'
import StatusBadge  from '../components/StatusBadge.vue'
import TimeDisplay  from '../components/TimeDisplay.vue'
import { fmtRace, fmtTrain, fmtPenalty, fmtDelta, fmtDeltaTrain } from '../utils/format'
import { POLL_INTERVAL_MS, DEFAULT_RUNS, RECENT_RUNS_LIMIT } from '../constants/contest'
import { version } from '../../package.json'


// ── Store & State ─────────────────────────────────────────────────────────────
const store = useEventStore()
const selectedClassId  = ref(null)
const initialLoad      = ref(true)
const standingsByClass = ref({})
const runsByKey        = ref({})   // `${class_id}_${start_number}` → runs[]
const runsPerClass     = ref({})   // class_id → max observed run_number
const showTraining     = ref(false)
const trainingData     = ref(null)

const visibleClasses = computed(() => {
  const cls = store.classes
  if (selectedClassId.value) return cls.filter(c => c.id === selectedClassId.value)
  return cls
})

const hasIncompleteRuns = computed(() =>
  Object.entries(standingsByClass.value).some(([classId, rows]) =>
    rows.some(r => r.valid_runs < (runsPerClass.value[classId] ?? DEFAULT_RUNS))
  )
)

function runsFor(classId, startNumber) {
  return runsByKey.value[`${classId}_${startNumber}`] || []
}

// ── CSS class helpers ──────────────────────────────────────────────────────────
function penaltyClass(p) { return p > 0 ? 'text-red-400 font-bold' : 'opacity-40' }

function rankClass(rank) {
  if (rank === 1) return 'bg-gradient-to-r from-yellow-400 to-amber-400 text-gray-900'
  if (rank === 2) return 'bg-gradient-to-r from-slate-300 to-slate-400 text-gray-900'
  if (rank === 3) return 'bg-gradient-to-r from-amber-700 to-amber-800 text-white'
  return 'bg-gray-800 text-gray-200'
}

// ── Data loading ───────────────────────────────────────────────────────────────
async function loadTrainingData() {
  try {
    const { data } = await api.get('/public/training/active')
    trainingData.value = data
  } catch (e) {
    console.warn('[Livetiming] Training-Ladefehler:', e)
    trainingData.value = null
    if (showTraining.value) showTraining.value = false
  }
}

async function loadStandings() {
  if (!store.activeEvent) return
  try {
    const [stRes, runRes] = await Promise.all([
      api.get(`/events/${store.activeEvent.id}/standings`),
      api.get(`/events/${store.activeEvent.id}/run-results`),
    ])

    const grouped = {}
    for (const row of stRes.data) {
      ;(grouped[row.class_id] ??= []).push(row)
    }

    // For classes with no wertungsläufe yet, fall back to training results
    const classesWithStandings = new Set(stRes.data.map(r => r.class_id))
    for (const r of runRes.data) {
      if (r.run_number !== 0 || r.status !== 'valid' || r.raw_time === null) continue
      if (classesWithStandings.has(r.class_id)) continue
      ;(grouped[r.class_id] ??= []).push({
        participant_id: r.participant_id,
        start_number:   r.start_number,
        first_name:     r.first_name,
        last_name:      r.last_name,
        club:           r.club,
        total_time:     r.raw_time,
        valid_runs:     0,
        rank:           0,
        _training:      true,
      })
    }
    for (const cid in grouped) {
      if (grouped[cid][0]?._training) {
        grouped[cid].sort((a, b) => (a.total_time ?? 9_999) - (b.total_time ?? 9_999))
      }
    }

    standingsByClass.value = grouped

    const runMap = {}
    const maxByClass = {}
    for (const r of runRes.data) {
      const key = `${r.class_id}_${r.start_number}`
      ;(runMap[key] ??= []).push(r)
      if (r.run_number > 0) {
        maxByClass[r.class_id] = Math.max(maxByClass[r.class_id] ?? 0, r.run_number)
      }
    }
    for (const key in runMap) {
      runMap[key].sort((a, b) => a.run_number - b.run_number)
    }
    runsByKey.value = runMap
    runsPerClass.value = maxByClass
  } catch (e) {
    console.warn('[Livetiming] Standings-Ladefehler:', e)
  }
}

// ── Guard: prevents async callbacks from writing to refs after unmount ─────────
let mounted = true

// ── WebSocket ──────────────────────────────────────────────────────────────────
const { connected: wsConnected } = useRealtimeUpdate(async (msg) => {
  if (!mounted) return
  if (msg.type === 'training_run') { await loadTrainingData(); return }
  if (!store.activeEvent) return
  if (msg.event_id && msg.event_id !== store.activeEvent.id) return
  if (msg.type === 'results') await loadStandings()
  if (msg.type === 'classes') await store.loadEvents().catch(e => console.warn('[Livetiming] Event-Ladefehler:', e))
})

// ── Fallback polling — only active while WS is disconnected ───────────────────
let fallback = null
function startPolling() {
  if (fallback) return
  fallback = setInterval(async () => {
    if (!mounted) return
    await store.loadEvents().catch(e => console.warn('[Livetiming] Event-Ladefehler:', e))
    await Promise.all([loadStandings(), loadTrainingData()])
  }, POLL_INTERVAL_MS)
}
function stopPolling() { clearInterval(fallback); fallback = null }

watch(wsConnected, (live) => { if (live) stopPolling(); else startPolling() }, { immediate: true })

onMounted(async () => {
  if (!store.classes.length) await store.loadEvents().catch(e => console.warn('[Livetiming] Event-Ladefehler:', e))
  await Promise.all([loadStandings(), loadTrainingData()])
  initialLoad.value = false
})
onUnmounted(() => { mounted = false; stopPolling() })
</script>
