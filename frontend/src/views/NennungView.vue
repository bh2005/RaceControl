<template>
  <div class="max-w-7xl mx-auto px-4 py-4 pb-12 grid grid-cols-12 gap-4">

    <!-- ── LINKE SPALTE ── -->
    <aside class="col-span-3 space-y-3">

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
    <section class="col-span-6 space-y-2">

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

    </section>

    <!-- ── RECHTE SPALTE: Formular ── -->
    <aside class="col-span-3">
      <div v-if="form" class="card p-4 space-y-3">
        <h2 class="font-bold text-gray-800 flex items-center gap-2">
          <span class="h-2.5 w-2.5 rounded-full" :class="selected ? 'bg-amber-400' : 'bg-green-500'"></span>
          {{ selected ? `Bearbeiten: ${form.start_number ? '#' + form.start_number : form.last_name}` : 'Nachnennung' }}
        </h2>

        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Startnummer</label>
            <input v-model.number="form.start_number" type="number"
              placeholder="nach Auslosung" class="input font-bold">
            <p class="text-xs text-gray-400 mt-0.5">Wird nach Auslosung vergeben</p>
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Jahrgang</label>
            <input v-model.number="form.birth_year" type="number" placeholder="2013" class="input">
          </div>
        </div>

        <div>
          <label class="text-xs text-gray-500 font-semibold block mb-1">Geschlecht</label>
          <select v-model="form.gender" class="input">
            <option :value="null">– nicht angegeben –</option>
            <option value="m">Männlich</option>
            <option value="w">Weiblich</option>
          </select>
        </div>

        <div>
          <label class="text-xs text-gray-500 font-semibold block mb-1">Vorname</label>
          <input v-model="form.first_name" type="text" class="input">
        </div>
        <div>
          <label class="text-xs text-gray-500 font-semibold block mb-1">Nachname</label>
          <input v-model="form.last_name" type="text" class="input">
        </div>

        <div>
          <label class="text-xs text-gray-500 font-semibold block mb-1">Verein</label>
          <select v-model.number="form.club_id" class="input">
            <option :value="null">n.N.</option>
            <option v-for="c in store.clubs" :key="c.id" :value="c.id">{{ c.short_name || c.name }}</option>
          </select>
        </div>

        <div>
          <label class="text-xs text-gray-500 font-semibold block mb-1">Klasse</label>
          <select v-model.number="form.class_id" class="flex-1 input">
            <option :value="null">– automatisch –</option>
            <option v-for="c in store.classes" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>

        <div>
          <label class="text-xs text-gray-500 font-semibold block mb-1">Lizenznummer</label>
          <input v-model="form.license_number" type="text" placeholder="HE-12345" class="input font-mono">
        </div>

        <div v-if="selected">
          <label class="text-xs text-gray-500 font-semibold block mb-1">Status</label>
          <select v-model="form.status" class="input">
            <option value="registered">Gemeldet</option>
            <option value="checked_in">Eingecheckt</option>
            <option value="technical_ok">Freigegeben</option>
            <option value="disqualified">Disqualifiziert</option>
          </select>
        </div>

        <div class="border border-gray-200 rounded-xl p-3 space-y-2">
          <div class="text-xs font-bold uppercase tracking-widest text-gray-400 mb-1">Abnahme</div>
          <label class="flex items-center gap-3 cursor-pointer select-none">
            <input v-model="form.fee_paid" type="checkbox" class="h-4 w-4 rounded accent-green-600 cursor-pointer">
            <span class="text-sm font-semibold text-gray-700">€ Nenngeld bezahlt</span>
            <span v-if="form.fee_paid" class="text-xs text-green-600 font-bold ml-auto">✓</span>
          </label>
          <label class="flex items-center gap-3 cursor-pointer select-none">
            <input v-model="form.helmet_ok" type="checkbox" class="h-4 w-4 rounded accent-green-600 cursor-pointer">
            <span class="text-sm font-semibold text-gray-700">🪖 Helmkontrolle OK</span>
            <span v-if="form.helmet_ok" class="text-xs text-green-600 font-bold ml-auto">✓</span>
          </label>
          <div class="text-xs font-bold text-center rounded px-2 py-1 mt-1"
               :class="form.fee_paid && form.helmet_ok ? 'text-green-600 bg-green-50' : 'text-amber-600 bg-amber-50'">
            {{ form.fee_paid && form.helmet_ok ? '★ Startklar' : 'Noch nicht startklar' }}
          </div>
        </div>

        <!-- Nennungsformular drucken — nur wenn Lizenz + Helm + Geld iO -->
        <button
          v-if="selected && selected.license_number && selected.fee_paid && selected.helmet_ok"
          @click="printNennungsformular(selected)"
          class="w-full bg-green-700 hover:bg-green-800 text-white text-sm font-bold py-2 rounded-xl transition flex items-center justify-center gap-2"
        >
          🖨 Offizielles Nennungsformular
        </button>
        <div
          v-else-if="selected"
          class="text-center text-xs text-gray-400 bg-gray-50 rounded-lg py-1.5"
          :title="!selected.license_number ? 'Lizenznummer fehlt' : !selected.fee_paid ? 'Nenngeld fehlt' : 'Helmkontrolle fehlt'"
        >
          🖨 Formular: {{ !selected.license_number ? 'Lizenznr. fehlt' : !selected.fee_paid ? 'Nenngeld offen' : 'Helm ausstehend' }}
        </div>

        <div v-if="saveError" class="text-xs text-red-600 bg-red-50 rounded px-2 py-1">{{ saveError }}</div>
        <div class="flex gap-2 pt-1">
          <button @click="save" class="flex-1 btn-primary py-2">Speichern</button>
          <button @click="cancel" class="btn-secondary py-2 px-3 text-sm">Abbrechen</button>
        </div>
      </div>
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

const store = useEventStore()

const participants  = ref([])
const selected      = ref(null)
const form          = ref(null)
const filterClass   = ref('')
const filterStatus  = ref('')
const search        = ref('')
const saveError     = ref('')
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
  form.value = { ...p }
  saveError.value = ''
}

function openNew() {
  selected.value = null
  form.value = {
    start_number: null, first_name: '', last_name: '',
    birth_year: null, gender: null, club_id: null, class_id: null,
    license_number: '', status: 'registered',
    fee_paid: false, helmet_ok: false,
  }
  saveError.value = ''
}

function cancel() { selected.value = null; form.value = null }

async function save() {
  if (!store.activeEvent) return
  saveError.value = ''
  try {
    if (selected.value) {
      await api.patch(`/events/${store.activeEvent.id}/participants/${selected.value.id}`, form.value)
    } else {
      await api.post(`/events/${store.activeEvent.id}/participants`, { ...form.value, event_id: store.activeEvent.id })
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

async function printNennungsformular(p) {
  if (!store.activeEvent) return
  let cfg = {}
  try { const { data } = await api.get('/settings/'); cfg = data } catch { /* ignore */ }

  const event = store.activeEvent
  const cls   = store.classes.find(c => c.id === p.class_id)
  const esc   = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  const fmtD  = d => { if (!d) return ''; const [y,m,day]=d.split('-'); return `${day}.${m}.${y}` }

  const page1 = `
<div class="page">
  <div class="form-header">
    <div class="form-title">NENNUNGSFORMULAR</div>
    <div class="form-subtitle">für Jugendsport-Veranstaltungen beim ADAC Hessen-Thüringen e.V.</div>
  </div>

  <div class="section-box">
    <div class="section-label">Veranstaltungsdaten:</div>
    <div class="va-types">
      <label><input type="checkbox" checked disabled> <strong>Kartslalom</strong></label>
      <label><input type="checkbox" disabled> Kart-Turnier</label>
      <label><input type="checkbox" disabled> KS 2000</label>
      <label><input type="checkbox" disabled> Mot-Turnier</label>
      <label><input type="checkbox" disabled> Tretcar</label>
      <label><input type="checkbox" disabled> Wassersport</label>
    </div>
    <div class="ev-row">
      <span class="fl">Veranstalter:</span><span class="fv">${esc(cfg.organizer_name || 'MSC Braach e.V. im ADAC')}</span>
      <span class="fl" style="margin-left:16px">Datum:</span><span class="fv">${fmtD(event.date)}</span>
    </div>
    <div class="ev-row">
      <span class="fl">Veranstaltungsort:</span><span class="fv">${esc(event.location || '')}</span>
    </div>
  </div>

  <div class="two-col">
    <div class="pdata">
      <div class="fr"><div class="lbl">Vorname:</div><div class="vbox">${esc(p.first_name)}</div></div>
      <div class="fr"><div class="lbl">Name:</div><div class="vbox">${esc(p.last_name)}</div></div>
      <div class="fr"><div class="lbl">Straße, Hausnr.:</div><div class="vbox"></div></div>
      <div class="fr"><div class="lbl">PLZ/Wohnort:</div><div class="vbox"></div></div>
      <div class="fr">
        <div class="lbl">Geb.-Datum:</div><div class="vbox short">${p.birth_year ? 'Jg.&nbsp;' + p.birth_year : ''}</div>
        <div class="lbl" style="margin-left:6px">Jugend/Ü18-Ausw.-Nr.:</div><div class="vbox">${esc(p.license_number || '')}</div>
      </div>
      <div class="fr"><div class="lbl">Mitglied im ADAC Ortsclub:</div><div class="vbox">${esc(p.club_name || '')}</div></div>
      <div class="fr"><div class="lbl">Jugendleiter des Ortsclubs:</div><div class="vbox"></div></div>
    </div>

    <div class="vbox-right">
      <div class="vbox-title">Vom Veranstalter auszufüllen:</div>
      <div class="vr-field"><span class="big-lbl">START-NR.</span><span class="big-val">${p.start_number ? '#' + p.start_number : '–'}</span></div>
      <div class="vr-field"><span class="big-lbl">KLASSE</span><span class="big-val">${esc(cls?.short_name || cls?.name || '')}</span></div>
      <div class="vr-check"><label><input type="checkbox" checked disabled> ADAC Jugend/Ü18-Ausweis kontrolliert: <strong>✓</strong></label></div>
      <div class="vr-check"><label><input type="checkbox" checked disabled> Helm homologiert: <strong>✓</strong></label></div>
      <div class="vr-field small"><span class="lbl">Bemerkung:</span><span class="sline"></span></div>
      <div class="vr-field small" style="margin-top:10px"><span class="lbl">Unterschrift:</span><span class="sline"></span></div>
    </div>
  </div>

  <div class="legal">
    <p><strong>Ausschreibung:</strong> Ich/Wir habe/n die Rahmenausschreibung des ADAC Hessen-Thüringen für die oben angekreuzte Veranstaltungsart im Wortlaut zur Kenntnis genommen und genehmige/n die Teilnahme.</p>
    <p><strong>Datenschutz:</strong> Mit Abgabe dieser Nennung und Teilnahme an dieser Veranstaltung erklärt sich der Teilnehmer bzw. seine Erziehungsberechtigten mit der elektronischen Speicherung der wettkampfrelevanten Daten und der Veröffentlichung der Startlisten und Ergebnisse in Aushängen, im Internet und in den Publikationen des Vereins/Verbandes sowie in Pressemitteilungen einverstanden.</p>
    <p><strong>Fotos:</strong> Ich habe / wir haben zur Kenntnis genommen, dass – sollte ich / sollten wir nicht wünschen, dass Fotos von meinem/unserem Kind im Rahmen der Veranstaltung veröffentlicht werden – dies zusammen mit dieser Nennung auf einem gesonderten Schriftstück erklärt werden muss.</p>
  </div>

  <div class="sig-section">
    <div class="sig-row">
      <div class="si"><div class="sline-l"></div><div class="sc">Datum</div></div>
      <div class="si"><div class="sline-l"></div><div class="sc">Unterschrift des Teilnehmers</div></div>
      <div class="si"><div class="sline-l"></div><div class="sc">Unterschrift des/der Erziehungsberechtigten</div></div>
    </div>
  </div>

  <table class="res-table">
    <thead>
      <tr><th colspan="3">1. Lauf</th><th colspan="3">2. Lauf</th><th>Fahrzeit insgesamt</th></tr>
      <tr><th>Fahrzeit</th><th>Fehlerpunkte</th><th>Gesamt</th><th>Fahrzeit</th><th>Fehlerpunkte</th><th>Gesamt</th><th></th></tr>
    </thead>
    <tbody><tr><td class="rt"></td><td class="rt"></td><td class="rt"></td><td class="rt"></td><td class="rt"></td><td class="rt"></td><td class="rt"></td></tr></tbody>
  </table>
</div>`

  const page2 = `
<div class="page page-break">
  <div class="form-header">
    <div class="form-title" style="font-size:13pt">Haftungsausschluss</div>
  </div>
  <div class="haftung-fields">
    <div><strong>Titel der Veranstaltung:</strong> ${esc(event.name)}</div>
    <div><strong>Name des Fahrers/Bewerbers:</strong> ${esc(p.last_name)}, ${esc(p.first_name)}</div>
  </div>
  <div class="haftung-text">
    <p>Die Teilnehmer nehmen auf eigene Gefahr an den Veranstaltungen teil. Sie tragen die alleinige zivil- und strafrechtliche Verantwortung für alle von ihnen oder dem von ihnen benutzten Fahrzeug verursachten Schäden. Sie erklären den Verzicht auf Ansprüche jeder Art für Schäden, die im Zusammenhang mit der Veranstaltung entstehen, und zwar gegenüber</p>
    <ul>
      <li>den eigenen Teilnehmer (anderslautende Vereinbarungen zwischen den Teilnehmer gehen vor!) und Helfern,</li>
      <li>den jeweils anderen Teilnehmern, den Eigentümern und Haltern aller an der Veranstaltung teilnehmenden Fahrzeuge (soweit die Veranstaltung auf einer permanenten oder temporär geschlossenen Strecke stattfindet) und deren Helfern,</li>
      <li>der FIA, der CIK, dem DMSB, den Mitgliedsorganisationen des DMSB, deren Präsidenten, Organen, Geschäftsführern und Generalsekretären,</li>
      <li>dem ADAC e.V., den ADAC Regionalclubs, den ADAC Ortsclubs und den mit dem ADAC e.V. verbundenen Unternehmen, deren Präsidenten, Organen, Geschäftsführern, Generalsekretären, den Mitarbeitern und Mitgliedern,</li>
      <li>dem Promotor/Serienorganisator,</li>
      <li>dem Veranstalter, den Sportwarten, den Rennstreckeneigentümern, den Rechtsträgern der Behörden, Renndiensten und allen anderen Personen, die mit der Organisation der Veranstaltung in Verbindung stehen,</li>
      <li>den Straßenbaulastträgern und</li>
      <li>der Erfüllungs- und Verrichtungsgehilfen, den gesetzlichen Vertretern, den haupt- und ehrenamtlichen Mitarbeitern aller zuvor genannten Personen und Stellen sowie deren Mitgliedern.</li>
    </ul>
    <p>Der Haftungsverzicht gilt nicht für Schäden aus der Verletzung des Lebens, des Körpers oder der Gesundheit, für sonstige Schäden, die auf einer vorsätzlichen oder grob fahrlässigen Pflichtverletzung beruhen sowie nicht für Schäden aus der Verletzung einer wesentlichen Vertragspflicht durch den enthafteten Personenkreis. Bei Schäden, die auf einer leicht fahrlässigen Pflichtverletzung von wesentlichen Vertragspflichten beruhen ist die Haftung für Vermögens- und Sachschäden der Höhe nach auf den typischen, vorhersehbaren Schaden beschränkt.</p>
    <p>Der Haftungsverzicht gilt für Ansprüche aus jeglichem Rechtsgrund, insbesondere also für Schadensersatzansprüche aus vertraglicher und ausservertraglicher Haftung und für Ansprüche aus unerlaubter Handlung. Stillschweigende Haftungsausschlüsse bleiben von vorstehender Haftungsausschlussklausel unberührt.</p>
    <p>Mit Abgabe der Nennung nimmt der Teilnehmer davon Kenntnis, dass Versicherungsschutz im Rahmen der Kraftverkehrsversicherungen (Kfz-Haftpflicht, Kasko-Versicherung etc.) für Schäden, die im Rahmen der Veranstaltungen entstehen, nicht gewährt wird. Er verpflichtet sich, auch den Halter und den Eigentümer des eingesetzten Fahrzeugs davon zu unterrichten.</p>
    <p>Im Falle einer im Laufe der Veranstaltung eintretenden oder festgestellten Verletzung bzw. im Falle von gesundheitlichen Schäden, die die automobilsportliche Tauglichkeit auf Dauer oder vorübergehend in Frage stellen können, entbindet der Teilnehmer alle behandelnden Ärzte – im Hinblick auf das sich daraus unter Umständen auch für Dritte ergebende Sicherheitsrisiko – von der ärztlichen Schweigepflicht gegenüber dem DMSB, dem ADAC (ADAC e.V., ADAC Regionalverbände und ADAC Ortsclubs) gegenüber den Rennärzten, Slalomleitern, Schiedsgerichten.</p>
    <p><strong>Mit meiner Unterschrift erkenne ich den o.a. Haftungsausschluss an.</strong></p>
  </div>
  <div class="haftung-sig">
    <div class="sig-row">
      <div class="si"><div class="sline-l"></div><div class="sc">Ort</div></div>
      <div class="si"><div class="sline-l"></div><div class="sc">Datum</div></div>
      <div class="si" style="flex:2"><div class="sline-l"></div><div class="sc">Unterschrift Fahrer/Fahrerin</div></div>
    </div>
    <div class="sig-row" style="margin-top:18px">
      <div class="si" style="flex:2"><div class="sline-l"></div><div class="sc">Unterschrift des/der Erziehungsberechtigten</div></div>
      <div class="si" style="flex:1"><div class="sline-l"></div><div class="sc">/</div></div>
    </div>
    <p class="small-note">Bei Unterschrift nur eines Erziehungsberechtigten bestätigt dieser damit, dass er alleiniger Erziehungsberechtigter ist, bzw. dass das Einverständnis des zweiten Elternteils vorliegt. Bei Alleinigem Sorgerecht ist immer eine entsprechende Bescheinigung mitzuführen und auf Verlangen vorzulegen.</p>
    <p class="small-note" style="margin-top:8px">Stand 2024</p>
  </div>
</div>`

  const html = `<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8">
<title>Nennungsformular – ${esc(p.last_name)}, ${esc(p.first_name)}</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 9.5pt; color: #000; margin: 0; }
  @page { size: A4 portrait; margin: 12mm 14mm; }
  .page { padding: 0; }
  .page-break { page-break-before: always; }
  .form-header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 8px; }
  .form-title { font-size: 16pt; font-weight: bold; letter-spacing: 1px; }
  .form-subtitle { font-size: 10pt; }
  .section-box { border: 1px solid #888; padding: 5px 8px; margin-bottom: 8px; }
  .section-label { font-size: 8pt; font-weight: bold; margin-bottom: 3px; }
  .va-types { display: flex; gap: 14px; flex-wrap: wrap; margin-bottom: 5px; font-size: 9pt; }
  .va-types label { display: flex; align-items: center; gap: 3px; }
  .ev-row { display: flex; align-items: baseline; gap: 4px; margin-top: 3px; font-size: 9pt; flex-wrap: wrap; }
  .fl { font-size: 8pt; color: #555; white-space: nowrap; }
  .fv { font-weight: bold; border-bottom: 1px solid #555; min-width: 80px; padding: 0 3px; }
  .two-col { display: flex; gap: 10px; margin-bottom: 8px; }
  .pdata { flex: 1; }
  .fr { display: flex; align-items: baseline; gap: 3px; margin-bottom: 4px; flex-wrap: wrap; }
  .lbl { font-size: 8pt; color: #555; white-space: nowrap; }
  .vbox { flex: 1; border-bottom: 1px solid #555; min-width: 60px; font-weight: bold; padding: 0 3px; font-size: 9.5pt; min-height: 14px; }
  .vbox.short { flex: 0 0 60px; min-width: 60px; }
  .vbox-right { width: 145px; border: 1.5px solid #333; padding: 6px 8px; flex-shrink: 0; }
  .vbox-title { font-size: 7.5pt; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 3px; margin-bottom: 5px; }
  .vr-field { margin-bottom: 5px; }
  .big-lbl { display: block; font-size: 7.5pt; color: #555; font-weight: bold; }
  .big-val { display: block; font-size: 14pt; font-weight: black; border-bottom: 1px solid #555; min-height: 18px; padding: 0 2px; }
  .vr-check { font-size: 8pt; margin-bottom: 4px; }
  .vr-check input[type=checkbox] { margin-right: 3px; }
  .small .lbl { font-size: 8pt; }
  .sline { display: inline-block; border-bottom: 1px solid #555; flex: 1; min-width: 80px; }
  .legal { font-size: 7.5pt; line-height: 1.4; margin-bottom: 8px; border-top: 1px solid #ccc; padding-top: 5px; }
  .legal p { margin: 0 0 4px; }
  .sig-section { margin-bottom: 8px; }
  .sig-row { display: flex; gap: 12px; }
  .si { flex: 1; }
  .sline-l { border-bottom: 1px solid #333; height: 18px; margin-bottom: 2px; }
  .sc { font-size: 7.5pt; color: #555; text-align: center; }
  .res-table { width: 100%; border-collapse: collapse; margin-top: 6px; font-size: 8.5pt; }
  .res-table th { border: 1px solid #888; background: #e8e8e8; padding: 3px 5px; text-align: center; }
  .res-table td { border: 1px solid #bbb; padding: 0; height: 14mm; }
  .rt { text-align: center; }
  .haftung-fields { font-size: 9pt; border: 1px solid #888; padding: 5px 8px; margin-bottom: 8px; display: flex; gap: 20px; }
  .haftung-text { font-size: 8.5pt; line-height: 1.5; }
  .haftung-text p { margin: 0 0 5px; }
  .haftung-text ul { margin: 3px 0 5px 18px; padding: 0; }
  .haftung-text li { margin-bottom: 2px; }
  .haftung-sig { margin-top: 12px; }
  .small-note { font-size: 7.5pt; color: #444; margin-top: 6px; line-height: 1.4; }
</style>
</head><body>${page1}${page2}</body></html>`

  const w = window.open('', '_blank', 'width=900,height=750')
  if (!w) { alert('Popup wurde blockiert – bitte Popups für diese Seite erlauben.'); return }
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => w.print(), 400)
}

async function printNennliste() {
  if (!store.activeEvent) return
  let cfg = {}
  try { const { data } = await api.get('/settings/'); cfg = data } catch { /* ignore */ }

  const event = store.activeEvent
  const printDate = new Date().toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
  const escHtml = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')

  const classPages = store.classes.map((cls, idx) => {
    const ps = participants.value
      .filter(p => p.class_id === cls.id)
      .sort((a, b) => (a.start_number ?? 9999) - (b.start_number ?? 9999) || a.last_name.localeCompare(b.last_name))

    const rows = ps.map((p, i) => `
      <tr>
        <td class="center">${i + 1}</td>
        <td class="center mono">${p.start_number ? '#' + p.start_number : '–'}</td>
        <td><strong>${escHtml(p.last_name)}</strong>, ${escHtml(p.first_name)}</td>
        <td>${escHtml(p.club_name || 'n.N.')}</td>
        <td class="center">${p.birth_year || '–'}</td>
        <td class="center check">${p.fee_paid ? '✓' : '□'}</td>
        <td class="center check">${p.helmet_ok ? '✓' : '□'}</td>
        <td class="sig"></td>
      </tr>`).join('')

    return `
      <div class="${idx > 0 ? 'page-break' : ''}">
        <div class="event-header">
          <div>
            <h1>${escHtml(event.name)}</h1>
            <div class="meta">${escHtml(event.date.split('-').reverse().join('.'))} · ${escHtml(event.location || '')}</div>
          </div>
          <div class="org">
            <div>${escHtml(cfg.organizer_name || '')}</div>
            <div style="font-size:8pt;color:#666">${escHtml(cfg.organizer_address || '')}</div>
            <div style="font-size:8pt;color:#999;margin-top:4px">Druck: ${printDate}</div>
          </div>
        </div>
        <h2>${escHtml(cls.name)}</h2>
        <table>
          <thead>
            <tr>
              <th class="center" style="width:24px">Nr.</th>
              <th class="center" style="width:36px">St.Nr.</th>
              <th>Name</th>
              <th style="width:90px">Verein</th>
              <th class="center" style="width:36px">Jg.</th>
              <th class="center" style="width:24px">€</th>
              <th class="center" style="width:28px">Helm</th>
              <th style="width:55mm">Unterschrift Fahrer/Erziehungsber.</th>
            </tr>
          </thead>
          <tbody>${rows || '<tr><td colspan="8" style="text-align:center;color:#999">Keine Teilnehmer</td></tr>'}</tbody>
        </table>
        <div class="footer">
          <p><strong>Versicherungshinweis:</strong> ${escHtml(cfg.insurance_notice || '')}</p>
          <p style="margin-top:6px"><strong>Einverständniserklärung:</strong> ${escHtml(cfg.parent_consent_text || '')}</p>
        </div>
      </div>`
  }).join('')

  const html = `<!DOCTYPE html>
<html lang="de"><head><meta charset="UTF-8">
<title>Nennliste – ${escHtml(event.name)}</title>
<style>
  @page { size: A4 portrait; margin: 12mm 15mm; }
  * { box-sizing: border-box; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 10pt; color: #222; }
  h1 { font-size: 13pt; margin: 0 0 2px; }
  h2 { font-size: 11pt; margin: 14px 0 6px; border-bottom: 1.5px solid #333; padding-bottom: 3px; }
  .event-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px; }
  .meta { font-size: 9pt; color: #555; }
  .org { text-align: right; font-size: 9pt; }
  table { width: 100%; border-collapse: collapse; font-size: 9pt; }
  th { background: #e8e8e8; border: 1px solid #888; padding: 3px 5px; text-align: left; font-size: 8.5pt; }
  td { border: 1px solid #bbb; padding: 3px 5px; vertical-align: middle; }
  .center { text-align: center; }
  .mono { font-family: monospace; font-weight: bold; }
  .check { font-size: 12pt; }
  .sig { height: 10mm; }
  .footer { margin-top: 10px; border-top: 1px solid #ccc; padding-top: 6px; font-size: 8pt; color: #444; }
  .page-break { page-break-before: always; }
</style>
</head><body>${classPages}</body></html>`

  const w = window.open('', '_blank', 'width=900,height=700')
  if (!w) { alert('Popup wurde blockiert – bitte Popups für diese Seite erlauben.'); return }
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => w.print(), 400)
}

onMounted(async () => {
  if (!store.classes.length) await store.loadEvents()
  await load()
})
watch(() => store.activeEvent, load)

function statusLabel(s) {
  return { planned: 'Geplant', running: 'Läuft', preliminary: 'Vorläufig', technical_ok: 'Freigegeben', registered: 'Gemeldet', checked_in: 'Eingecheckt', disqualified: 'DSQ', official: 'Offiziell' }[s] || s
}
function statusBadge(s) {
  return { registered: 'badge-info', checked_in: 'badge-warn', technical_ok: 'badge-ok', disqualified: 'badge-danger' }[s] || 'badge-gray'
}
</script>
