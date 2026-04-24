<template>
  <div class="max-w-7xl mx-auto px-4 py-4 pb-12 grid grid-cols-12 gap-4">

    <!-- ── LINKE SPALTE: Startliste ── -->
    <aside class="col-span-3 space-y-3">
      <!-- Klassen-Auswahl -->
      <select v-model="selectedClassId" @change="loadClass" class="input font-semibold">
        <option v-for="c in store.classes" :key="c.id" :value="c.id">
          {{ c.name }}
        </option>
      </select>

      <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500 px-1">Startliste</h2>

      <!-- Aktueller Fahrer -->
      <div v-if="currentParticipant" class="bg-msc-blue text-white rounded-xl p-3 shadow-md">
        <div class="flex items-center justify-between mb-1">
          <span class="text-3xl font-black">#{{ currentParticipant.start_number }}</span>
          <span class="bg-white/20 text-xs rounded px-2 py-0.5 font-mono">→ JETZT</span>
        </div>
        <div class="font-bold text-lg leading-tight">
          {{ currentParticipant.first_name }} {{ currentParticipant.last_name }}
        </div>
        <div class="text-blue-200 text-sm">{{ currentParticipant.club_name || 'n.N.' }}</div>
      </div>
      <div v-else class="bg-gray-100 rounded-xl p-3 text-center text-gray-400 text-sm">
        Kein Fahrer ausgewählt
      </div>

      <!-- Warteschlange -->
      <div class="space-y-1.5">
        <div class="flex items-center justify-between px-1">
          <span class="text-xs text-gray-400 font-semibold uppercase tracking-widest">Nächste Starter</span>
          <button v-if="manualOrder.length" @click="manualOrder = []"
            class="text-xs text-orange-600 hover:text-orange-700 font-bold transition">
            ↺ Reihenfolge zurücksetzen
          </button>
        </div>
        <div
          v-for="(p, i) in queue.slice(1, 7)"
          :key="p.id"
          class="bg-white rounded-lg px-3 py-2 flex items-center gap-2 shadow-sm border transition"
          :class="i === 0 ? 'border-blue-200 bg-blue-50/40' : 'border-gray-100'"
        >
          <span class="text-xl font-black text-gray-700 w-8 shrink-0">#{{ p.start_number }}</span>
          <div class="flex-1 min-w-0">
            <div class="font-semibold text-sm text-gray-800 truncate">
              {{ p.first_name }} {{ p.last_name }}
            </div>
            <div class="text-xs text-gray-400">{{ p.club_name || 'n.N.' }}</div>
          </div>
          <div class="flex flex-col items-end gap-0.5 shrink-0">
            <span class="text-xs text-gray-400 font-mono">{{ i + 2 }}.</span>
            <button
              @click="pullForward(p)"
              class="text-xs text-msc-blue hover:text-msc-bluedark font-bold leading-none transition"
              title="Als nächsten starten lassen"
            >↑ Vorziehen</button>
          </div>
        </div>
        <div v-if="queue.length <= 1" class="text-xs text-gray-400 text-center py-2">
          Alle Fahrer abgeschlossen
        </div>
      </div>
    </aside>

    <!-- ── MITTE: Eingabe ── -->
    <section class="col-span-6 space-y-4">

      <!-- Status-Banner: Klasse noch nicht gestartet / offiziell -->
      <div v-if="classBlockReason" class="rounded-xl px-4 py-3 flex items-center gap-3 text-sm font-semibold"
           :class="selectedClass?.run_status === 'official'
             ? 'bg-green-100 text-green-800 border border-green-300'
             : 'bg-amber-100 text-amber-800 border border-amber-300'">
        <span class="text-xl">{{ selectedClass?.run_status === 'official' ? '✓' : '⚠' }}</span>
        {{ classBlockReason }}
      </div>

      <!-- Zeit-Eingabe -->
      <div class="card p-5">
        <div class="flex items-center justify-between mb-3">
          <h2 class="font-bold text-gray-700 text-sm uppercase tracking-widest">
            <span v-if="currentParticipant">
              #{{ currentParticipant.start_number }} · {{ currentParticipant.first_name }} {{ currentParticipant.last_name }}
            </span>
            <span v-else class="text-gray-400">Kein Fahrer</span>
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
            <span v-if="lsFlash" class="ml-auto text-green-600 font-bold">
              ⚡ Zeit eingetragen
            </span>
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
              class="w-full text-center border-2 rounded-xl px-4 py-3 text-6xl font-black tabnum focus:outline-none focus:ring-4 bg-blue-50/30 transition-colors duration-300"
              :class="lsFlash
                ? 'border-green-500 ring-4 ring-green-200 bg-green-50/30 text-green-700'
                : 'border-msc-blue focus:ring-blue-200 text-msc-blue'"
              @keydown.enter.prevent="confirm"
            >
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 text-lg font-semibold">s</span>
          </div>
          <div class="text-right text-sm text-gray-500 shrink-0 w-24">
            <div>Strafen:</div>
            <div class="font-bold text-msc-red text-xl tabnum">+ {{ totalPenalties.toFixed(1) }} s</div>
            <div class="border-t border-gray-200 pt-1 mt-1">Gesamt:</div>
            <div class="font-black text-gray-800 text-xl tabnum">
              {{ totalTime !== null ? totalTime.toFixed(2) + ' s' : '–' }}
            </div>
          </div>
        </div>

        <!-- Aktive Strafen -->
        <div class="flex flex-wrap gap-1.5 min-h-8 mb-3 p-2 bg-gray-50 rounded-lg border border-gray-200">
          <span
            v-for="(pen, i) in activePenalties"
            :key="i"
            class="flex items-center gap-1 bg-msc-red text-white text-xs font-bold rounded-full px-2.5 py-1"
          >
            {{ pen.label }} ×{{ pen.count }}
            <button @click="removePenalty(i)" class="ml-1 hover:text-red-200">✕</button>
          </span>
          <span v-if="activePenalties.length === 0" class="text-xs text-gray-400 self-center ml-1">
            Keine Strafen
          </span>
          <span v-else class="text-xs text-gray-400 self-center ml-1">
            = {{ totalPenalties.toFixed(1) }} s
          </span>
        </div>

        <!-- Bestätigen / Undo -->
        <div class="flex gap-2">
          <button
            @click="confirm"
            :disabled="!currentParticipant || (!rawTime && resultStatus === 'valid') || !!classBlockReason"
            class="flex-1 btn-primary py-3 text-lg disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <span>✓ Bestätigen</span>
            <span class="bg-white/20 text-xs rounded px-1.5 py-0.5 font-mono">Enter</span>
          </button>
          <button
            @click="undo"
            :disabled="history.length === 0"
            class="px-4 py-3 btn-secondary disabled:opacity-40 flex items-center gap-1.5"
          >
            ↩ Undo
            <span class="bg-gray-200 text-xs rounded px-1.5 py-0.5 font-mono">Ctrl+Z</span>
          </button>
        </div>

        <!-- Lauf-Anzeige + manueller Override -->
        <div class="flex items-center gap-3 mt-3 pt-3 border-t border-gray-100">
          <div class="shrink-0">
            <div class="text-xs text-gray-400 leading-none mb-0.5">Aktueller Lauf</div>
            <div class="text-base font-black text-msc-blue leading-none">
              {{ selectedRun === 0 ? 'Training' : 'Lauf ' + selectedRun }}
            </div>
          </div>
          <div class="flex-1 flex items-center gap-1 justify-end">
            <span class="text-xs text-gray-400 mr-0.5">Override:</span>
            <button
              v-for="n in runNumbers"
              :key="n"
              @click="changeRun(n)"
              class="px-2 py-0.5 rounded text-xs font-bold transition border"
              :class="selectedRun === n
                ? 'bg-msc-blue/15 text-msc-blue border-msc-blue/40'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-500 border-transparent'"
            >
              {{ n === 0 ? 'Tr.' : 'L' + n }}
            </button>
          </div>
        </div>
      </div>

      <!-- Straf-Buttons -->
      <div class="card p-4">
        <h2 class="font-bold text-gray-700 text-xs uppercase tracking-widest mb-3">
          Strafen · {{ currentReglement?.name || '–' }}
        </h2>
        <div v-if="penalties.length === 0" class="text-sm text-gray-400">
          Kein Reglement / keine Strafen definiert.
        </div>
        <div class="grid grid-cols-3 gap-2">
          <button
            v-for="pen in penalties"
            :key="pen.id"
            @click="addPenalty(pen)"
            class="relative bg-red-50 hover:bg-msc-red hover:text-white border-2 border-red-200 hover:border-msc-red rounded-xl p-3 text-left transition group active:scale-95"
            :class="{ 'col-span-2': pen.sort_order >= 99 }"
          >
            <div class="text-xs opacity-55 font-semibold mb-1 group-hover:opacity-70">
              {{ pen.shortcut_key ? 'Taste: ' + pen.shortcut_key : '' }}
            </div>
            <div class="font-bold text-sm text-gray-800 group-hover:text-white">{{ pen.label }}</div>
            <div class="text-xs text-gray-500 group-hover:text-white/80">+ {{ pen.seconds.toFixed(1) }} s</div>
          </button>
        </div>
      </div>
    </section>

    <!-- ── RECHTE SPALTE: Ergebnisse ── -->
    <aside class="col-span-3 space-y-3">
      <div class="flex items-center justify-between px-1">
        <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500">
          Lauf {{ selectedRun === 0 ? 'Training' : selectedRun }} – Ergebnisse
        </h2>
        <span class="text-xs text-gray-400">{{ runResults.length }}</span>
      </div>

      <div class="card overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-msc-blue text-white text-xs">
              <th class="py-2 px-2 text-left font-semibold">#</th>
              <th class="py-2 px-2 text-left font-semibold">Fahrer</th>
              <th class="py-2 px-2 text-right font-semibold">Zeit</th>
              <th class="py-2 px-2 text-right font-semibold">Ges.</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="r in runResults"
              :key="r.result_id"
              class="border-b border-gray-50 even:bg-gray-50/50"
              :class="{ 'bg-blue-50': r.participant_id === currentParticipant?.id }"
            >
              <td class="py-2 px-2 font-black text-gray-600">{{ r.start_number }}</td>
              <td class="py-2 px-2">
                <div class="font-semibold text-gray-800 text-xs">
                  {{ r.first_name[0] }}. {{ r.last_name }}
                </div>
                <div class="text-gray-400" style="font-size:10px">{{ r.club }}</div>
              </td>
              <td class="py-2 px-2 text-right font-mono text-xs text-gray-600">
                <span v-if="r.status === 'valid' && r.raw_time !== null">{{ r.raw_time.toFixed(2) }}</span>
                <span v-else class="badge-warn">{{ r.status.toUpperCase() }}</span>
              </td>
              <td class="py-2 px-2 text-right font-mono font-bold text-xs">
                <span v-if="r.total_time !== null" :class="r.total_penalties > 0 ? 'text-msc-red' : 'text-gray-800'">
                  {{ r.total_time.toFixed(2) }}
                </span>
                <span v-else class="text-gray-300">–</span>
              </td>
            </tr>
            <tr v-if="runResults.length === 0">
              <td colspan="4" class="py-4 text-center text-xs text-gray-400">Noch keine Ergebnisse</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Klassen-Status -->
      <div class="card p-3 space-y-1.5">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Klassen-Status</h3>
        <div
          v-for="c in store.classes"
          :key="c.id"
          class="flex items-center justify-between text-xs"
        >
          <span :class="c.id === selectedClassId ? 'font-semibold text-msc-blue' : 'text-gray-600'">
            {{ c.name }}
          </span>
          <span
            class="font-bold rounded px-1.5 py-0.5"
            :class="{
              'bg-green-100 text-green-700': c.run_status === 'official',
              'bg-msc-blue/10 text-msc-blue': c.run_status === 'running',
              'bg-amber-100 text-amber-700': c.run_status === 'preliminary',
              'bg-gray-100 text-gray-500': c.run_status === 'planned',
            }"
          >
            {{ statusLabel(c.run_status) }}
          </span>
        </div>
      </div>
    </aside>

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
const rawTime          = ref('')
const resultStatus     = ref('valid')
const activePenalties  = ref([])  // [{ id, label, seconds, count }]
const penalties        = ref([])
const participants     = ref([])
const runResults       = ref([])
const allClassResults  = ref([])   // alle Läufe der Klasse (für Auto-Advance)
const history          = ref([])  // für Undo
const currentReglement = ref(null)
const timeInput        = ref(null)
const manualOrder      = ref([])  // participant IDs in user-defined sequence

// ── Lichtschranke / Timing-Device ─────────────────────────────────────────────
const lsConnected = ref(false)   // Raspi aktuell verbunden
const lsFlash     = ref(false)   // kurzes Aufleuchten wenn Zeit ankommt
let lsFlashTimer  = null

function handleWsMessage(data) {
  if (data.type === 'timing_device_status') {
    lsConnected.value = data.connected
  }
  if (data.type === 'timing_device_heartbeat') {
    lsConnected.value = true
  }
  if (data.type === 'timing_result' && typeof data.raw_time === 'number') {
    rawTime.value      = data.raw_time.toFixed(2)
    resultStatus.value = 'valid'
    lsFlash.value      = true
    clearTimeout(lsFlashTimer)
    lsFlashTimer = setTimeout(() => { lsFlash.value = false }, 1800)
    timeInput.value?.focus()
  }
  // Reload results if another client confirmed a result
  if (data.type === 'results' && data.class_id === selectedClassId.value) {
    loadRunResults()
  }
}

useRealtimeUpdate(handleWsMessage)

const selectedClass = computed(() =>
  store.classes.find(c => c.id === selectedClassId.value) || null
)

// null = OK; string = Grund warum Eingabe gesperrt
const classBlockReason = computed(() => {
  const cls = selectedClass.value
  if (!cls) return null
  if (cls.is_exhibition) return null
  if (cls.run_status === 'official')
    return 'Klasse ist offiziell freigegeben – keine Zeiteingaben mehr möglich.'
  if (cls.run_status === 'planned')
    return 'Klasse noch nicht gestartet – bitte Schiedsrichter den Start bestätigen lassen.'
  if (cls.run_status === 'preliminary')
    return 'Klasse abgeschlossen (vorläufig) – keine neuen Zeiteingaben.'
  return null  // running / paused → OK
})

const runNumbers = computed(() => {
  const reg = currentReglement.value
  if (!reg) return [1]
  const nums = []
  if (reg.has_training) nums.push(0)
  for (let i = 1; i <= reg.runs_per_class; i++) nums.push(i)
  return nums
})

// Fahrerliste — pending vor done; pending kann per manualOrder umsortiert werden
const queue = computed(() => {
  if (!participants.value.length) return []
  const doneIds = new Set(runResults.value.map(r => r.participant_id))
  const done    = participants.value.filter(p =>  doneIds.has(p.id))
  let   pending = participants.value.filter(p => !doneIds.has(p.id))

  if (manualOrder.value.length) {
    const rank = new Map(manualOrder.value.map((id, i) => [id, i]))
    pending = [...pending].sort((a, b) => {
      const ra = rank.has(a.id) ? rank.get(a.id) : Infinity
      const rb = rank.has(b.id) ? rank.get(b.id) : Infinity
      return ra !== rb ? ra - rb : (a.start_number ?? 9999) - (b.start_number ?? 9999)
    })
  } else {
    pending = [...pending].sort((a, b) => (a.start_number ?? 9999) - (b.start_number ?? 9999))
  }
  return [...pending, ...done]
})

// Einen Fahrer ganz nach vorne ziehen (wird sofort als nächster angezeigt)
function pullForward(p) {
  const doneIds = new Set(runResults.value.map(r => r.participant_id))
  const pending = queue.value.filter(pp => !doneIds.has(pp.id))
  manualOrder.value = [p.id, ...pending.filter(pp => pp.id !== p.id).map(pp => pp.id)]
}

const currentParticipant = computed(() => queue.value[0] || null)

const totalPenalties = computed(() =>
  activePenalties.value.reduce((s, p) => s + p.seconds * p.count, 0)
)

const totalTime = computed(() => {
  const t = parseFloat(rawTime.value)
  if (isNaN(t) || resultStatus.value !== 'valid') return null
  return t + totalPenalties.value
})

// Ermittelt automatisch den aktuellen Lauf (erster Lauf, der noch nicht alle Fahrer hat)
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

// Strafen laden wenn Klasse gewechselt
async function loadClass() {
  if (!selectedClassId.value || !store.activeEvent) return
  manualOrder.value = []
  const eid = store.activeEvent.id
  const cid = selectedClassId.value
  const cls = store.classes.find(c => c.id === cid)
  const regId = cls?.reglement_id
  if (regId) {
    const [regRes, penRes] = await Promise.all([
      api.get(`/reglements/${regId}`),
      api.get(`/reglements/${regId}/penalties`)
    ])
    currentReglement.value = regRes.data
    penalties.value = penRes.data
  } else {
    currentReglement.value = null
    penalties.value = []
  }
  const [partRes, allRes] = await Promise.all([
    api.get(`/events/${eid}/participants`),
    api.get(`/events/${eid}/run-results`, { params: { class_id: cid } }),
  ])
  participants.value = partRes.data.filter(p => p.class_id === cid)
  allClassResults.value = allRes.data
  selectedRun.value = computeAutoRun()
  await loadRunResults()
  resetInput()
}

async function loadRunResults() {
  if (!store.activeEvent || !selectedClassId.value) return
  const { data } = await api.get(`/events/${store.activeEvent.id}/run-results`, {
    params: { class_id: selectedClassId.value, run_number: selectedRun.value }
  })
  runResults.value = data
}

async function changeRun(n) {
  selectedRun.value = n
  manualOrder.value = []
  await loadRunResults()
}

function resetInput() {
  rawTime.value = ''
  resultStatus.value = 'valid'
  activePenalties.value = []
  timeInput.value?.focus()
}

function addPenalty(pen) {
  const existing = activePenalties.value.find(p => p.id === pen.id)
  if (existing) existing.count++
  else activePenalties.value.push({ id: pen.id, label: pen.label, seconds: pen.seconds, count: 1 })
}

function removePenalty(index) {
  const pen = activePenalties.value[index]
  if (pen.count > 1) pen.count--
  else activePenalties.value.splice(index, 1)
}

function setStatus(s) {
  resultStatus.value = s
  if (s !== 'valid') rawTime.value = ''
}

async function confirm() {
  if (!currentParticipant.value || !store.activeEvent) return
  const p  = currentParticipant.value
  const rt = resultStatus.value === 'valid' ? parseFloat(rawTime.value) : null

  try {
    const { data: result } = await api.post(
      `/events/${store.activeEvent.id}/results`,
      {
        event_id: store.activeEvent.id,
        participant_id: p.id,
        class_id: selectedClassId.value,
        run_number: selectedRun.value,
        raw_time: isNaN(rt) ? null : rt,
        status: resultStatus.value,
      }
    )
    // Strafen eintragen
    for (const pen of activePenalties.value) {
      await api.post(
        `/events/${store.activeEvent.id}/results/${result.id}/penalties`,
        { result_id: result.id, penalty_definition_id: pen.id, count: pen.count }
      )
    }
    // Undo-Stack
    history.value.push({ resultId: result.id, participantId: p.id })
    // Alle Ergebnisse neu laden und ggf. Lauf automatisch wechseln
    const { data: allRes } = await api.get(
      `/events/${store.activeEvent.id}/run-results`,
      { params: { class_id: selectedClassId.value } }
    )
    allClassResults.value = allRes
    const ar = computeAutoRun()
    if (ar !== selectedRun.value) {
      selectedRun.value = ar
      manualOrder.value = []
    }
    await loadRunResults()
    resetInput()
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler beim Speichern')
  }
}

async function undo() {
  const last = history.value.pop()
  if (!last || !store.activeEvent) return
  // Ergebnis löschen ist nicht direkt vorgesehen — Status auf DSQ setzen als Notlösung
  // In echter Implementierung: DELETE /results/{id}
  await loadRunResults()
}

// Keyboard shortcuts
function onKey(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
    return  // Enter auf dem Zeitfeld wird per @keydown.enter im Template behandelt
  }
  if (e.ctrlKey && e.key === 'z') { undo(); return }
  const pen = penalties.value.find(p => p.shortcut_key === e.key.toUpperCase())
  if (pen) addPenalty(pen)
}

onMounted(async () => {
  if (store.classes.length) {
    selectedClassId.value = store.classes[0].id
    await loadClass()
  }
  window.addEventListener('keydown', onKey)
})

onUnmounted(() => window.removeEventListener('keydown', onKey))

watch(rawTime, (val) => {
  if (typeof val === 'string' && val.includes(','))
    rawTime.value = val.replace(/,/g, '.')
})

watch(() => store.classes, async (v) => {
  if (v.length && !selectedClassId.value) {
    selectedClassId.value = v[0].id
    await loadClass()
  }
})

function statusLabel(s) {
  return { planned: 'Geplant', running: 'Läuft', paused: 'Unterbrochen', preliminary: 'Vorläufig', official: 'Offiziell' }[s] || s
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.4s ease; }
.fade-enter-from, .fade-leave-to       { opacity: 0; }
</style>
