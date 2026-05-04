<template>
  <div class="max-w-7xl mx-auto px-4 py-4 pb-12 grid grid-cols-1 lg:grid-cols-12 gap-4">

    <!-- ── LINKE SPALTE: Session + Fahrerliste ── -->
    <aside class="col-span-full lg:col-span-3 space-y-3">

      <!-- Session-Auswahl -->
      <div>
        <label class="text-xs font-bold uppercase tracking-widest text-gray-500 block mb-1">Training-Session</label>
        <select v-model="selectedSessionId" @change="loadSession" class="input font-semibold text-sm">
          <option :value="null" disabled>– Session wählen –</option>
          <option v-for="s in sessions" :key="s.id" :value="s.id">
            {{ s.date }} · {{ s.name }}
            <template v-if="s.discipline_name"> [{{ s.discipline_name }}]</template>
            <template v-if="s.status === 'active'"> ▶</template>
          </option>
        </select>
        <div v-if="selectedSession?.discipline_name"
             class="mt-1.5 flex items-center gap-1.5">
          <span class="text-xs font-semibold bg-blue-100 text-blue-700 rounded px-2 py-0.5">
            {{ selectedSession.discipline_name }}
          </span>
        </div>
      </div>

      <!-- Kein aktiver Fahrer -->
      <div v-if="!selectedSession" class="bg-gray-100 rounded-xl p-3 text-center text-gray-400 text-sm">
        Keine Session ausgewählt
      </div>

      <!-- Aktueller Fahrer -->
      <div v-if="currentTrainee" class="bg-msc-blue text-white rounded-xl p-3 shadow-md">
        <div class="flex items-center justify-between mb-1">
          <span class="text-2xl font-black">Kart {{ currentTrainee.kart_number || '?' }}</span>
          <span class="bg-white/20 text-xs rounded px-2 py-0.5 font-mono">→ JETZT</span>
        </div>
        <div class="font-bold text-lg leading-tight">
          {{ currentTrainee.first_name }} {{ currentTrainee.last_name }}
        </div>
        <div class="text-blue-200 text-sm">{{ currentTrainee.club_name || '' }}</div>
        <div class="text-blue-300 text-xs mt-1">
          {{ traineeRunCount(currentTrainee.id) }} Lauf/Läufe · Bestzeit: {{ fmtTime(traineeBest(currentTrainee.id)) }}
        </div>
      </div>
      <div v-else-if="selectedSession" class="bg-gray-100 rounded-xl p-3 text-center text-gray-400 text-sm">
        Kein Fahrer ausgewählt
      </div>

      <!-- Fahrerliste -->
      <div v-if="selectedSession">
        <div class="flex items-center justify-between px-1 mb-1.5">
          <span class="text-xs text-gray-400 font-semibold uppercase tracking-widest">Fahrer</span>
          <input v-model="traineeSearch" type="text" placeholder="Suche…"
                 class="text-xs input py-0.5 px-2 w-28">
        </div>
        <div class="space-y-1 max-h-64 lg:max-h-[calc(100vh-340px)] overflow-y-auto pr-1">
          <div
            v-for="t in filteredTrainees"
            :key="t.id"
            @click="setCurrentTrainee(t)"
            class="bg-white rounded-lg px-3 py-2 flex items-center gap-2 shadow-sm border transition cursor-pointer"
            :class="currentTrainee?.id === t.id
              ? 'border-msc-blue bg-blue-50/60'
              : 'border-gray-100 hover:border-blue-200 hover:bg-blue-50/30'"
          >
            <div class="text-sm font-black text-gray-600 w-8 shrink-0 text-center">
              {{ t.kart_number || '–' }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="font-semibold text-sm text-gray-800 truncate">
                {{ t.last_name }}, {{ t.first_name }}
              </div>
              <div class="text-xs text-gray-400">{{ t.club_name || '' }}</div>
            </div>
            <div class="text-right text-xs text-gray-400 shrink-0">
              <div>{{ traineeRunCount(t.id) }}×</div>
              <div class="font-mono font-bold text-gray-600">{{ fmtTime(traineeBest(t.id)) }}</div>
            </div>
          </div>
          <div v-if="!filteredTrainees.length" class="text-xs text-gray-400 text-center py-3">
            Keine aktiven Fahrer
          </div>
        </div>
      </div>
    </aside>

    <!-- ── MITTE: Zeitnahme ── -->
    <section class="col-span-full lg:col-span-5 space-y-4">

      <div v-if="!selectedSession" class="card p-8 text-center text-gray-400">
        <div class="text-4xl mb-3">🏁</div>
        <div class="font-semibold">Keine Training-Session aktiv</div>
        <div class="text-sm mt-1">Im Admin-Bereich unter "Training" eine Session erstellen und aktivieren.</div>
      </div>

      <template v-else>
        <!-- Session-Status-Banner -->
        <div v-if="selectedSession.status !== 'active'"
             class="rounded-xl px-4 py-3 flex items-center gap-3 text-sm font-semibold bg-amber-100 text-amber-800 border border-amber-300">
          <span class="text-xl">⚠</span>
          Session ist {{ selectedSession.status === 'planned' ? 'noch nicht gestartet' : 'beendet' }}.
          Im Admin-Bereich aktivieren.
        </div>

        <!-- Zeit-Eingabe -->
        <div class="card p-5">
          <div class="flex items-center justify-between mb-3">
            <h2 class="font-bold text-gray-700 text-sm uppercase tracking-widest">
              <span v-if="currentTrainee">
                {{ currentTrainee.first_name }} {{ currentTrainee.last_name }}
                <span class="text-gray-400 font-normal">· Kart {{ currentTrainee.kart_number || '?' }}</span>
              </span>
              <span v-else class="text-gray-400">Kein Fahrer ausgewählt</span>
            </h2>
            <div class="flex gap-1.5">
              <button @click="setStatus('dns')" class="px-3 py-1 rounded-lg text-xs font-bold bg-gray-100 hover:bg-gray-200 text-gray-600 transition">DNS</button>
              <button @click="setStatus('dnf')" class="px-3 py-1 rounded-lg text-xs font-bold bg-amber-100 hover:bg-amber-200 text-amber-700 transition">DNF</button>
              <button @click="setStatus('dsq')" class="px-3 py-1 rounded-lg text-xs font-bold bg-red-100 hover:bg-red-200 text-red-700 transition">DSQ</button>
            </div>
          </div>

          <!-- Lichtschranken-Status -->
          <div class="flex items-center gap-2 text-xs mb-3">
            <span class="h-2 w-2 rounded-full shrink-0 transition-colors duration-500"
                  :class="lsConnected ? 'bg-green-500' : 'bg-gray-300'"></span>
            <span :class="lsConnected ? 'text-green-700 font-semibold' : 'text-gray-400'">
              {{ lsConnected ? 'Lichtschranke verbunden' : 'Lichtschranke nicht verbunden' }}
            </span>
            <Transition name="fade">
              <span v-if="lsFlash" class="ml-auto text-green-600 font-bold">⚡ Zeit eingetragen</span>
            </Transition>
          </div>

          <!-- Zeitfeld -->
          <div class="flex items-center gap-3 mb-3">
            <div class="flex-1 relative">
              <input
                ref="timeInput"
                v-model="rawTime"
                type="text"
                inputmode="decimal"
                placeholder="0.00"
                :disabled="entryStatus !== 'valid'"
                class="w-full text-center border-2 rounded-xl px-4 py-3 text-6xl font-black tabnum focus:outline-none focus:ring-4 bg-blue-50/30 transition-colors duration-300 disabled:opacity-40 disabled:bg-gray-50"
                :class="lsFlash
                  ? 'border-green-500 ring-4 ring-green-200 bg-green-50/30 text-green-700'
                  : 'border-msc-blue focus:ring-blue-200 text-msc-blue'"
                @keydown.enter.prevent="saveRun"
              >
              <span v-if="entryStatus === 'valid'" class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-lg font-semibold">s</span>
              <span v-else class="absolute inset-0 flex items-center justify-center text-4xl font-black text-gray-500 pointer-events-none">
                {{ entryStatus.toUpperCase() }}
              </span>
            </div>
            <div class="text-right text-sm text-gray-500 shrink-0 w-24">
              <div>Strafen:</div>
              <div class="font-bold text-msc-red text-xl tabnum">+ {{ penaltySeconds.toFixed(0) }} s</div>
              <div class="border-t border-gray-200 pt-1 mt-1">Gesamt:</div>
              <div class="font-black text-gray-800 text-xl tabnum">
                {{ totalTime !== null ? fmtTime(totalTime) : '–' }}
              </div>
            </div>
          </div>

          <!-- Straf-Schnelltasten -->
          <div class="flex flex-wrap gap-1.5 mb-4">
            <span class="text-xs text-gray-400 self-center mr-1">Strafen:</span>
            <button
              v-for="p in PENALTIES"
              :key="p.label"
              @click="addPenalty(p.seconds)"
              class="px-2.5 py-1 rounded-lg text-xs font-bold border border-gray-200 hover:border-msc-red hover:bg-red-50 hover:text-msc-red transition"
            >
              +{{ p.seconds }}s {{ p.label }}
            </button>
            <button v-if="penaltySeconds > 0"
              @click="penaltySeconds = 0"
              class="ml-auto px-2 py-1 rounded-lg text-xs font-bold text-gray-400 hover:text-msc-red transition"
            >
              ✕ Strafen zurücksetzen
            </button>
          </div>

          <!-- Speichern -->
          <button
            @click="saveRun"
            :disabled="!currentTrainee || selectedSession.status !== 'active'"
            class="w-full btn-primary py-3 text-base font-bold disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Lauf speichern
          </button>
          <div v-if="saveError" class="text-xs text-red-600 bg-red-50 rounded px-2 py-1.5 mt-2">{{ saveError }}</div>
        </div>

        <!-- Letzte Läufe des aktuellen Fahrers -->
        <div v-if="currentTrainee && currentTraineeRuns.length" class="card overflow-hidden">
          <div class="px-4 py-2.5 border-b border-gray-100 text-xs font-bold text-gray-500 uppercase tracking-widest">
            Läufe · {{ currentTrainee.first_name }} {{ currentTrainee.last_name }}
          </div>
          <table class="w-full text-sm">
            <tbody class="divide-y divide-gray-100">
              <tr v-for="r in currentTraineeRuns" :key="r.id"
                  class="hover:bg-gray-50">
                <td class="py-2 px-3 text-gray-400 text-xs font-mono w-8">{{ r.run_number }}</td>
                <td class="py-2 px-3 font-black tabnum text-msc-blue text-base">
                  <span v-if="r.status === 'valid' && r.raw_time != null">{{ fmtTime(r.total_time) }}</span>
                  <span v-else class="text-gray-400">{{ r.status.toUpperCase() }}</span>
                </td>
                <td class="py-2 px-2 text-xs text-gray-400">
                  <span v-if="r.penalty_seconds > 0" class="text-msc-red font-semibold">+{{ r.penalty_seconds }}s</span>
                </td>
                <td class="py-2 px-2 text-xs text-gray-400">{{ r.source === 'lichtschranke' ? '⚡' : '' }}</td>
                <td class="py-2 px-2">
                  <button @click="deleteRun(r)" class="text-gray-300 hover:text-msc-red text-xs">✕</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </section>

    <!-- ── RECHTE SPALTE: Wertung ── -->
    <aside class="col-span-full lg:col-span-4 space-y-3">

      <div class="flex items-center justify-between px-1">
        <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500">Session-Wertung</h2>
        <button @click="loadStandings" class="text-xs text-msc-blue hover:underline">↺ Aktualisieren</button>
      </div>

      <div class="card overflow-hidden">
        <table class="w-full text-sm" v-if="standings.length">
          <thead>
            <tr class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
              <th class="py-2 px-2 text-center w-8">#</th>
              <th class="py-2 px-3 text-left">Fahrer</th>
              <th class="py-2 px-2 text-center">Läufe</th>
              <th class="py-2 px-3 text-right">Bestzeit</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="s in standings"
              :key="s.trainee_id"
              class="transition"
              :class="currentTrainee?.id === s.trainee_id ? 'bg-blue-50/60 font-semibold' : 'hover:bg-gray-50'"
            >
              <td class="py-2.5 px-2 text-center font-black text-gray-400">{{ s.rank }}</td>
              <td class="py-2.5 px-3">
                <div class="font-semibold text-gray-800">{{ s.last_name }}, {{ s.first_name }}</div>
                <div class="text-xs text-gray-400">{{ s.club_name || '' }}</div>
              </td>
              <td class="py-2.5 px-2 text-center text-gray-500">{{ s.run_count }}</td>
              <td class="py-2.5 px-3 text-right font-black tabnum text-msc-blue">
                {{ fmtTime(s.best_time) }}
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="py-8 text-center text-gray-400 text-sm">
          {{ selectedSession ? 'Noch keine Läufe gespeichert' : 'Keine Session ausgewählt' }}
        </div>
      </div>

      <!-- Alle Läufe der Session (kompakt) -->
      <div v-if="sessionRuns.length" class="card overflow-hidden">
        <div class="px-4 py-2.5 border-b border-gray-100 text-xs font-bold text-gray-500 uppercase tracking-widest">
          Alle Läufe ({{ sessionRuns.length }})
        </div>
        <div class="max-h-60 overflow-y-auto">
          <table class="w-full text-xs">
            <tbody class="divide-y divide-gray-100">
              <tr v-for="r in sessionRuns" :key="r.id" class="hover:bg-gray-50">
                <td class="py-1.5 px-3 text-gray-500">{{ r.last_name }}, {{ r.first_name }}</td>
                <td class="py-1.5 px-2 text-gray-400 font-mono">{{ r.run_number }}</td>
                <td class="py-1.5 px-2 font-bold tabnum text-msc-blue">
                  <span v-if="r.status === 'valid' && r.raw_time != null">{{ fmtTime(r.total_time) }}</span>
                  <span v-else class="text-gray-400">{{ r.status.toUpperCase() }}</span>
                </td>
                <td class="py-1.5 px-1 text-gray-300">{{ r.source === 'lichtschranke' ? '⚡' : '' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </aside>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import api from '../api/client'

// ── Straf-Definitionen für Training ──────────────────────────────────────────
const PENALTIES = [
  { label: 'Pylone',  seconds: 3  },
  { label: 'Tor',     seconds: 10 },
  { label: 'Gasse',   seconds: 15 },
  { label: 'Linie',   seconds: 3  },
]

// ── State ─────────────────────────────────────────────────────────────────────
const sessions        = ref([])
const selectedSessionId = ref(null)
const selectedSession   = ref(null)
const trainees          = ref([])       // alle aktiven Trainees
const sessionRuns       = ref([])       // alle Läufe dieser Session
const standings         = ref([])

const currentTrainee  = ref(null)
const rawTime         = ref('')
const penaltySeconds  = ref(0)
const entryStatus     = ref('valid')   // valid | dns | dnf | dsq
const saveError       = ref('')
const traineeSearch   = ref('')

const lsConnected = ref(false)
const lsFlash     = ref(false)
let   lsFlashTimer  = null
let   ws            = null

const timeInput = ref(null)

// ── Computed ──────────────────────────────────────────────────────────────────
const filteredTrainees = computed(() => {
  const q = traineeSearch.value.trim().toLowerCase()
  if (!q) return trainees.value
  return trainees.value.filter(t =>
    t.first_name.toLowerCase().includes(q) ||
    t.last_name.toLowerCase().includes(q) ||
    (t.kart_number || '').includes(q)
  )
})

const totalTime = computed(() => {
  if (entryStatus.value !== 'valid') return null
  const t = parseFloat(rawTime.value.replace(',', '.'))
  if (isNaN(t)) return null
  return t + penaltySeconds.value
})

const currentTraineeRuns = computed(() =>
  sessionRuns.value
    .filter(r => r.trainee_id === currentTrainee.value?.id)
    .sort((a, b) => b.run_number - a.run_number)
)

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmtTime(s) {
  if (s == null) return '–'
  return s.toFixed(3) + ' s'
}

function traineeRunCount(id) {
  return sessionRuns.value.filter(r => r.trainee_id === id).length
}

function traineeBest(id) {
  const times = sessionRuns.value
    .filter(r => r.trainee_id === id && r.status === 'valid' && r.total_time != null)
    .map(r => r.total_time)
  return times.length ? Math.min(...times) : null
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function loadSessions() {
  const { data } = await api.get('/training/sessions')
  sessions.value = data
  // Auto-select aktive Session
  const active = data.find(s => s.status === 'active')
  if (active && !selectedSessionId.value) {
    selectedSessionId.value = active.id
    await loadSession()
  }
}

async function loadSession() {
  if (!selectedSessionId.value) return
  const { data } = await api.get(`/training/sessions/${selectedSessionId.value}`)
  selectedSession.value = data
  await Promise.all([loadTrainees(), loadRuns(), loadStandings()])
}

async function loadTrainees() {
  const { data } = await api.get('/trainees?active_only=true')
  // Enriche mit Club-Namen aus Runs
  trainees.value = data
}

async function loadRuns() {
  if (!selectedSessionId.value) return
  const { data } = await api.get(`/training/sessions/${selectedSessionId.value}/runs`)
  sessionRuns.value = data
}

async function loadStandings() {
  if (!selectedSessionId.value) return
  const { data } = await api.get(`/training/sessions/${selectedSessionId.value}/standings`)
  standings.value = data
}

// ── Fahrer setzen ─────────────────────────────────────────────────────────────
function setCurrentTrainee(t) {
  currentTrainee.value = t
  resetEntry()
  timeInput.value?.focus()
}

function resetEntry() {
  rawTime.value = ''
  penaltySeconds.value = 0
  entryStatus.value = 'valid'
  saveError.value = ''
}

function setStatus(s) {
  entryStatus.value = entryStatus.value === s ? 'valid' : s
  if (entryStatus.value !== 'valid') rawTime.value = ''
}

function addPenalty(s) {
  penaltySeconds.value += s
}

// ── Lauf speichern ────────────────────────────────────────────────────────────
async function saveRun() {
  if (!currentTrainee.value || selectedSession.value?.status !== 'active') return
  saveError.value = ''

  const rawVal = entryStatus.value === 'valid' ? parseFloat(rawTime.value.replace(',', '.')) : null
  if (entryStatus.value === 'valid' && (isNaN(rawVal) || rawVal <= 0)) {
    saveError.value = 'Bitte eine gültige Zeit eingeben (z.B. 45.32 oder 45,32)'
    return
  }

  try {
    await api.post(`/training/sessions/${selectedSessionId.value}/runs`, {
      trainee_id:      currentTrainee.value.id,
      raw_time:        rawVal,
      penalty_seconds: penaltySeconds.value,
      status:          entryStatus.value,
      source:          'manual',
    })
    await Promise.all([loadRuns(), loadStandings()])
    resetEntry()
    timeInput.value?.focus()
  } catch (e) {
    saveError.value = e.response?.data?.detail || 'Fehler beim Speichern'
  }
}

async function deleteRun(r) {
  if (!confirm(`Lauf ${r.run_number} von ${r.first_name} ${r.last_name} löschen?`)) return
  await api.delete(`/training/sessions/${selectedSessionId.value}/runs/${r.id}`)
  await Promise.all([loadRuns(), loadStandings()])
}

// ── WebSocket (Lichtschranke) ─────────────────────────────────────────────────
function connectWs() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${proto}://${location.host}/ws`)
  ws.onmessage = ({ data }) => {
    try {
      const msg = JSON.parse(data)
      if (msg.type === 'timing_device_status') {
        lsConnected.value = msg.connected
      }
      if (msg.type === 'timing_result' && msg.raw_time != null) {
        // Zeit automatisch eintragen wenn Fahrer ausgewählt und Feld leer
        if (currentTrainee.value && entryStatus.value === 'valid') {
          rawTime.value = msg.raw_time.toFixed(3)
          lsFlash.value = true
          clearTimeout(lsFlashTimer)
          lsFlashTimer = setTimeout(() => { lsFlash.value = false }, 3000)
        }
      }
      // Wertung aktualisieren wenn ein anderer Client einen Lauf gespeichert hat
      if (msg.type === 'training_run' && msg.session_id === selectedSessionId.value) {
        loadRuns()
        loadStandings()
      }
    } catch { /* ignore */ }
  }
  ws.onclose = () => {
    lsConnected.value = false
    setTimeout(connectWs, 3000)
  }
}

onMounted(async () => {
  await loadSessions()
  connectWs()
})

onUnmounted(() => {
  ws?.close()
  clearTimeout(lsFlashTimer)
})

watch(selectedSessionId, () => loadSession())
</script>

<style scoped>
.tabnum { font-variant-numeric: tabular-nums; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.4s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
