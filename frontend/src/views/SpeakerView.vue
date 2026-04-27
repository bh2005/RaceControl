<template>
  <div class="min-h-screen bg-gray-950 text-white flex flex-col">

    <!-- Header / Steuerung -->
    <header class="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-4 flex-wrap">
      <img src="/msc-logo.svg" alt="MSC" class="h-8 w-8 rounded-full border border-white/20 shrink-0">
      <span class="font-black text-lg tracking-tight text-white shrink-0">Sprecher-Dashboard</span>

      <select v-model="selectedClassId" @change="onClassChange"
        class="bg-gray-800 border border-gray-600 rounded-lg px-3 py-1.5 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-cyan-500">
        <option v-for="c in store.classes" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>

      <!-- Lauf-Anzeige: automatisch erkannt, manueller Override möglich -->
      <div class="flex items-center gap-2">
        <span class="text-sm font-black text-white">{{ runLabel }}</span>
        <div class="flex gap-1">
          <button v-if="currentReglement?.has_training"
            @click="selectedRun = 0; loadData()"
            class="text-xs px-2 py-0.5 rounded font-bold transition border"
            :class="selectedRun === 0
              ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
              : 'bg-gray-700 text-gray-400 border-transparent hover:bg-gray-600'">
            Tr.
          </button>
          <button v-for="n in runNums" :key="n"
            @click="selectedRun = n; loadData()"
            class="text-xs px-2 py-0.5 rounded font-bold transition border"
            :class="selectedRun === n
              ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
              : 'bg-gray-700 text-gray-400 border-transparent hover:bg-gray-600'">
            L{{ n }}
          </button>
        </div>
      </div>

      <span class="flex items-center gap-1.5 text-xs font-bold rounded-full px-2.5 py-1 border ml-auto"
        :class="wsConnected
          ? 'bg-green-500/20 text-green-300 border-green-500/30'
          : 'bg-gray-600/20 text-gray-400 border-gray-600/30'">
        <span class="h-2 w-2 rounded-full"
          :class="wsConnected ? 'bg-green-400 animate-pulse' : 'bg-gray-500'"></span>
        {{ wsConnected ? 'LIVE' : 'Offline' }}
      </span>
    </header>

    <!-- Main Content -->
    <div class="flex-1 grid grid-cols-12 gap-6 p-6 max-w-screen-2xl mx-auto w-full">

      <!-- Linke Spalte: Aktueller Fahrer -->
      <div class="col-span-5 flex flex-col gap-4">

        <!-- Aktueller Fahrer - Hauptbox -->
        <div class="bg-gray-900 rounded-2xl border border-gray-700 p-6 flex flex-col gap-2">
          <div class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-1">
            Jetzt am Start · {{ runLabel }}
          </div>

          <div v-if="currentDriver" class="space-y-1">
            <div class="flex items-baseline gap-4">
              <span class="font-black text-cyan-400" style="font-size: 6rem; line-height: 1;">
                #{{ currentDriver.start_number }}
              </span>
            </div>
            <div class="font-black text-white" style="font-size: 2.8rem; line-height: 1.1;">
              {{ currentDriver.first_name }}<br>{{ currentDriver.last_name }}
            </div>
            <div class="text-gray-400 text-xl mt-2">{{ currentDriver.club_name || 'n.N.' }}</div>

            <!-- Bisherige Läufe -->
            <div v-if="driverPrevRuns.length" class="mt-4 space-y-1">
              <div class="text-xs font-bold uppercase tracking-widest text-gray-600 mb-1">Bisherige Läufe</div>
              <div v-for="run in driverPrevRuns" :key="run.run_number"
                   class="flex items-center gap-3 text-sm font-mono">
                <span class="text-gray-500 w-16">
                  {{ run.run_number === 0 ? 'Training' : 'Lauf ' + run.run_number }}
                </span>
                <span class="text-white font-bold">{{ run.raw_time?.toFixed(2) }}</span>
                <span :class="run.total_penalties > 0 ? 'text-red-400 font-bold' : 'text-gray-600'">
                  +{{ run.total_penalties.toFixed(1) }}s
                </span>
                <span v-if="run.total_time" class="text-cyan-300 font-black">
                  = {{ run.total_time.toFixed(2) }}
                </span>
              </div>
              <div class="pt-1 border-t border-gray-800 flex items-center gap-2 text-sm font-mono">
                <span class="text-gray-500 w-16">Teilsumme</span>
                <span class="text-cyan-400 font-black text-lg">{{ driverPartial.toFixed(2) }}s</span>
              </div>
            </div>
          </div>

          <div v-else class="text-gray-600 text-2xl font-bold py-8 text-center">
            Warten auf Fahrer…
          </div>
        </div>

        <!-- Marshal-Meldungen -->
        <TransitionGroup name="marshal-list" tag="div" class="space-y-2">
          <div
            v-for="m in marshalNotices"
            :key="m._id"
            class="bg-yellow-500/10 border border-yellow-500/30 rounded-xl px-4 py-3 flex items-center gap-3"
          >
            <span class="text-yellow-400 text-xl shrink-0">🚩</span>
            <div class="flex-1 min-w-0">
              <span class="font-black text-yellow-300">{{ m.penalty_label }}</span>
              <span class="text-yellow-500 font-semibold ml-2">+{{ m.penalty_seconds.toFixed(0) }}s</span>
              <span class="text-gray-500 text-xs ml-2">{{ m.station }}</span>
            </div>
            <button @click="dismissMarshal(m)" class="text-gray-600 hover:text-gray-400 text-sm">✕</button>
          </div>
        </TransitionGroup>

        <!-- Startnummern-Warteschlange -->
        <div class="bg-gray-900 rounded-2xl border border-gray-700 p-4">
          <div class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">Nächste Starter</div>
          <div class="flex flex-wrap gap-2">
            <span v-for="(p, i) in nextDrivers" :key="p.id"
                  class="rounded-xl px-3 py-1.5 text-sm font-bold"
                  :class="i === 0 ? 'bg-cyan-600 text-white' : 'bg-gray-800 text-gray-300'">
              #{{ p.start_number }} {{ p.first_name[0] }}. {{ p.last_name }}
            </span>
            <span v-if="nextDrivers.length === 0" class="text-gray-600 text-sm">Alle gefahren</span>
          </div>
        </div>
      </div>

      <!-- Rechte Spalte: Zeitanalyse -->
      <div class="col-span-7 flex flex-col gap-4">

        <!-- Zeitanalyse für aktuellen Fahrer -->
        <div class="bg-gray-900 rounded-2xl border border-gray-700 p-6" v-if="currentDriver && selectedRun > 0">
          <div class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-4">
            Zeitanalyse – was braucht {{ currentDriver.first_name }} {{ currentDriver.last_name }}?
          </div>

          <div v-if="timeTargets.length === 0" class="text-gray-600 text-sm">
            Noch keine Wertungszeiten vorhanden.
          </div>

          <div v-else class="space-y-3">
            <div v-for="t in timeTargets" :key="t.label"
                 class="rounded-xl p-4 flex items-center gap-4"
                 :class="t.impossible ? 'bg-gray-800/50 opacity-50' : t.rank <= 3 ? 'bg-gray-800' : 'bg-gray-800/60'">

              <!-- Rang-Badge -->
              <div class="shrink-0 h-12 w-12 rounded-full flex items-center justify-center font-black text-xl"
                   :class="{
                     'bg-yellow-500/20 text-yellow-300': t.rank === 1,
                     'bg-slate-400/20 text-slate-300':  t.rank === 2,
                     'bg-amber-700/20 text-amber-400':  t.rank === 3,
                     'bg-gray-700 text-gray-400':        t.rank > 3,
                   }">
                {{ t.rank }}
              </div>

              <div class="flex-1">
                <div class="text-gray-400 text-xs font-semibold uppercase tracking-wide">{{ t.label }}</div>
                <div class="text-gray-300 text-xs mt-0.5">
                  {{ t.holderName }} · {{ t.holderTime.toFixed(2) }}s Gesamt
                </div>
              </div>

              <div class="text-right shrink-0">
                <div v-if="t.impossible" class="text-red-400 font-bold text-lg">nicht möglich</div>
                <template v-else>
                  <div class="font-black tabnum" style="font-size: 2rem; line-height: 1;"
                       :class="t.needed < 0 ? 'text-red-400' : 'text-cyan-300'">
                    {{ t.needed.toFixed(2) }}<span class="text-base font-normal text-gray-500">s</span>
                  </div>
                  <!-- Pylonen-Budget -->
                  <div v-if="mainPenalty && t.needed > 0" class="text-xs text-gray-500 mt-1">
                    bis {{ Math.floor(t.needed / mainPenalty) }}× Pylone (à {{ mainPenalty }}s)
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- Aktuelle Wertung -->
        <div class="bg-gray-900 rounded-2xl border border-gray-700 p-4 flex-1">
          <div class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">
            {{ selectedRun === 0 ? 'Training' : 'Aktuelle Wertung' }} · {{ selectedClass?.name }}
          </div>
          <div class="space-y-1">
            <div v-for="(row, i) in topStandings" :key="row.participant_id || row.start_number"
                 class="flex items-center gap-3 rounded-lg px-3 py-2"
                 :class="{
                   'bg-yellow-500/10 border border-yellow-500/20': i === 0,
                   'bg-gray-800/60': i > 0,
                   'ring-1 ring-cyan-500': row.start_number === currentDriver?.start_number,
                 }">
              <span class="font-black text-sm w-5 text-center"
                    :class="i === 0 ? 'text-yellow-300' : i === 1 ? 'text-slate-400' : i === 2 ? 'text-amber-600' : 'text-gray-500'">
                {{ row.rank }}
              </span>
              <span class="font-bold text-sm text-gray-300 w-8">#{{ row.start_number }}</span>
              <span class="font-semibold text-sm flex-1 truncate"
                    :class="row.start_number === currentDriver?.start_number ? 'text-cyan-300' : 'text-white'">
                {{ row.first_name }} {{ row.last_name }}
              </span>
              <span class="font-black tabnum text-sm" :class="i === 0 ? 'text-yellow-300' : 'text-white'">
                {{ row.total_time?.toFixed(2) ?? '–' }}
              </span>
              <span v-if="i > 0 && row.total_time && topStandings[0]?.total_time"
                    class="text-xs tabnum text-gray-500 w-14 text-right shrink-0">
                +{{ (row.total_time - topStandings[0].total_time).toFixed(2) }}s
              </span>
              <span v-else class="w-14 shrink-0"></span>
            </div>
          </div>
          <div v-if="standings.length > 10" class="text-xs text-gray-600 text-center mt-2">
            + {{ standings.length - 10 }} weitere
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'
import { useRealtimeUpdate } from '../composables/useRealtimeUpdate'

const store = useEventStore()

const selectedClassId  = ref(null)
const selectedRun      = ref(1)
const standings        = ref([])
const runResults       = ref([])
const allClassResults  = ref([])
const participants     = ref([])
const currentReglement = ref(null)
const penalties        = ref([])

// ── Marshal-Meldungen ─────────────────────────────────────────────────────────
const marshalNotices   = ref([])
let _marshalSeq        = 0
const _marshalTimers   = new Map()

function dismissMarshal(m) {
  clearTimeout(_marshalTimers.get(m._id))
  _marshalTimers.delete(m._id)
  marshalNotices.value = marshalNotices.value.filter(x => x._id !== m._id)
}

// ── Ereignis-Log ─────────────────────────────────────────────────────────────
const announcementLog = ref([])   // newest first
let _logSeq = 0

function _fmtTime(iso) {
  const d = iso ? new Date(iso) : new Date()
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function addLogEntry(icon, text, level = 'info', isoTs = null) {
  announcementLog.value.unshift({ _id: ++_logSeq, icon, text, level, timeStr: _fmtTime(isoTs) })
  if (announcementLog.value.length > 50) announcementLog.value.pop()
}

function _classStatusIcon(s) {
  return { running: '🟢', paused: '⏸️', preliminary: '🏁', official: '✅', planned: '🔄' }[s] ?? '📋'
}
function _classStatusText(s) {
  return {
    running:     'Klasse gestartet',
    paused:      'Unterbrochen',
    preliminary: 'Vorläufiges Ergebnis',
    official:    'Offiziell freigegeben',
    planned:     'Zurückgesetzt',
  }[s] ?? s
}

const runNums = computed(() => {
  const n = currentReglement.value?.runs_per_class ?? 2
  return Array.from({ length: n }, (_, i) => i + 1)
})

const runLabel = computed(() =>
  selectedRun.value === 0 ? 'Training' : `Lauf ${selectedRun.value}`
)

const selectedClass = computed(() =>
  store.classes.find(c => c.id === selectedClassId.value) || null
)

const mainPenalty = computed(() => {
  if (!penalties.value.length) return null
  return Math.min(...penalties.value.map(p => p.seconds))
})

// Wer hat den aktuellen Lauf noch NICHT absolviert → pending queue
const queue = computed(() => {
  const doneIds = new Set(runResults.value.map(r => r.participant_id))
  return participants.value
    .filter(p => !doneIds.has(p.id))
    .sort((a, b) => (a.start_number ?? 9999) - (b.start_number ?? 9999))
})

const currentDriver  = computed(() => queue.value[0] || null)
const nextDrivers    = computed(() => queue.value.slice(0, 8))

// Bisherige Läufe des aktuellen Fahrers (run_number < selectedRun)
const driverPrevRuns = computed(() => {
  if (!currentDriver.value) return []
  // All run-results endpoint returns all runs for the class
  return allRunResults.value
    .filter(r =>
      r.participant_id === currentDriver.value.id &&
      r.run_number > 0 &&
      r.run_number < selectedRun.value &&
      r.status === 'valid'
    )
    .sort((a, b) => a.run_number - b.run_number)
})

const driverPartial = computed(() =>
  driverPrevRuns.value.reduce((s, r) => s + (r.total_time ?? 0), 0)
)

const allRunResults = ref([])  // alle Läufe der Klasse (nicht nur aktueller Lauf)

const topStandings = computed(() => {
  if (selectedRun.value === 0) {
    return [...allClassResults.value]
      .filter(r => r.run_number === 0 && r.status === 'valid' && r.raw_time !== null)
      .sort((a, b) => (a.raw_time ?? 9999) - (b.raw_time ?? 9999))
      .slice(0, 10)
      .map((r, i) => ({ ...r, total_time: r.raw_time, rank: i + 1 }))
  }
  return standings.value.slice(0, 10)
})

// Zeitanalyse: welche Zeiten braucht der Fahrer für Pn?
const timeTargets = computed(() => {
  if (!currentDriver.value || standings.value.length === 0) return []
  const partial = driverPartial.value
  const targets = [1, 3, 10]
  return targets
    .map(rank => {
      const idx = rank - 1
      if (idx >= standings.value.length) return null
      const holder = standings.value[idx]
      if (!holder.total_time) return null
      const isCurrentDriver = holder.start_number === currentDriver.value.start_number
      // Wenn der Fahrer selbst diese Position hat: zeige nicht doppelt
      if (isCurrentDriver && driverPrevRuns.value.length > 0) return null
      const needed = holder.total_time - partial
      return {
        rank,
        label: rank === 1 ? '🥇 Platz 1 schlagen' : rank === 3 ? '🥉 Top 3 erreichen' : `Top ${rank} erreichen`,
        holderName: `${holder.first_name} ${holder.last_name}`,
        holderTime: holder.total_time,
        needed,
        impossible: needed <= 0,
      }
    })
    .filter(Boolean)
})

function computeAutoRun() {
  const reg = currentReglement.value
  if (!reg || !participants.value.length) return selectedRun.value
  const nums = []
  if (reg.has_training) nums.push(0)
  for (let i = 1; i <= reg.runs_per_class; i++) nums.push(i)
  for (const rn of nums) {
    const done = new Set(allClassResults.value.filter(r => r.run_number === rn).map(r => r.participant_id))
    if (done.size < participants.value.length) return rn
  }
  return nums[nums.length - 1]
}

async function loadData() {
  if (!store.activeEvent || !selectedClassId.value) return
  const eid = store.activeEvent.id
  const cid = selectedClassId.value

  const [stRes, rrAllRes, partRes] = await Promise.all([
    api.get(`/events/${eid}/standings`, { params: { class_id: cid } }),
    api.get(`/events/${eid}/run-results`, { params: { class_id: cid } }),
    api.get(`/events/${eid}/participants`),
  ])

  participants.value   = partRes.data.filter(p => p.class_id === cid)
  allClassResults.value = rrAllRes.data
  allRunResults.value  = rrAllRes.data
  standings.value      = stRes.data

  // Auto-advance: nächsten unvollständigen Lauf wählen
  const ar = computeAutoRun()
  if (ar !== selectedRun.value) selectedRun.value = ar

  // Ergebnisse des aktuellen Laufs laden
  const rrRes = await api.get(`/events/${eid}/run-results`, {
    params: { class_id: cid, run_number: selectedRun.value }
  })
  runResults.value = rrRes.data
}

async function onClassChange() {
  const cls = selectedClass.value
  if (!cls) return
  allClassResults.value = []
  participants.value = []
  const regId = cls.reglement_id
  if (regId) {
    const [regRes, penRes] = await Promise.all([
      api.get(`/reglements/${regId}`),
      api.get(`/reglements/${regId}/penalties`),
    ])
    currentReglement.value = regRes.data
    penalties.value = penRes.data
  } else {
    currentReglement.value = null
    penalties.value = []
  }
  await loadData()
}

const { connected: wsConnected } = useRealtimeUpdate(async (msg) => {
  if (!store.activeEvent) return
  if (msg.event_id && msg.event_id !== store.activeEvent.id) return

  if (msg.type === 'results') {
    await loadData()
  }

  if (msg.type === 'classes') {
    const prevStatus = store.classes.find(c => c.id === msg.class_id)?.run_status
    await store.selectEvent(store.activeEvent)  // refresh store.classes
    await loadData()
    const cls = store.classes.find(c => c.id === msg.class_id)
    if (cls && prevStatus !== undefined && prevStatus !== cls.run_status) {
      addLogEntry(_classStatusIcon(cls.run_status), `${cls.name}: ${_classStatusText(cls.run_status)}`, 'important')
    }
  }

  if (msg.type === 'notification') {
    addLogEntry('📢', msg.message, 'important')
  }

  if (msg.type === 'marshal_penalty') {
    // Show in real-time notice box only for current/unfiltered class
    if (msg.class_id == null || msg.class_id === selectedClassId.value) {
      const entry = { ...msg, _id: ++_marshalSeq }
      marshalNotices.value.push(entry)
      const t = setTimeout(() => dismissMarshal(entry), 30_000)
      _marshalTimers.set(entry._id, t)
    }
    const cls = msg.class_name ? ` (${msg.class_name})` : ''
    addLogEntry('🚩', `Posten ${msg.station}${cls}: ${msg.penalty_label}`, 'warn', msg.ts)
  }

  if (msg.type === 'marshal_cancel') {
    addLogEntry('↩️', `Storno – ${msg.marshal}`, 'info', msg.ts)
  }
})

onMounted(async () => {
  if (!store.classes.length) await store.loadEvents()
  if (store.classes.length) {
    // Bevorzuge laufende Klasse
    const running = store.classes.find(c => c.run_status === 'running')
    selectedClassId.value = (running ?? store.classes[0]).id
    await onClassChange()
  }
})

watch(() => store.classes, async (v) => {
  if (v.length && !selectedClassId.value) {
    selectedClassId.value = v[0].id
    await onClassChange()
  }
})

onUnmounted(() => _marshalTimers.forEach(t => clearTimeout(t)))
</script>

<style scoped>
.tabnum { font-variant-numeric: tabular-nums; }

.marshal-list-enter-active, .marshal-list-leave-active { transition: all 0.3s ease; }
.marshal-list-enter-from, .marshal-list-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
