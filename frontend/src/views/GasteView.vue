<template>
  <div class="min-h-screen bg-gray-950 text-white flex flex-col">

    <!-- Hero Header -->
    <header class="bg-gradient-to-b from-msc-blue to-msc-bluedark pt-10 pb-16 px-4 text-center relative overflow-hidden">
      <!-- subtle grid pattern -->
      <div class="absolute inset-0 opacity-10"
           style="background-image: repeating-linear-gradient(0deg,transparent,transparent 39px,rgba(255,255,255,.3) 39px,rgba(255,255,255,.3) 40px),repeating-linear-gradient(90deg,transparent,transparent 39px,rgba(255,255,255,.3) 39px,rgba(255,255,255,.3) 40px)">
      </div>
      <div class="relative">
        <img src="/msc-logo.svg" alt="MSC" class="h-20 w-20 rounded-full border-3 border-white/30 mx-auto mb-4 shadow-2xl">
        <div class="text-blue-200 text-sm font-semibold tracking-widest uppercase mb-1">MSC Braach e.V. im ADAC</div>
        <h1 class="font-black text-3xl sm:text-4xl leading-tight">
          {{ event?.name || 'RaceControl Pro' }}
        </h1>
        <div v-if="event" class="flex items-center justify-center gap-3 mt-3 text-blue-200 text-sm">
          <span>📅 {{ formatDate(event.date) }}</span>
          <span class="opacity-40">·</span>
          <span>📍 {{ event.location }}</span>
        </div>
        <!-- live indicator if something's running -->
        <div v-if="runningClass" class="inline-flex items-center gap-2 mt-4 bg-green-500/20 border border-green-500/40 text-green-300 text-sm font-bold rounded-full px-4 py-1.5">
          <span class="h-2 w-2 rounded-full bg-green-400 animate-pulse inline-block"></span>
          {{ runningClass.name }} läuft gerade
        </div>
      </div>
    </header>

    <!-- Pull-up card -->
    <div class="-mt-6 flex-1 bg-gray-950 rounded-t-3xl px-4 pt-6 pb-12 space-y-5">

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-12">
        <div class="h-10 w-10 border-4 border-msc-blue border-t-transparent rounded-full animate-spin"></div>
      </div>

      <template v-else>

        <!-- ── Veranstaltungsbeschreibung ── -->
        <div v-if="event?.description" class="bg-gray-900 border border-gray-800 rounded-2xl px-4 py-3 text-sm text-gray-300 leading-relaxed whitespace-pre-line">
          {{ event.description }}
        </div>

        <!-- ── Zwei Haupt-Aktionen ── -->
        <div class="grid grid-cols-2 gap-3">
          <RouterLink to="/livetiming"
            class="card-dark flex flex-col items-center justify-center gap-2 py-6 rounded-2xl text-center hover:bg-gray-700 active:scale-95 transition-transform border border-gray-700">
            <span class="text-4xl">🏁</span>
            <div class="font-black text-base">Livetiming</div>
            <div class="text-xs text-gray-400">Ergebnisse live</div>
          </RouterLink>
          <RouterLink to="/nennen"
            class="card-dark flex flex-col items-center justify-center gap-2 py-6 rounded-2xl text-center hover:bg-gray-700 active:scale-95 transition-transform border border-gray-700">
            <span class="text-4xl">📝</span>
            <div class="font-black text-base">Online-Nennung</div>
            <div class="text-xs text-gray-400">Jetzt anmelden</div>
          </RouterLink>
        </div>

        <!-- ── Klassen-Übersicht ── -->
        <div v-if="classes.length">
          <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2 px-1">Klassen heute</h2>
          <div class="space-y-2">
            <div
              v-for="c in classes" :key="c.id"
              class="flex items-center gap-3 rounded-xl px-4 py-3 border"
              :class="{
                'bg-green-950/60 border-green-800': c.run_status === 'official',
                'bg-blue-950/60 border-blue-700': c.run_status === 'running',
                'bg-amber-950/40 border-amber-800': c.run_status === 'preliminary',
                'bg-gray-900 border-gray-800': c.run_status === 'planned',
              }"
            >
              <span
                class="h-2.5 w-2.5 rounded-full shrink-0"
                :class="{
                  'bg-green-400': c.run_status === 'official',
                  'bg-blue-400 animate-pulse': c.run_status === 'running',
                  'bg-amber-400': c.run_status === 'preliminary',
                  'bg-gray-600': c.run_status === 'planned',
                }"
              ></span>
              <span class="font-semibold text-sm flex-1">{{ c.name }}</span>
              <span
                class="text-xs font-bold rounded-full px-2 py-0.5"
                :class="{
                  'bg-green-900/60 text-green-400': c.run_status === 'official',
                  'bg-blue-900/60 text-blue-300': c.run_status === 'running',
                  'bg-amber-900/60 text-amber-400': c.run_status === 'preliminary',
                  'bg-gray-800 text-gray-500': c.run_status === 'planned',
                }"
              >{{ statusLabel(c.run_status) }}</span>
            </div>
          </div>
        </div>

        <!-- ── Mini-Standings für laufende/letzte Klasse ── -->
        <div v-if="previewClass && previewStandings.length">
          <div class="flex items-center justify-between mb-2 px-1">
            <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500">
              Aktueller Stand · {{ previewClass.name }}
            </h2>
            <RouterLink to="/livetiming" class="text-xs text-msc-blue font-semibold">
              Alle →
            </RouterLink>
          </div>
          <div class="space-y-1.5">
            <div
              v-for="(row, i) in previewStandings.slice(0, 5)"
              :key="row.participant_id"
              class="flex items-center gap-3 rounded-xl px-3 py-2.5"
              :class="i === 0
                ? 'bg-gradient-to-r from-yellow-500/20 to-amber-500/10 border border-yellow-700/40'
                : 'bg-gray-900 border border-gray-800'"
            >
              <span class="font-black text-lg w-6 text-center shrink-0"
                    :class="i === 0 ? 'text-yellow-400' : i === 1 ? 'text-slate-300' : i === 2 ? 'text-amber-700' : 'text-gray-600'">
                {{ i + 1 }}
              </span>
              <span class="font-black text-sm shrink-0 text-gray-300">#{{ row.start_number }}</span>
              <span class="font-semibold text-sm flex-1 truncate">{{ row.first_name }} {{ row.last_name }}</span>
              <span class="font-black tabnum text-sm shrink-0"
                    :class="i === 0 ? 'text-yellow-400' : 'text-gray-300'">
                {{ row.total_time ? row.total_time.toFixed(2) : '–' }}
              </span>
            </div>
          </div>
        </div>

        <!-- ── Teilnehmer-Zähler ── -->
        <div v-if="stats.total > 0">
          <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-2 px-1">Teilnehmer</h2>
          <div class="grid grid-cols-3 gap-2">
            <div class="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
              <div class="text-2xl font-black text-white">{{ stats.total }}</div>
              <div class="text-xs text-gray-500">Gemeldet</div>
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
              <div class="text-2xl font-black text-green-400">{{ stats.technical_ok }}</div>
              <div class="text-xs text-gray-500">Abgenommen</div>
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-xl p-3 text-center">
              <div class="text-2xl font-black text-msc-blue">{{ classes.length }}</div>
              <div class="text-xs text-gray-500">Klassen</div>
            </div>
          </div>
        </div>

        <!-- ── Sponsoren ── -->
        <div v-if="sponsors.length">
          <h2 class="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3 px-1">Unsere Sponsoren</h2>
          <div class="flex flex-wrap justify-center gap-4">
            <a
              v-for="s in sponsors" :key="s.id"
              :href="s.website_url || undefined"
              :target="s.website_url ? '_blank' : undefined"
              rel="noopener noreferrer"
              class="bg-gray-900 border border-gray-800 rounded-xl p-3 flex items-center justify-center transition hover:border-gray-600"
              :class="s.website_url ? 'cursor-pointer' : 'cursor-default'"
              style="min-width: 100px; max-width: 160px;"
            >
              <img v-if="s.logo_url" :src="s.logo_url" :alt="s.name" class="h-10 object-contain">
              <span v-else class="text-xs text-gray-400 font-semibold text-center">{{ s.name }}</span>
            </a>
          </div>
        </div>

        <!-- ── Staff login link (unauffällig) ── -->
        <div class="text-center pt-2">
          <RouterLink to="/login" class="text-xs text-gray-700 hover:text-gray-500 transition">
            Anmelden (Personal)
          </RouterLink>
        </div>

      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '../api/client'
import { useRealtimeUpdate } from '../composables/useRealtimeUpdate'

const loading          = ref(true)
const event            = ref(null)
const classes          = ref([])
const sponsors         = ref([])
const standingsByClass = ref({})

const runningClass = computed(() =>
  classes.value.find(c => c.run_status === 'running') || null
)

const previewClass = computed(() =>
  classes.value.find(c => c.run_status === 'running') ||
  classes.value.find(c => c.run_status === 'preliminary') ||
  null
)

const previewStandings = computed(() =>
  previewClass.value ? (standingsByClass.value[previewClass.value.id] || []) : []
)

const stats = computed(() => {
  const s = { total: 0, technical_ok: 0 }
  for (const rows of Object.values(standingsByClass.value)) {
    s.total += rows.length
    s.technical_ok += rows.filter(r => r.status === 'technical_ok' || r.total_time != null).length
  }
  return s
})

async function load() {
  try {
    const [evRes, stRes] = await Promise.allSettled([
      api.get('/public/active-event'),
      loadStandings(),
    ])
    if (evRes.status === 'fulfilled') {
      event.value    = evRes.value.data.event
      classes.value  = evRes.value.data.classes
      sponsors.value = evRes.value.data.sponsors || []
    }
  } finally {
    loading.value = false
  }
}

async function loadStandings() {
  if (!event.value) {
    // Try to get event first
    try {
      const { data } = await api.get('/public/active-event')
      event.value    = data.event
      classes.value  = data.classes
      sponsors.value = data.sponsors || []
    } catch {
      return
    }
  }
  try {
    const { data } = await api.get(`/events/${event.value.id}/standings`)
    const grouped = {}
    for (const row of data) {
      if (!grouped[row.class_id]) grouped[row.class_id] = []
      grouped[row.class_id].push(row)
    }
    standingsByClass.value = grouped
  } catch { /* standings not yet available */ }
}

async function refresh() {
  if (!event.value) return
  try {
    const [evRes, stRes] = await Promise.allSettled([
      api.get('/public/active-event'),
      api.get(`/events/${event.value.id}/standings`),
    ])
    if (evRes.status === 'fulfilled') {
      event.value    = evRes.value.data.event
      classes.value  = evRes.value.data.classes
      sponsors.value = evRes.value.data.sponsors || []
    }
    if (stRes.status === 'fulfilled') {
      const grouped = {}
      for (const row of stRes.value.data) {
        if (!grouped[row.class_id]) grouped[row.class_id] = []
        grouped[row.class_id].push(row)
      }
      standingsByClass.value = grouped
    }
  } catch { /* ignore */ }
}

// WebSocket — sofortige Updates bei neuen Ergebnissen oder Statuswechseln
useRealtimeUpdate(async (msg) => {
  if (!event.value) return
  if (msg.event_id && msg.event_id !== event.value.id) return
  if (msg.type === 'results' || msg.type === 'classes') await refresh()
})

// Fallback-Polling (60 s) für robuste Zuverlässigkeit
let fallback = null
onMounted(async () => {
  await load()
  fallback = setInterval(refresh, 60000)
})
onUnmounted(() => clearInterval(fallback))

function formatDate(d) {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${day}.${m}.${y}`
}

function statusLabel(s) {
  return { planned: 'Geplant', running: 'Läuft ▶', preliminary: 'Vorläufig', official: 'Offiziell' }[s] || s
}
</script>
