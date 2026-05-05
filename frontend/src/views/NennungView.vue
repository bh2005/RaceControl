<template>
  <div class="max-w-7xl mx-auto px-4 py-4 pb-12 grid grid-cols-1 lg:grid-cols-12 gap-4">

    <!-- ── LINKE SPALTE ── -->
    <aside class="col-span-full lg:col-span-3 space-y-3">

      <!-- Kennzahlen -->
      <div class="grid grid-cols-2 gap-2">
        <div class="card p-3 text-center">
          <div class="text-2xl font-black text-msc-blue">{{ stats.total }}</div>
          <div class="text-xs text-gray-500">Gesamt</div>
        </div>
        <div class="card p-3 text-center">
          <div class="text-2xl font-black text-amber-500">{{ stats.no_number }}</div>
          <div class="text-xs text-gray-500">Ohne Nr.</div>
        </div>
        <div class="card p-3 text-center">
          <div class="text-2xl font-black text-green-600">{{ stats.technical_ok }}</div>
          <div class="text-xs text-gray-500">Freigegeben</div>
        </div>
        <div class="card p-3 text-center">
          <div class="text-2xl font-black text-msc-red">{{ stats.disqualified }}</div>
          <div class="text-xs text-gray-500">DSQ</div>
        </div>
      </div>

      <!-- Startklar-Banner -->
      <div class="card p-3 border-l-4"
           :class="stats.startklar === stats.total && stats.total > 0
             ? 'border-green-500 bg-green-50' : 'border-amber-400 bg-amber-50'">
        <div class="text-xs font-bold uppercase tracking-widest mb-1.5"
             :class="stats.startklar === stats.total && stats.total > 0 ? 'text-green-600' : 'text-amber-700'">
          Startklar (€ + Helm)
        </div>
        <div class="flex items-end gap-1 mb-1">
          <span class="text-3xl font-black"
                :class="stats.startklar === stats.total && stats.total > 0 ? 'text-green-600' : 'text-amber-600'">
            {{ stats.startklar }}</span>
          <span class="text-gray-400 text-sm mb-1">/ {{ stats.total }}</span>
        </div>
        <div class="space-y-0.5 text-xs">
          <div class="flex justify-between text-gray-600">
            <span>€ Offen</span>
            <span class="font-bold" :class="stats.fee_open > 0 ? 'text-amber-600' : 'text-green-600'">{{ stats.fee_open }}</span>
          </div>
          <div class="flex justify-between text-gray-600">
            <span>🪖 Ausstehend</span>
            <span class="font-bold" :class="stats.helmet_open > 0 ? 'text-amber-600' : 'text-green-600'">{{ stats.helmet_open }}</span>
          </div>
        </div>
      </div>

      <!-- Klassen-Status + Nennungsschluss -->
      <div class="card p-3 space-y-2">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500">Klassen-Status</h3>
        <div v-for="cls in store.classes" :key="cls.id"
             class="rounded-xl border p-2.5 space-y-1.5"
             :class="{
               'border-amber-300 bg-amber-50': cls.registration_closed_at && !cls.start_time,
               'border-green-200 bg-green-50': cls.start_time,
               'border-gray-200 bg-white': !cls.registration_closed_at,
             }">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-gray-800">{{ cls.short_name || cls.name }}</span>
            <span class="text-xs rounded px-1.5 py-0.5 font-bold"
                  :class="{
                    'bg-green-100 text-green-700': cls.run_status === 'official',
                    'bg-blue-100 text-blue-700': cls.run_status === 'running',
                    'bg-amber-100 text-amber-700': cls.run_status === 'preliminary',
                    'bg-gray-100 text-gray-500': cls.run_status === 'planned',
                  }">{{ statusLabel(cls.run_status) }}</span>
          </div>

          <!-- Zeiten anzeigen wenn gesetzt -->
          <div v-if="cls.start_time" class="text-xs text-gray-600 space-y-0.5">
            <div>Start: <span class="font-bold">{{ cls.start_time }}</span></div>
            <div v-if="cls.registration_closed_at" class="text-gray-400">
              Nennungsschluss: {{ cls.registration_closed_at.slice(11, 16) }}
            </div>
          </div>

          <!-- Nennungsschluss-Button (solange noch nicht gesetzt) -->
          <div v-if="!cls.registration_closed_at">
            <button
              v-if="closingClassId !== cls.id"
              @click="openNennungsschluss(cls)"
              class="w-full text-xs bg-msc-blue hover:bg-msc-bluedark text-white font-bold py-1.5 rounded-lg transition"
            >Nennungsschluss setzen</button>
          </div>

          <!-- Ankündigung wiederholen (wenn Nennungsschluss bereits gesetzt) -->
          <button v-if="cls.registration_closed_at"
            @click="announceClass(cls)"
            class="w-full text-xs bg-amber-500 hover:bg-amber-600 text-white font-bold py-1.5 rounded-lg transition"
            title="Benachrichtigung an Zuschauer und Sprecher erneut senden">
            📢 Ankündigung wiederholen
          </button>

          <!-- Nennungsschluss-Formular (inline) -->
          <div v-if="closingClassId === cls.id" class="space-y-1.5">
            <div>
              <label class="text-xs text-gray-500 block mb-0.5">Startzeit der Klasse</label>
              <input v-model="closingStartTime" type="time"
                class="w-full border border-gray-300 rounded px-2 py-1 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-msc-blue">
            </div>
            <div class="flex gap-1">
              <button @click="saveNennungsschluss(cls)"
                :disabled="!closingStartTime"
                class="flex-1 text-xs bg-green-600 hover:bg-green-700 text-white font-bold py-1.5 rounded-lg transition disabled:opacity-40">
                Bestätigen
              </button>
              <button @click="closingClassId = null"
                class="text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold py-1.5 px-2 rounded-lg transition">
                ✕
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Filter -->
      <div class="card p-3 space-y-2">
        <h3 class="text-xs font-bold uppercase tracking-widest text-gray-500">Filter</h3>
        <select v-model="filterClass" class="input">
          <option value="">Alle Klassen</option>
          <option v-for="c in store.classes" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
        <select v-model="filterStatus" class="input">
          <option value="">Alle Status</option>
          <option value="no_number">⬜ Ohne Startnummer</option>
          <option value="startklar">⭐ Startklar (€ + Helm)</option>
          <option value="pending">⚠ Abnahme offen</option>
          <option value="registered">Gemeldet</option>
          <option value="checked_in">Eingecheckt</option>
          <option value="technical_ok">Freigegeben</option>
          <option value="disqualified">DSQ</option>
        </select>
        <input v-model="search" type="text" placeholder="Name / Startnr. suchen" class="input">
      </div>

      <button @click="openNew" class="w-full btn-primary py-2.5 flex items-center justify-center gap-2">
        + Nachnennung
      </button>
    </aside>

    <!-- ── MITTE: Teilnehmerliste ── -->
    <section class="col-span-full lg:col-span-6 space-y-2">

      <!-- Modus-Toggle -->
      <div class="flex items-center gap-2">
        <button @click="mode = 'list'"
          class="text-xs font-bold px-3 py-1.5 rounded-lg transition"
          :class="mode === 'list' ? 'bg-msc-blue text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'">
          Teilnehmer
        </button>
        <button @click="mode = 'numbers'"
          class="text-xs font-bold px-3 py-1.5 rounded-lg transition"
          :class="mode === 'numbers' ? 'bg-msc-blue text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'">
          🎲 Startnummern vergeben
        </button>
        <button v-if="isDownhill" @click="mode = 'schedule'; loadSchedule()"
          class="text-xs font-bold px-3 py-1.5 rounded-lg transition"
          :class="mode === 'schedule' ? 'bg-orange-500 text-white' : 'bg-white text-orange-600 border border-orange-200 hover:bg-orange-50'">
          📋 Starterliste
        </button>
        <span v-if="mode === 'numbers'" class="text-xs text-gray-400 ml-1">
          Nach Auslosung eintragen
        </span>
        <div class="ml-auto flex gap-2">
          <!-- CSV-Import -->
          <label class="text-xs font-bold px-3 py-1.5 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 transition flex items-center gap-1.5 cursor-pointer"
                 title="ADAC-Portal CSV importieren">
            📥 CSV Import
            <input type="file" accept=".csv,.txt" class="hidden" @change="importCsv">
          </label>
          <div v-if="importResult" class="flex items-center gap-1.5 text-xs font-semibold rounded-lg px-2.5 py-1.5 border"
               :class="importResult.errors.length ? 'bg-amber-50 text-amber-800 border-amber-300' : 'bg-green-50 text-green-800 border-green-300'">
            ✓ {{ importResult.imported }} importiert · {{ importResult.skipped }} übersprungen
            <span v-if="importResult.errors.length" class="text-msc-red">· {{ importResult.errors.length }} Fehler</span>
            <button @click="importResult = null" class="ml-1 opacity-50 hover:opacity-100">✕</button>
          </div>
          <button @click="printNennliste()"
            class="text-xs font-bold px-3 py-1.5 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 transition flex items-center gap-1.5">
            🖨 Nennliste drucken
          </button>
        </div>
      </div>

      <!-- ═══ NORMALER MODUS ═══ -->
      <div v-if="mode === 'list'" class="card overflow-hidden">
        <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <h2 class="font-bold text-gray-800">
            Teilnehmer <span class="text-gray-400 font-normal text-sm">({{ filtered.length }})</span>
          </h2>
          <span v-if="filterStatus === 'startklar'"
            class="text-xs bg-green-100 text-green-700 font-bold rounded-full px-2 py-0.5">Starterliste</span>
        </div>
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
              <th class="py-2.5 px-3 text-left">Nr.</th>
              <th class="py-2.5 px-3 text-left">Name</th>
              <th class="py-2.5 px-3 text-left">Jg.</th>
              <th class="py-2.5 px-3 text-center">Abnahme</th>
              <th class="py-2.5 px-3 text-center">Status</th>
              <th class="py-2.5 px-3 text-center">Aktion</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr
              v-for="p in filtered" :key="p.id"
              class="transition cursor-pointer"
              :class="{
                'bg-amber-50 border-l-2 border-amber-300': selected?.id === p.id,
                'hover:bg-green-50/60': isStartklar(p) && selected?.id !== p.id,
                'hover:bg-blue-50': !isStartklar(p) && selected?.id !== p.id,
              }"
              @click="select(p)"
            >
              <td class="py-2 px-3 font-black text-gray-700">
                <span v-if="p.start_number">#{{ p.start_number }}</span>
                <span v-else class="text-xs text-gray-300 font-normal italic">ausstehend</span>
                <span v-if="isStartklar(p)" class="ml-1 text-green-500 text-xs">★</span>
              </td>
              <td class="py-2 px-3 font-semibold text-gray-800">
                {{ p.first_name }} {{ p.last_name }}
                <div class="text-xs text-gray-400 font-normal">{{ p.club_name || 'n.N.' }}</div>
              </td>
              <td class="py-2 px-3 text-gray-500 text-xs">{{ p.birth_year || '–' }}</td>
              <td class="py-2 px-3">
                <div class="flex items-center justify-center gap-1">
                  <button @click.stop="toggleFee(p)"
                    class="text-xs font-bold px-1.5 py-0.5 rounded transition"
                    :class="p.fee_paid ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-gray-100 text-gray-400 hover:bg-amber-100 hover:text-amber-600'"
                    title="Nenngeld bezahlt">€</button>
                  <button @click.stop="toggleHelmet(p)"
                    class="text-xs font-bold px-1.5 py-0.5 rounded transition"
                    :class="p.helmet_ok ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-gray-100 text-gray-400 hover:bg-amber-100 hover:text-amber-600'"
                    title="Helmkontrolle">🪖</button>
                </div>
              </td>
              <td class="py-2 px-3 text-center">
                <span :class="statusBadge(p.status)">{{ statusLabel(p.status) }}</span>
              </td>
              <td class="py-2 px-3 text-center">
                <button v-if="p.status === 'registered'"
                  @click.stop="quickStatus(p, 'checked_in')"
                  class="text-xs bg-amber-500 hover:bg-amber-600 text-white font-bold px-2 py-0.5 rounded-lg transition">
                  Check-in</button>
                <template v-else-if="p.status === 'checked_in'">
                  <button v-if="isStartklar(p)"
                    @click.stop="quickStatus(p, 'technical_ok')"
                    class="text-xs bg-green-600 hover:bg-green-700 text-white font-bold px-2 py-0.5 rounded-lg transition">
                    Freigeben ✓</button>
                  <span v-else class="text-xs text-amber-600 font-semibold">
                    <span v-if="!p.fee_paid">€ </span>
                    <span v-if="!p.helmet_ok">🪖 </span>fehlt
                  </span>
                </template>
              </td>
            </tr>
            <tr v-if="filtered.length === 0">
              <td colspan="6" class="py-6 text-center text-sm text-gray-400">Keine Teilnehmer gefunden</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ═══ NUMMERN-VERGABE-MODUS ═══ -->
      <div v-if="mode === 'numbers'" class="space-y-4">
        <div v-for="cls in store.classes" :key="cls.id" class="card overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between bg-gray-50">
            <h3 class="font-bold text-sm text-gray-800">{{ cls.name }}</h3>
            <div class="flex items-center gap-3">
              <span class="text-xs text-gray-400">
                {{ participantsByClass(cls.id).filter(p => p.start_number).length }}
                / {{ participantsByClass(cls.id).length }} vergeben
              </span>
              <button
                v-if="participantsByClass(cls.id).length > 0"
                @click="autoNumber(cls.id)"
                :disabled="autoNumbering[cls.id]"
                class="text-xs px-2.5 py-1 rounded-lg bg-msc-blue hover:bg-msc-bluedark text-white font-bold transition disabled:opacity-40"
                title="Startnummern per Zufallsauslosung vergeben (1, 2, 3 …)"
              >
                {{ autoNumbering[cls.id] ? '…' : '🎲 Auto ab 1' }}
              </button>
            </div>
          </div>
          <div v-if="participantsByClass(cls.id).length === 0" class="px-4 py-3 text-sm text-gray-400 text-center">
            Keine Teilnehmer
          </div>
          <div v-else class="divide-y divide-gray-100">
            <div v-for="p in participantsByClass(cls.id)" :key="p.id"
                 class="flex items-center gap-3 px-4 py-2.5">
              <div class="flex-1 min-w-0">
                <span class="font-semibold text-sm text-gray-800">{{ p.first_name }} {{ p.last_name }}</span>
                <span class="text-xs text-gray-400 ml-2">{{ p.birth_year || '' }}</span>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <span class="text-xs text-gray-400">#</span>
                <input
                  :value="numberDraft[p.id] ?? p.start_number ?? ''"
                  @input="numberDraft[p.id] = $event.target.value ? parseInt($event.target.value) : null"
                  @keydown.enter.prevent="saveNumber(p)"
                  @blur="saveNumber(p)"
                  type="number"
                  min="1"
                  placeholder="–"
                  class="w-16 border-2 rounded-lg px-2 py-1 text-center font-black font-mono text-sm focus:outline-none focus:ring-2 focus:ring-msc-blue"
                  :class="p.start_number ? 'border-green-300 bg-green-50' : 'border-gray-200'"
                >
              </div>
            </div>
          </div>
        </div>
        <p class="text-xs text-gray-400 text-center">
          Startnummer eingeben + Enter oder Klick außerhalb → sofort gespeichert ·
          „🎲 Auto ab 1" vergibt 1, 2, 3 … alphabetisch (überschreibt vorhandene Nummern)
        </p>
      </div>

      <!-- ═══ DOWNHILL STARTERLISTE ═══ -->
      <div v-if="mode === 'schedule'" class="space-y-4">

        <!-- Startzeiten generieren -->
        <div class="card p-4 space-y-3">
          <h3 class="font-bold text-gray-700 text-sm uppercase tracking-widest">Startzeiten generieren</h3>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-gray-500 font-semibold block mb-1">Erste Startzeit</label>
              <input v-model="schedFirstStart" type="time" step="1" class="input font-mono">
            </div>
            <div>
              <label class="text-xs text-gray-500 font-semibold block mb-1">Startintervall</label>
              <select v-model="schedInterval" class="input">
                <option value="30">30 Sekunden</option>
                <option value="45">45 Sekunden</option>
                <option value="60">1 Minute</option>
                <option value="90">90 Sekunden</option>
                <option value="120">2 Minuten</option>
                <option value="custom">Benutzerdefiniert</option>
              </select>
            </div>
          </div>
          <div v-if="schedInterval === 'custom'" class="flex items-center gap-2">
            <label class="text-xs text-gray-500 font-semibold shrink-0">Sekunden:</label>
            <input v-model.number="schedCustomInterval" type="number" min="10" max="600" class="input w-24">
          </div>
          <div class="flex items-center gap-2">
            <button @click="generateSchedule"
              :disabled="!schedFirstStart || !participantsForSchedule.length"
              class="flex-1 btn-primary py-2 disabled:opacity-40">
              ⚡ Startzeiten generieren ({{ participantsForSchedule.length }} Starter)
            </button>
            <button v-if="schedule.length" @click="clearSchedule"
              class="text-xs font-bold px-3 py-2 rounded-lg bg-red-50 hover:bg-red-100 text-red-600 hover:text-red-700 transition">
              🗑 Alle löschen
            </button>
          </div>
          <p class="text-xs text-gray-400">
            Starter werden in Reihenfolge der Startnummer eingeplant.
            Nur Teilnehmer mit vergebener Startnummer werden berücksichtigt.
          </p>
        </div>

        <!-- Aktuelle Starterliste -->
        <div class="card overflow-hidden">
          <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h3 class="font-bold text-gray-700">
              Starterliste
              <span class="text-gray-400 font-normal text-sm">({{ schedule.length }})</span>
              <span v-if="schedule.filter(s => s.finished).length" class="ml-2 text-xs text-green-600 font-normal">
                {{ schedule.filter(s => s.finished).length }} abgeschlossen
              </span>
            </h3>
            <label class="text-xs font-bold px-2.5 py-1 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 transition cursor-pointer"
                   title="CSV importieren (Spalten: Startnr.,HH:MM:SS)">
              📥 CSV Import
              <input type="file" accept=".csv,.txt" class="hidden" @change="importScheduleCsv">
            </label>
          </div>
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider border-b border-gray-200">
                <th class="py-2.5 px-3 text-left">Startzeit</th>
                <th class="py-2.5 px-3 text-left">Nr.</th>
                <th class="py-2.5 px-3 text-left">Fahrer</th>
                <th class="py-2.5 px-3 text-center">Status</th>
                <th class="py-2.5 px-3 text-center">Aktion</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="s in schedule" :key="s.id"
                  :class="s.finished ? 'opacity-60 bg-green-50/40' : ''">
                <td class="py-2 px-3 font-mono text-xs font-bold text-gray-700">
                  {{ s.scheduled_start ? s.scheduled_start.slice(11, 19) : '–' }}
                </td>
                <td class="py-2 px-3 font-black text-gray-700">
                  <span v-if="s.start_number">#{{ s.start_number }}</span>
                  <span v-else class="text-gray-300 font-normal">–</span>
                </td>
                <td class="py-2 px-3 font-semibold text-gray-800">
                  {{ s.first_name }} {{ s.last_name }}
                </td>
                <td class="py-2 px-3 text-center">
                  <span v-if="s.finished"
                    class="text-xs bg-green-100 text-green-700 font-bold rounded-full px-2 py-0.5">✓ Finish</span>
                  <span v-else class="text-xs text-amber-600">Ausstehend</span>
                </td>
                <td class="py-2 px-3 text-center">
                  <button @click="deleteScheduleEntry(s.id)"
                    class="text-xs text-red-400 hover:text-red-600 font-bold transition"
                    :disabled="s.finished"
                    :class="s.finished ? 'opacity-30 cursor-not-allowed' : ''"
                    title="Eintrag löschen">✕</button>
                </td>
              </tr>
              <tr v-if="schedule.length === 0">
                <td colspan="5" class="py-8 text-center text-sm text-gray-400">
                  Noch keine Startzeiten generiert.<br>
                  <span class="text-xs">Erste Startzeit und Interval oben eingeben, dann „Startzeiten generieren" klicken.</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </section>

    <!-- ── RECHTE SPALTE: Formular ── -->
    <aside class="col-span-full lg:col-span-3">
      <ParticipantCard
        v-if="showForm"
        :participant="selected"
        :error="saveError"
        @save="onFormSave"
        @cancel="cancel"
      />
      <div v-else class="card p-6 text-center text-sm text-gray-400">
        Teilnehmer anklicken zum Bearbeiten
      </div>
    </aside>

  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'
import { printNennliste as _printNennliste } from '../utils/printNennung'
import ParticipantCard from '../components/ParticipantCard.vue'

const store = useEventStore()

const participants  = ref([])
const selected      = ref(null)
const showForm      = ref(false)
const saveError     = ref('')
const filterClass   = ref('')
const filterStatus  = ref('')
const search        = ref('')
const mode          = ref('list')        // 'list' | 'numbers'
const numberDraft   = reactive({})       // { participantId: value }
const importResult  = ref(null)          // { imported, skipped, errors }
const autoNumbering = reactive({})       // { classId: true } während Auto-Vergabe läuft

async function importCsv(evt) {
  const file = evt.target.files?.[0]
  evt.target.value = ''   // reset so same file can be selected again
  if (!file || !store.activeEvent) return
  const fd = new FormData()
  fd.append('file', file)
  try {
    const { data } = await api.post(
      `/events/${store.activeEvent.id}/import-participants`,
      fd,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    importResult.value = data
    if (data.errors.length) console.warn('Import-Fehler:', data.errors)
    await loadParticipants()
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler beim Import')
  }
}

// Nennungsschluss
const closingClassId   = ref(null)
const closingStartTime = ref('')

function isStartklar(p) {
  return p.fee_paid && p.helmet_ok
}

const stats = computed(() => {
  const ps = participants.value
  return {
    total:        ps.length,
    no_number:    ps.filter(p => !p.start_number).length,
    technical_ok: ps.filter(p => p.status === 'technical_ok').length,
    disqualified: ps.filter(p => p.status === 'disqualified').length,
    startklar:    ps.filter(p => isStartklar(p)).length,
    fee_open:     ps.filter(p => !p.fee_paid).length,
    helmet_open:  ps.filter(p => !p.helmet_ok).length,
  }
})

const STATUS_ORDER = { registered: 0, checked_in: 1, technical_ok: 2, disqualified: 3 }

const filtered = computed(() => {
  let list = participants.value
  if (filterClass.value)  list = list.filter(p => p.class_id === filterClass.value)
  if (filterStatus.value === 'no_number')   list = list.filter(p => !p.start_number)
  else if (filterStatus.value === 'startklar') list = list.filter(p => isStartklar(p))
  else if (filterStatus.value === 'pending')   list = list.filter(p => !isStartklar(p) && p.status !== 'disqualified')
  else if (filterStatus.value)  list = list.filter(p => p.status === filterStatus.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(p =>
      p.first_name.toLowerCase().includes(q) ||
      p.last_name.toLowerCase().includes(q) ||
      String(p.start_number ?? '').includes(q)
    )
  }
  // Sortierung: 1. Status  2. Klasse (Reihenfolge im Event)  3. Jahrgang  4. Nachname
  const classOrder = new Map(store.classes.map((c, i) => [c.id, i]))
  return [...list].sort((a, b) => {
    const sd = (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9)
    if (sd !== 0) return sd
    const cd = (classOrder.get(a.class_id) ?? 99) - (classOrder.get(b.class_id) ?? 99)
    if (cd !== 0) return cd
    const yd = (a.birth_year ?? 0) - (b.birth_year ?? 0)
    if (yd !== 0) return yd
    return a.last_name.localeCompare(b.last_name, 'de')
  })
})

function participantsByClass(classId) {
  return participants.value
    .filter(p => p.class_id === classId)
    .sort((a, b) => (a.last_name > b.last_name ? 1 : -1))
}

async function load() {
  if (!store.activeEvent) return
  const { data } = await api.get(`/events/${store.activeEvent.id}/participants`)
  participants.value = data
}

function select(p) {
  selected.value = p
  showForm.value = true
  saveError.value = ''
}

function openNew() {
  selected.value = null
  showForm.value = true
  saveError.value = ''
}

function cancel() {
  selected.value = null
  showForm.value = false
  saveError.value = ''
}

async function onFormSave(formData) {
  if (!store.activeEvent) return
  saveError.value = ''
  try {
    if (selected.value) {
      await api.patch(`/events/${store.activeEvent.id}/participants/${selected.value.id}`, formData)
    } else {
      await api.post(`/events/${store.activeEvent.id}/participants`, { ...formData, event_id: store.activeEvent.id })
    }
    await load(); cancel()
  } catch (e) {
    saveError.value = e.response?.data?.detail || 'Fehler beim Speichern'
  }
}

async function quickStatus(p, status) {
  if (!store.activeEvent) return
  await api.patch(`/events/${store.activeEvent.id}/participants/${p.id}`, { status })
  await load()
}

async function toggleFee(p) {
  if (!store.activeEvent) return
  await api.patch(`/events/${store.activeEvent.id}/participants/${p.id}`, { fee_paid: !p.fee_paid })
  await load()
}

async function toggleHelmet(p) {
  if (!store.activeEvent) return
  await api.patch(`/events/${store.activeEvent.id}/participants/${p.id}`, { helmet_ok: !p.helmet_ok })
  await load()
}

async function saveNumber(p) {
  if (!store.activeEvent) return
  const val = numberDraft[p.id]
  if (val === undefined) return          // nicht verändert
  if (val === p.start_number) { delete numberDraft[p.id]; return }
  try {
    await api.patch(`/events/${store.activeEvent.id}/participants/${p.id}`, { start_number: val || null })
    delete numberDraft[p.id]
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Startnummer bereits vergeben')
  }
}

function shuffled(arr) {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

async function autoNumber(classId) {
  if (!store.activeEvent) return
  const ps = participantsByClass(classId)
  if (!ps.length) return

  const hasNumbers = ps.some(p => p.start_number)
  if (hasNumbers && !confirm(
    `Klasse hat bereits Startnummern.\nAlle Nummern neu auslosen (Zufallsreihenfolge)?`
  )) return

  autoNumbering[classId] = true
  try {
    // Erst alle auf null setzen um Unique-Konflikte beim Neu-Vergeben zu vermeiden
    await Promise.all(ps.map(p =>
      api.patch(`/events/${store.activeEvent.id}/participants/${p.id}`, { start_number: null })
    ))
    // Zufällig mischen, dann 1, 2, 3 …
    const randomized = shuffled(ps)
    for (let i = 0; i < randomized.length; i++) {
      await api.patch(`/events/${store.activeEvent.id}/participants/${randomized[i].id}`, { start_number: i + 1 })
    }
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler bei der Auslosung')
    await load()
  } finally {
    delete autoNumbering[classId]
  }
}

// Nennungsschluss
function openNennungsschluss(cls) {
  closingClassId.value = cls.id
  // Vorschlag: 30 min vor Startzeit falls schon eine spätere Klasse eine hat
  closingStartTime.value = ''
}

async function saveNennungsschluss(cls) {
  if (!store.activeEvent || !closingStartTime.value) return
  const now = new Date().toISOString()
  await api.patch(`/events/${store.activeEvent.id}/classes/${cls.id}`, {
    registration_closed_at: now,
    start_time: closingStartTime.value,
  })
  closingClassId.value = null
  closingStartTime.value = ''
  await store.selectEvent(store.activeEvent)
  await api.post(`/events/${store.activeEvent.id}/classes/${cls.id}/announce`).catch(() => {})
}

async function announceClass(cls) {
  if (!store.activeEvent) return
  await api.post(`/events/${store.activeEvent.id}/classes/${cls.id}/announce`).catch(() => {})
}

function printNennungsformular(p) {
  if (!store.activeEvent) return
  _printNennungsformular(api, store.activeEvent, store.classes, p)
}

function printNennliste() {
  if (!store.activeEvent) return
  _printNennliste(api, store.activeEvent, store.classes, participants.value)
}

// ── Downhill Starterliste ─────────────────────────────────────────────────────
const isDownhill          = computed(() => store.activeEvent?.timing_mode === 'downhill')
const schedule            = ref([])
const schedFirstStart     = ref('')
const schedInterval       = ref('60')
const schedCustomInterval = ref(60)

const participantsForSchedule = computed(() =>
  [...participants.value]
    .filter(p => p.start_number)
    .sort((a, b) => (a.start_number ?? 9999) - (b.start_number ?? 9999))
)

async function loadSchedule() {
  if (!store.activeEvent || !isDownhill.value) return
  try {
    const { data } = await api.get(`/events/${store.activeEvent.id}/schedule`)
    schedule.value = data
  } catch { schedule.value = [] }
}

async function generateSchedule() {
  if (!store.activeEvent || !schedFirstStart.value) return
  const ps = participantsForSchedule.value
  if (!ps.length) { alert('Keine Teilnehmer mit Startnummer vorhanden.'); return }
  const intervalSec = schedInterval.value === 'custom'
    ? (schedCustomInterval.value || 60)
    : parseInt(schedInterval.value)
  const today   = new Date().toISOString().slice(0, 10)
  const firstMs = new Date(`${today}T${schedFirstStart.value}`).getTime()
  const entries = ps.map((p, i) => ({
    participant_id:  p.id,
    lane:            null,
    scheduled_start: new Date(firstMs + i * intervalSec * 1000).toISOString(),
  }))
  try {
    const { data } = await api.post(`/events/${store.activeEvent.id}/schedule/bulk`, entries)
    schedule.value = data
  } catch (e) {
    alert(e.response?.data?.detail || 'Fehler beim Generieren der Startzeiten')
  }
}

async function deleteScheduleEntry(id) {
  if (!store.activeEvent) return
  try {
    await api.delete(`/events/${store.activeEvent.id}/schedule/${id}`)
    await loadSchedule()
  } catch (e) { alert(e.response?.data?.detail || 'Fehler beim Löschen') }
}

async function clearSchedule() {
  if (!store.activeEvent || !schedule.value.length) return
  if (!confirm(`Alle ${schedule.value.length} Startzeiten wirklich löschen?`)) return
  try {
    for (const s of schedule.value)
      await api.delete(`/events/${store.activeEvent.id}/schedule/${s.id}`)
    schedule.value = []
  } catch { await loadSchedule() }
}

async function importScheduleCsv(evt) {
  const file = evt.target.files?.[0]
  evt.target.value = ''
  if (!file || !store.activeEvent) return
  const text  = await file.text()
  const today = new Date().toISOString().slice(0, 10)
  const lines = text.trim().split(/\r?\n/)
  const start = lines[0]?.match(/^\D/) ? 1 : 0
  const entries = []
  for (const line of lines.slice(start)) {
    const [numStr, timeStr] = line.split(',').map(s => s.trim().replace(/"/g, ''))
    if (!numStr || !timeStr) continue
    const p = participants.value.find(pp => String(pp.start_number) === numStr)
    if (!p) continue
    const dt = new Date(`${today}T${timeStr}`)
    if (isNaN(dt.getTime())) continue
    entries.push({ participant_id: p.id, lane: null, scheduled_start: dt.toISOString() })
  }
  if (!entries.length) { alert('Keine gültigen Einträge gefunden (Format: Startnr.,HH:MM:SS)'); return }
  try {
    const { data } = await api.post(`/events/${store.activeEvent.id}/schedule/bulk`, entries)
    schedule.value = data
  } catch (e) { alert(e.response?.data?.detail || 'Fehler beim CSV-Import') }
}

onMounted(async () => {
  if (!store.classes.length) await store.loadEvents()
  await load()
  if (isDownhill.value) await loadSchedule()
})
watch(() => store.activeEvent, async () => {
  await load()
  if (isDownhill.value) await loadSchedule()
})

function statusLabel(s) {
  return { planned: 'Geplant', running: 'Läuft', preliminary: 'Vorläufig', technical_ok: 'Freigegeben', registered: 'Gemeldet', checked_in: 'Eingecheckt', disqualified: 'DSQ', official: 'Offiziell' }[s] || s
}
function statusBadge(s) {
  return { registered: 'badge-info', checked_in: 'badge-warn', technical_ok: 'badge-ok', disqualified: 'badge-danger' }[s] || 'badge-gray'
}
</script>
