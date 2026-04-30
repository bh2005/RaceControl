<template>
  <div class="max-w-5xl mx-auto px-4 py-6 space-y-6">

    <!-- Header / Event-Auswahl -->
    <div class="flex items-center justify-between flex-wrap gap-3">
      <h1 class="text-2xl font-black text-gray-900">Auswertung</h1>
      <div class="flex items-center gap-2 flex-wrap">
        <select v-model.number="selectedEventId" @change="load" class="input max-w-xs">
          <option v-for="ev in events" :key="ev.id" :value="ev.id">
            {{ ev.name }} ({{ ev.date }})
          </option>
        </select>
        <button
          v-if="selectedEventId"
          @click="exportCsv"
          class="btn-secondary px-3 py-2 text-sm flex items-center gap-1.5 whitespace-nowrap"
          title="Alle Klassen als CSV exportieren (öffnet in Excel)"
        >
          📥 CSV / Excel
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-gray-400">Lade Daten…</div>

    <template v-else-if="stats">

      <!-- Schnellste Einzellaufzeit pro Klasse -->
      <section class="card p-0 overflow-hidden">
        <div class="px-4 py-3 bg-msc-blue text-white font-bold flex items-center gap-2">
          <span>🏆</span> Schnellste Wertungsläufe pro Klasse
        </div>
        <div v-if="stats.fastest_per_class.length === 0"
             class="px-4 py-6 text-sm text-gray-400 text-center">
          Noch keine Wertungsläufe vorhanden
        </div>
        <table v-else class="w-full text-sm">
          <thead class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th class="px-4 py-2 text-left">Klasse</th>
              <th class="px-4 py-2 text-left">#</th>
              <th class="px-4 py-2 text-left">Fahrer / Fahrerin</th>
              <th class="px-4 py-2 text-left">Verein</th>
              <th class="px-4 py-2 text-center">Lauf</th>
              <th class="px-4 py-2 text-right font-mono">Bestzeit</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in stats.fastest_per_class" :key="row.class_id"
                class="border-t border-gray-100 hover:bg-blue-50 transition">
              <td class="px-4 py-2.5 font-semibold text-msc-blue">{{ row.class_name }}</td>
              <td class="px-4 py-2.5 text-gray-500">{{ row.start_number ?? '–' }}</td>
              <td class="px-4 py-2.5 font-medium">{{ row.first_name }} {{ row.last_name }}</td>
              <td class="px-4 py-2.5 text-gray-500">{{ row.club || 'n.N.' }}</td>
              <td class="px-4 py-2.5 text-center text-gray-500">{{ row.run_number }}</td>
              <td class="px-4 py-2.5 text-right font-mono font-bold text-green-700">
                {{ fmtTime(row.total_time) }}
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Schnellste Dame / Schnellster Herr -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

        <section class="card p-4 space-y-2">
          <div class="font-bold text-gray-800 flex items-center gap-2 text-base">
            <span>👑</span> Schnellste Dame
          </div>
          <div v-if="!stats.fastest_dame"
               class="text-sm text-gray-400 py-4 text-center">
            Noch kein Ergebnis — Geschlecht muss bei Teilnehmern hinterlegt sein
          </div>
          <div v-else class="space-y-1">
            <div class="text-xl font-black font-mono text-pink-600">
              {{ fmtTime(stats.fastest_dame.total_time) }}
            </div>
            <div class="font-semibold text-gray-900">
              {{ stats.fastest_dame.start_number ? '#' + stats.fastest_dame.start_number + ' ' : '' }}{{ stats.fastest_dame.first_name }} {{ stats.fastest_dame.last_name }}
            </div>
            <div class="text-sm text-gray-500">
              {{ stats.fastest_dame.class_name }}
              <span v-if="stats.fastest_dame.club"> · {{ stats.fastest_dame.club }}</span>
            </div>
            <div class="text-xs text-gray-400">Lauf {{ stats.fastest_dame.run_number }}</div>
          </div>
        </section>

        <section class="card p-4 space-y-2">
          <div class="font-bold text-gray-800 flex items-center gap-2 text-base">
            <span>👑</span> Schnellster Herr
          </div>
          <div v-if="!stats.fastest_herr"
               class="text-sm text-gray-400 py-4 text-center">
            Noch kein Ergebnis — Geschlecht muss bei Teilnehmern hinterlegt sein
          </div>
          <div v-else class="space-y-1">
            <div class="text-xl font-black font-mono text-blue-700">
              {{ fmtTime(stats.fastest_herr.total_time) }}
            </div>
            <div class="font-semibold text-gray-900">
              {{ stats.fastest_herr.start_number ? '#' + stats.fastest_herr.start_number + ' ' : '' }}{{ stats.fastest_herr.first_name }} {{ stats.fastest_herr.last_name }}
            </div>
            <div class="text-sm text-gray-500">
              {{ stats.fastest_herr.class_name }}
              <span v-if="stats.fastest_herr.club"> · {{ stats.fastest_herr.club }}</span>
            </div>
            <div class="text-xs text-gray-400">Lauf {{ stats.fastest_herr.run_number }}</div>
          </div>
        </section>

      </div>

    </template>

    <div v-else-if="!loading" class="text-center py-12 text-gray-400 text-sm">
      Keine Veranstaltung ausgewählt
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'

const store  = useEventStore()
const events = ref([])
const selectedEventId = ref(null)
const stats  = ref(null)
const loading = ref(false)

function fmtTime(sec) {
  if (sec == null) return '–'
  const m = Math.floor(sec / 60)
  const s = (sec % 60).toFixed(3).padStart(6, '0')
  return m > 0 ? `${m}:${s}` : `${s}`
}

async function load() {
  if (!selectedEventId.value) return
  loading.value = true
  stats.value = null
  try {
    const { data } = await api.get(`/events/${selectedEventId.value}/statistics`)
    stats.value = data
  } finally {
    loading.value = false
  }
}

async function exportCsv() {
  if (!selectedEventId.value) return
  const { data } = await api.get(`/events/${selectedEventId.value}/results/export`, {
    responseType: 'blob',
  })
  const ev  = events.value.find(e => e.id === selectedEventId.value)
  const url = URL.createObjectURL(new Blob([data], { type: 'text/csv;charset=utf-8' }))
  const a   = document.createElement('a')
  a.download = `Ergebnisse_${ev ? ev.name : selectedEventId.value}.csv`
  a.href = url
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  const { data } = await api.get('/events/')
  events.value = data
  if (store.activeEvent) {
    selectedEventId.value = store.activeEvent.id
  } else if (data.length) {
    selectedEventId.value = data[0].id
  }
  if (selectedEventId.value) await load()
})
</script>
