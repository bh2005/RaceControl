<template>
  <div class="max-w-7xl mx-auto px-4 py-4 pb-12 grid grid-cols-12 gap-4">

    <!-- ── LINKE SPALTE: Klassen-Steuerung ── -->
    <aside class="col-span-3 space-y-3">
      <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500 px-1">Klassen-Steuerung</h2>

      <div
        v-for="c in store.classes" :key="c.id"
        class="card p-3 space-y-2"
        :class="{
          'border-2 border-amber-300 bg-amber-50': c.run_status === 'preliminary',
          'border-2 border-orange-400 bg-orange-50': c.run_status === 'paused',
        }"
      >
        <div class="flex items-center justify-between">
          <div class="font-semibold text-sm text-gray-800">{{ c.name }}</div>
          <span class="text-xs font-bold rounded-full px-2 py-0.5"
            :class="{
              'bg-green-100 text-green-700':   c.run_status === 'official',
              'bg-msc-blue/10 text-msc-blue':  c.run_status === 'running',
              'bg-orange-100 text-orange-700': c.run_status === 'paused',
              'bg-amber-100 text-amber-700':   c.run_status === 'preliminary',
              'bg-gray-100 text-gray-500':     c.run_status === 'planned',
            }">{{ statusLabel(c.run_status) }}</span>
        </div>

        <!-- Startzeit anzeigen falls gesetzt -->
        <div v-if="c.start_time" class="text-xs text-gray-500">
          Start: <span class="font-semibold">{{ c.start_time }}</span>
        </div>

        <!-- Protest-Timer für preliminary -->
        <div v-if="c.run_status === 'preliminary' && c.end_time" class="rounded-lg p-2 text-center"
             :class="protestExpired(c) ? 'bg-green-50 border border-green-200' : 'bg-amber-50 border border-amber-200'">
          <div class="text-xs font-bold uppercase tracking-widest mb-0.5"
               :class="protestExpired(c) ? 'text-green-600' : 'text-amber-700'">
            Einspruchfrist
          </div>
          <div v-if="!protestExpired(c)" class="font-black text-xl tabnum text-amber-700">
            {{ protestCountdown(c) }}
          </div>
          <div v-else class="font-bold text-sm text-green-600">Abgelaufen ✓</div>
          <div class="text-xs text-gray-400 mt-0.5">
            bis {{ protestDeadline(c) }}
          </div>
        </div>

        <!-- Aktions-Buttons je nach Status -->

        <!-- Geplant → Starten -->
        <button
          v-if="c.run_status === 'planned'"
          @click="startClass(c)"
          class="w-full bg-msc-blue hover:bg-msc-bluedark text-white text-xs font-bold py-1.5 rounded-lg transition"
        >▶ Klasse starten</button>

        <!-- Läuft → Unterbrechen + Beenden -->
        <template v-if="c.run_status === 'running'">
          <button
            @click="pauseClass(c)"
            class="w-full bg-orange-500 hover:bg-orange-600 text-white text-xs font-bold py-1.5 rounded-lg transition"
          >⏸ Unterbrechen</button>
          <button
            @click="finishClass(c)"
            class="w-full bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold py-1.5 rounded-lg transition"
          >⏹ Klasse beenden (Einspruchfrist starten)</button>
        </template>

        <!-- Unterbrochen → Fortsetzen + Beenden -->
        <template v-if="c.run_status === 'paused'">
          <div class="text-xs text-orange-700 font-semibold text-center bg-orange-100 rounded py-1">
            ⏸ Klasse unterbrochen
          </div>
          <button
            @click="resumeClass(c)"
            class="w-full bg-msc-blue hover:bg-msc-bluedark text-white text-xs font-bold py-1.5 rounded-lg transition"
          >▶ Fortsetzen</button>
          <button
            @click="finishClass(c)"
            class="w-full bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold py-1.5 rounded-lg transition"
          >⏹ Klasse beenden</button>
        </template>

        <!-- Preliminary → Offiziell (nur nach Ablauf der Einspruchfrist, oder mit Warnung) -->
        <div v-if="c.run_status === 'preliminary'">
          <button
            @click="approveClass(c)"
            class="w-full text-xs font-bold py-1.5 rounded-lg transition"
            :class="protestExpired(c)
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-gray-200 hover:bg-gray-300 text-gray-600'"
            :title="!protestExpired(c) ? 'Einspruchfrist läuft noch' : ''"
          >
            <span v-if="protestExpired(c)">✓ Klasse offiziell freigeben</span>
            <span v-else>Freigeben (Frist läuft noch…)</span>
          </button>
        </div>
      </div>

      <!-- Audit-Zähler -->
      <div class="card p-3">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2">Korrekturen heute</h3>
        <div class="flex justify-between text-sm">
          <span class="text-gray-600">Einträge gesamt</span>
          <span class="font-bold">{{ auditLog.length }}</span>
        </div>
      </div>
    </aside>

    <!-- ── MITTE: Ergebnisse + Korrektur ── -->
    <section class="col-span-6 space-y-4">

      <!-- Filter -->
      <div class="card p-3 flex gap-3">
        <select v-model="filterClass" @change="loadResults" class="flex-1 input">
          <option value="">Alle Klassen</option>
          <option v-for="c in store.classes" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <select v-model="filterRun" @change="loadResults" class="input w-32">
          <option value="">Alle Läufe</option>
          <option value="0">Training</option>
          <option value="1">Lauf 1</option>
          <option value="2">Lauf 2</option>
        </select>
      </div>

      <!-- Ergebnistabelle -->
      <div class="card overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-msc-blue text-white text-xs">
              <th class="py-2.5 px-3 text-left">Nr.</th>
              <th class="py-2.5 px-3 text-left">Fahrer</th>
              <th class="py-2.5 px-3 text-right">Rohzeit</th>
              <th class="py-2.5 px-3 text-right">Strafen</th>
              <th class="py-2.5 px-3 text-right">Gesamt</th>
              <th class="py-2.5 px-3 text-center">Status</th>
              <th class="py-2.5 px-3 text-center">Aktion</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="r in results" :key="r.result_id"
              class="hover:bg-blue-50 transition"
              :class="{ 'bg-blue-50 border-l-4 border-msc-blue': editing?.result_id === r.result_id }"
            >
              <td class="py-2.5 px-3 font-black text-gray-700">#{{ r.start_number }}</td>
              <td class="py-2.5 px-3">
                <span class="font-semibold text-gray-800">{{ r.first_name[0] }}. {{ r.last_name }}</span>
                <span class="text-gray-400 text-xs ml-1">{{ r.class_name }}</span>
              </td>
              <td class="py-2.5 px-3 text-right font-mono text-gray-700">
                {{ r.raw_time !== null ? r.raw_time.toFixed(2) : '–' }}
              </td>
              <td class="py-2.5 px-3 text-right font-mono font-bold"
                  :class="r.total_penalties > 0 ? 'text-msc-red' : 'text-gray-400'">
                +{{ r.total_penalties.toFixed(1) }}
              </td>
              <td class="py-2.5 px-3 text-right font-mono font-bold text-gray-800">
                {{ r.total_time !== null ? r.total_time.toFixed(2) : r.status.toUpperCase() }}
              </td>
              <td class="py-2.5 px-3 text-center">
                <span :class="r.is_official ? 'badge-ok' : 'badge-gray'">
                  {{ r.is_official ? '✓ Offiz.' : 'Offen' }}
                </span>
              </td>
              <td class="py-2.5 px-3 text-center">
                <button @click="startEdit(r)"
                  class="text-msc-blue hover:underline text-xs font-semibold">Korrigieren</button>
              </td>
            </tr>
            <tr v-if="results.length === 0">
              <td colspan="7" class="py-6 text-center text-sm text-gray-400">Keine Ergebnisse</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Korrektur-Formular -->
      <div v-if="editing" class="card border-2 border-msc-blue p-4 space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="font-bold text-gray-800 flex items-center gap-2">
            <span class="h-2.5 w-2.5 rounded-full bg-msc-blue"></span>
            Korrektur: #{{ editing.start_number }} {{ editing.first_name }} {{ editing.last_name }}
          </h3>
          <button @click="editing = null" class="text-gray-400 hover:text-gray-600">✕</button>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Rohzeit (s)</label>
            <input v-model.number="editForm.raw_time" type="number" step="0.01"
              class="w-full border-2 border-gray-200 rounded-xl px-3 py-2 text-2xl font-bold text-center font-mono focus:outline-none focus:ring-2 focus:ring-msc-blue focus:border-msc-blue">
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Status</label>
            <select v-model="editForm.status" class="input font-semibold">
              <option value="valid">valid – gültig</option>
              <option value="dns">dns – nicht gestartet</option>
              <option value="dnf">dnf – nicht gewertet</option>
              <option value="dsq">dsq – disqualifiziert</option>
            </select>
          </div>
        </div>

        <div>
          <label class="text-xs font-bold block mb-1 flex items-center gap-1.5">
            <span class="text-msc-red">⚠</span>
            <span class="text-gray-700">Begründung <span class="text-msc-red">*</span></span>
          </label>
          <textarea v-model="editForm.reason" rows="3"
            placeholder="z.B. ‹Pylone nach Videobeweis gestrichen›"
            class="w-full border-2 border-amber-300 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400 bg-amber-50/40 resize-none">
          </textarea>
        </div>

        <div v-if="editError" class="text-xs text-red-600 bg-red-50 rounded px-2 py-1">{{ editError }}</div>
        <div class="flex gap-2">
          <button @click="saveEdit" :disabled="!editForm.reason.trim()"
            class="flex-1 btn-primary py-2.5 disabled:opacity-50">Korrektur speichern</button>
          <button @click="editing = null" class="btn-secondary py-2.5 px-4">Abbrechen</button>
        </div>
      </div>
    </section>

    <!-- ── RECHTE SPALTE: Drucken + Audit-Log ── -->
    <aside class="col-span-3 space-y-3">

      <!-- Drucken -->
      <div class="card p-3 space-y-2">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-1">Drucken</h3>
        <button @click="printErgebnisliste"
          class="w-full bg-msc-blue hover:bg-msc-bluedark text-white text-xs font-bold py-2 rounded-lg transition flex items-center justify-center gap-1.5">
          🖨 Ergebnisliste
        </button>
        <button @click="printSprecherliste"
          class="w-full bg-gray-700 hover:bg-gray-600 text-white text-xs font-bold py-2 rounded-lg transition flex items-center justify-center gap-1.5">
          🖨 Sprecherliste
        </button>
      </div>

      <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500 px-1">Audit-Log</h2>
      <div v-if="auditLog.length === 0" class="card p-4 text-center text-sm text-gray-400">
        Noch keine Korrekturen
      </div>
      <div v-for="entry in auditLog.slice(0, 10)" :key="entry.id" class="card p-3">
        <div class="flex items-start justify-between mb-1">
          <span class="text-xs font-bold text-msc-blue">{{ entry.field_changed }}</span>
          <span class="text-xs text-gray-400">{{ entry.timestamp?.slice(11, 16) }}</span>
        </div>
        <div class="flex items-center gap-1.5 text-xs mb-1.5">
          <span class="line-through text-gray-400 font-mono">{{ entry.old_value }}</span>
          <span class="text-gray-400">→</span>
          <span class="font-bold text-green-600 font-mono">{{ entry.new_value }}</span>
        </div>
        <div class="text-xs text-gray-500 italic bg-gray-50 rounded px-2 py-1 line-clamp-2">
          "{{ entry.reason }}"
        </div>
      </div>
    </aside>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'

const store = useEventStore()

const results     = ref([])
const auditLog    = ref([])
const editing     = ref(null)
const editForm    = ref({ raw_time: null, status: 'valid', reason: '' })
const editError   = ref('')
const filterClass = ref('')
const filterRun   = ref('')

// ── Protest-Timer ───────────────────────────────────────────────────
const now = ref(new Date())
let clockInterval = null

const PROTEST_MINUTES = 30

function protestDeadline(cls) {
  if (!cls.end_time) return ''
  const d = new Date(new Date(cls.end_time).getTime() + PROTEST_MINUTES * 60000)
  return d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
}

function protestExpired(cls) {
  if (!cls.end_time) return false
  return new Date(cls.end_time).getTime() + PROTEST_MINUTES * 60000 <= now.value.getTime()
}

function protestCountdown(cls) {
  if (!cls.end_time) return ''
  const deadline = new Date(cls.end_time).getTime() + PROTEST_MINUTES * 60000
  const remaining = Math.max(0, deadline - now.value.getTime())
  const m = Math.floor(remaining / 60000)
  const s = Math.floor((remaining % 60000) / 1000)
  return `${m}:${String(s).padStart(2, '0')}`
}

// ── Klassen-Aktionen ─────────────────────────────────────────────────
async function startClass(cls) {
  if (!store.activeEvent) return
  await api.patch(`/events/${store.activeEvent.id}/classes/${cls.id}`, {
    run_status: 'running'
  })
  await store.selectEvent(store.activeEvent)
}

async function pauseClass(cls) {
  if (!store.activeEvent) return
  await api.patch(`/events/${store.activeEvent.id}/classes/${cls.id}`, { run_status: 'paused' })
  await store.selectEvent(store.activeEvent)
}

async function resumeClass(cls) {
  if (!store.activeEvent) return
  await api.patch(`/events/${store.activeEvent.id}/classes/${cls.id}`, { run_status: 'running' })
  await store.selectEvent(store.activeEvent)
}

async function finishClass(cls) {
  if (!store.activeEvent) return
  const endTime = new Date().toISOString()
  await api.patch(`/events/${store.activeEvent.id}/classes/${cls.id}`, {
    run_status: 'preliminary',
    end_time: endTime,
  })
  await store.selectEvent(store.activeEvent)
}

async function approveClass(cls) {
  if (!store.activeEvent) return
  await api.patch(`/events/${store.activeEvent.id}/classes/${cls.id}`, {
    run_status: 'official'
  })
  await store.selectEvent(store.activeEvent)
}

// ── Ergebnisse ───────────────────────────────────────────────────────
async function loadResults() {
  if (!store.activeEvent) return
  const params = {}
  if (filterClass.value) params.class_id  = filterClass.value
  if (filterRun.value !== '') params.run_number = filterRun.value
  const { data } = await api.get(`/events/${store.activeEvent.id}/run-results`, { params })
  results.value = data
}

async function loadAuditLog() {
  auditLog.value = []
}

function startEdit(r) {
  editing.value = r
  editForm.value = { raw_time: r.raw_time, status: r.status, reason: '' }
  editError.value = ''
}

async function saveEdit() {
  if (!editing.value || !store.activeEvent) return
  editError.value = ''
  try {
    await api.patch(
      `/events/${store.activeEvent.id}/results/${editing.value.result_id}`,
      editForm.value
    )
    editing.value = null
    await loadResults()
    await loadAuditLog()
  } catch (e) {
    editError.value = e.response?.data?.detail || 'Fehler beim Speichern'
  }
}

onMounted(async () => {
  if (!store.classes.length) await store.loadEvents()
  await loadResults()
  await loadAuditLog()
  clockInterval = setInterval(() => { now.value = new Date() }, 1000)
})
onUnmounted(() => clearInterval(clockInterval))

watch(() => store.activeEvent, () => { loadResults(); loadAuditLog() })

function statusLabel(s) {
  return { planned: 'Geplant', running: 'Läuft ▶', paused: 'Unterbrochen ⏸', preliminary: 'Vorläufig', official: 'Offiziell' }[s] || s
}

// ── Drucken ──────────────────────────────────────────────────────────
function esc(s) {
  return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function fmtDate(d) {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${day}.${m}.${y}`
}

function printOpen(title, html) {
  const w = window.open('', '_blank', 'width=1100,height=800')
  w.document.write(`<!DOCTYPE html><html lang="de"><head>
<meta charset="UTF-8"><title>${esc(title)}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #000; margin: 0; }
  .ev-header { border-bottom: 3px solid #1a3fa0; padding-bottom: 6px; margin-bottom: 14px; }
  .ev-header h1 { margin: 0; font-size: 15pt; color: #1a3fa0; letter-spacing: 1px; }
  .ev-header h2 { margin: 2px 0 0; font-size: 10pt; font-weight: normal; color: #444; }
  .ev-header .org { font-size: 8pt; color: #777; margin-top: 2px; }
  .cls-section { margin-bottom: 18px; break-inside: avoid; }
  .cls-header { background: #1a3fa0; color: #fff; font-size: 10pt; font-weight: bold;
                padding: 4px 8px; margin-bottom: 3px; display: flex; align-items: center; gap: 8px; }
  table { width: 100%; border-collapse: collapse; font-size: 8.5pt; }
  th { background: #e8edf6; border: 1px solid #b0b8d0; padding: 3px 5px; font-size: 8pt; }
  td { border: 1px solid #ddd; padding: 2.5px 5px; }
  tr:nth-child(even) td { background: #fafafa; }
  .tr { text-align: right; font-family: 'Courier New', monospace; }
  .rank-1 td { background: #fffce6 !important; }
  .rank-2 td { background: #f5f5f5 !important; }
  .rank-3 td { background: #fdf2e6 !important; }
  .badge { display: inline-block; font-size: 7pt; font-weight: bold; padding: 1px 5px; border-radius: 4px; }
  .b-ok    { background: #d4edda; color: #155724; }
  .b-pre   { background: #fff3cd; color: #856404; }
  .protest { font-size: 7.5pt; color: #777; text-align: right; margin-top: 3px; }
  footer   { position: fixed; bottom: 6px; left: 0; right: 0; text-align: center;
             font-size: 7pt; color: #aaa; border-top: 1px solid #eee; padding-top: 3px; }
</style>
</head><body>${html}</body></html>`)
  w.document.close()
  setTimeout(() => w.print(), 400)
}

async function printErgebnisliste() {
  if (!store.activeEvent) return
  const eventId = store.activeEvent.id

  const [stRes, runRes, setRes, partRes] = await Promise.all([
    api.get(`/events/${eventId}/standings`),
    api.get(`/events/${eventId}/run-results`),
    api.get('/settings/'),
    api.get(`/events/${eventId}/participants`),
  ])

  const settings = setRes.data
  const event    = store.activeEvent

  // birth year lookup: class_id_startNumber → year
  const byYear = {}
  for (const p of partRes.data) {
    byYear[`${p.class_id}_${p.start_number}`] = p.birth_year
  }

  // run detail map: class_id → start_number → run_number → { raw_time, total_penalties, total_time, status }
  const runMap = {}
  for (const r of runRes.data) {
    if (r.run_number === 0) continue
    ;(runMap[r.class_id] ??= {})[r.start_number] ??= {}
    runMap[r.class_id][r.start_number][r.run_number] = r
  }

  // standings grouped by class
  const byClass = {}
  for (const row of stRes.data) {
    ;(byClass[row.class_id] ??= []).push(row)
  }

  // how many competitive runs exist across the event
  const maxRun = runRes.data.reduce((m, r) => Math.max(m, r.run_number), 0) || 2

  function fmtT(v)  { return v != null ? Number(v).toFixed(2) : '' }
  function fmtP(v)  { return v != null && v > 0 ? '+' + Number(v).toFixed(1) : (v === 0 ? '0' : '') }
  function fmtTot(t){ return t != null ? t.toFixed(2) : '–' }

  function runCells(r) {
    // returns [zeitCell, strafCell, gesCell]
    if (!r) return ['–', '', '']
    if (r.status !== 'valid') return [`<em>${r.status.toUpperCase()}</em>`, '', '']
    return [fmtT(r.raw_time), fmtP(r.total_penalties), fmtT(r.total_time)]
  }

  const now       = new Date()
  const printDate = now.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })

  // grouped column headers for runs
  const runGroupHeaders = Array.from({ length: maxRun }, (_, i) =>
    `<th colspan="3" class="run-group">${i + 1}. Lauf</th>`
  ).join('')
  const runSubHeaders = Array.from({ length: maxRun }, () =>
    `<th class="tr">Fahrzeit</th><th class="tr">Fehlerpkt.</th><th class="tr">Gesamt</th>`
  ).join('')

  const classesHtml = store.classes
    .filter(cls => byClass[cls.id]?.length)
    .map(cls => {
      const rows   = byClass[cls.id]
      const leader = rows.find(r => r.total_time != null)
      const cRuns  = runMap[cls.id] || {}
      const isOk   = cls.run_status === 'official'
      const badge  = `<span class="badge ${isOk ? 'b-ok' : 'b-pre'}">${isOk ? 'OFFIZIELL' : 'VORLÄUFIG'}</span>`
      const deadline = cls.end_time
        ? new Date(new Date(cls.end_time).getTime() + 30 * 60000)
            .toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr'
        : '–'

      const rowsHtml = rows.map((row, i) => {
        const runs      = cRuns[row.start_number] || {}
        const birthYear = byYear[`${cls.id}_${row.start_number}`] || ''
        const hasTime   = row.total_time != null
        const diff      = (!hasTime || !leader?.total_time || row.total_time === leader.total_time)
          ? '–'
          : '+' + (row.total_time - leader.total_time).toFixed(2)

        const runTdHtml = Array.from({ length: maxRun }, (_, ri) => {
          const [z, s, g] = runCells(runs[ri + 1])
          return `<td class="tr">${z}</td><td class="tr straf">${s}</td><td class="tr">${g}</td>`
        }).join('')

        const rowCls = i === 0 && hasTime ? 'rank-1' : i === 1 && hasTime ? 'rank-2' : i === 2 && hasTime ? 'rank-3' : ''
        return `<tr class="${rowCls}">
          <td class="tc bold">${row.rank}</td>
          <td class="tc bold">#${row.start_number}</td>
          <td><strong>${esc(row.last_name)}</strong>, ${esc(row.first_name)}</td>
          <td class="tc">${birthYear}</td>
          <td>${esc(row.club || '–')}</td>
          ${runTdHtml}
          <td class="tr bold">${fmtTot(row.total_time)}</td>
          <td class="tr">${diff}</td>
        </tr>`
      }).join('')

      return `<div class="cls-section">
        <div class="cls-header">${esc(cls.name)} ${badge}</div>
        <table>
          <thead>
            <tr>
              <th rowspan="2" style="width:20px">Pl.</th>
              <th rowspan="2" style="width:28px">St.Nr.</th>
              <th rowspan="2">Name, Vorname</th>
              <th rowspan="2" style="width:22px">Jg.</th>
              <th rowspan="2" style="width:26mm">Verein</th>
              ${runGroupHeaders}
              <th rowspan="2" class="tr" style="width:16mm">Summe</th>
              <th rowspan="2" class="tr" style="width:14mm">Diff.</th>
            </tr>
            <tr>${runSubHeaders}</tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>
        <div class="class-footer">
          <span>Einspruchfrist 30 Min. ab Aushang · bis: <strong>${deadline}</strong></span>
          <span class="sig-block">Schiedsrichter/Sportkommissär: <span class="sig-line"></span></span>
        </div>
      </div>`
    }).join('')

  const html = `
    <style>@page { size: A4 landscape; margin: 1.0cm 1.4cm; }</style>
    <header class="ev-header">
      <div>
        <div class="ev-tag">ADAC Hessen-Thüringen e.V. · Kart-Slalom</div>
        <h1>ERGEBNISLISTE</h1>
        <h2>${esc(event.name)}</h2>
        <div class="ev-meta">${fmtDate(event.date)} &nbsp;·&nbsp; ${esc(event.location || '')} &nbsp;·&nbsp; Veranstalter: ${esc(settings.organizer_name || 'MSC Braach e.V. im ADAC')}</div>
      </div>
      <div class="ev-print">Ausdruck: ${printDate}</div>
    </header>
    ${classesHtml}
    <footer>RaceControl Pro · ${esc(settings.organizer_name || 'MSC Braach e.V. im ADAC')}</footer>`

  // Override the shared printOpen styles with the landscape-specific ones
  const w = window.open('', '_blank', 'width=1200,height=800')
  w.document.write(`<!DOCTYPE html><html lang="de"><head>
<meta charset="UTF-8"><title>Ergebnisliste – ${esc(event.name)}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 8.5pt; color: #000; margin: 0; }
  @page { size: A4 landscape; margin: 1.0cm 1.4cm; }
  .ev-header { display: flex; justify-content: space-between; align-items: flex-start;
               border-bottom: 3px solid #1a3fa0; padding-bottom: 5px; margin-bottom: 10px; }
  .ev-tag  { font-size: 7.5pt; color: #1a3fa0; font-weight: bold; letter-spacing: 0.5px; margin-bottom: 1px; }
  h1 { margin: 0; font-size: 15pt; color: #1a3fa0; letter-spacing: 1px; }
  h2 { margin: 1px 0 0; font-size: 10pt; font-weight: normal; }
  .ev-meta { font-size: 8pt; color: #555; margin-top: 2px; }
  .ev-print { font-size: 7.5pt; color: #aaa; align-self: flex-end; }
  .cls-section { margin-bottom: 14px; break-inside: avoid; }
  .cls-header  { background: #1a3fa0; color: #fff; font-size: 9.5pt; font-weight: bold;
                 padding: 3px 7px; margin-bottom: 0; display: flex; align-items: center; gap: 8px; }
  table { width: 100%; border-collapse: collapse; font-size: 8pt; }
  th { border: 1px solid #888; background: #e0e6f0; padding: 2px 4px; text-align: center;
       font-size: 7.5pt; vertical-align: middle; }
  .run-group { background: #c8d4ea; font-weight: bold; }
  td { border: 1px solid #ccc; padding: 2px 4px; vertical-align: middle; }
  .tr   { text-align: right; font-family: 'Courier New', monospace; }
  .tc   { text-align: center; }
  .bold { font-weight: bold; }
  .straf { color: #c00; font-size: 7.5pt; }
  tr:nth-child(even) td { background: #fafafa; }
  .rank-1 td { background: #fffce6 !important; }
  .rank-2 td { background: #f0f0f0 !important; }
  .rank-3 td { background: #fdf2e6 !important; }
  .badge { display: inline-block; font-size: 7pt; font-weight: bold; padding: 1px 5px;
           border-radius: 3px; }
  .b-ok  { background: #d4edda; color: #155724; }
  .b-pre { background: #fff3cd; color: #856404; }
  .class-footer { display: flex; justify-content: space-between; align-items: baseline;
                  font-size: 7.5pt; color: #555; border: 1px solid #ccc; border-top: none;
                  padding: 3px 6px; background: #f9f9f9; }
  .sig-block { display: flex; align-items: baseline; gap: 6px; }
  .sig-line  { display: inline-block; border-bottom: 1px solid #555; width: 80mm; }
  footer { position: fixed; bottom: 4px; left: 0; right: 0; text-align: center;
           font-size: 7pt; color: #bbb; border-top: 1px solid #eee; padding-top: 2px; }
</style>
</head><body>${html}</body></html>`)
  w.document.close()
  setTimeout(() => w.print(), 400)
}

async function printSprecherliste() {
  if (!store.activeEvent) return
  const eventId = store.activeEvent.id
  const [partRes, setRes] = await Promise.all([
    api.get(`/events/${eventId}/participants`),
    api.get('/settings/'),
  ])

  const settings     = setRes.data
  const event        = store.activeEvent
  const participants = partRes.data

  const byClass = {}
  for (const p of participants) {
    ;(byClass[p.class_id ?? 0] ??= []).push(p)
  }

  const now       = new Date()
  const printDate = now.toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })

  const classesHtml = [
    ...store.classes,
    ...(byClass[0]?.length ? [{ id: 0, name: 'Ohne Klasse', start_order: 999 }] : []),
  ]
    .filter(cls => byClass[cls.id]?.length)
    .map(cls => {
      const rows = [...(byClass[cls.id] || [])].sort((a, b) => (a.start_number || 0) - (b.start_number || 0))
      const rowsHtml = rows.map((p, i) => `<tr>
        <td style="text-align:center">${i + 1}</td>
        <td style="text-align:center;font-weight:bold">#${p.start_number ?? '–'}</td>
        <td><strong>${esc(p.last_name)}</strong>, ${esc(p.first_name)}</td>
        <td>${esc(p.club_name || '–')}</td>
        <td style="text-align:center">${p.birth_year ?? '–'}</td>
        <td></td>
      </tr>`).join('')
      return `<div class="cls-section">
        <div class="cls-header">${esc(cls.name)}
          <span style="font-weight:normal;font-size:8pt">(${rows.length} Teilnehmer)</span>
        </div>
        <table>
          <thead><tr>
            <th style="width:28px">Lfd.</th><th style="width:40px">St.Nr.</th>
            <th>Name, Vorname</th><th>Verein</th>
            <th style="width:38px;text-align:center">Jg.</th>
            <th style="width:65px">Notiz</th>
          </tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>`
    }).join('')

  const html = `
    <header class="ev-header">
      <h1>SPRECHERLISTE</h1>
      <h2>${esc(event.name)} · ${fmtDate(event.date)} · ${esc(event.location || '')}</h2>
      <div class="org">Veranstalter: ${esc(settings.organizer_name || 'MSC Braach e.V. im ADAC')}</div>
    </header>
    <style>@page { size: A4 portrait; margin: 1.2cm 1.5cm; }</style>
    ${classesHtml}
    <footer>RaceControl Pro · ${esc(settings.organizer_name || 'MSC Braach e.V. im ADAC')} · Ausdruck: ${printDate}</footer>`

  printOpen(`Sprecherliste – ${event.name}`, html)
}
</script>
