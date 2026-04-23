<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">

    <!-- Header -->
    <header class="bg-msc-blue text-white shadow-lg">
      <div class="max-w-lg mx-auto px-4 py-4 flex items-center gap-3">
        <img src="/msc-logo.svg" alt="MSC" class="h-12 w-12 rounded-full border-2 border-white/30">
        <div>
          <div class="font-black text-xl leading-tight">Online-Nennung</div>
          <div class="text-blue-200 text-sm">{{ eventInfo?.name || 'MSC Braach e.V. im ADAC' }}</div>
        </div>
      </div>
    </header>

    <main class="flex-1 max-w-lg mx-auto w-full px-4 py-6">

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-24 gap-4">
        <div class="h-12 w-12 border-4 border-msc-blue border-t-transparent rounded-full animate-spin"></div>
        <p class="text-gray-500">Veranstaltung wird geladen…</p>
      </div>

      <!-- No event -->
      <div v-else-if="!eventInfo" class="card p-8 text-center space-y-3">
        <div class="text-5xl">📅</div>
        <h2 class="font-bold text-gray-800 text-lg">Keine aktive Veranstaltung</h2>
        <p class="text-gray-500 text-sm">Aktuell ist keine Veranstaltung geöffnet.<br>Bitte wende dich an die Nennannahme.</p>
      </div>

      <!-- SUCCESS screen -->
      <div v-else-if="result?.status === 'created'" class="space-y-4">
        <div class="card p-8 text-center space-y-4">
          <div class="h-20 w-20 rounded-full bg-green-100 flex items-center justify-center mx-auto">
            <span class="text-4xl">✓</span>
          </div>
          <h2 class="font-black text-2xl text-green-700">Erfolgreich gemeldet!</h2>
          <div class="bg-gray-50 rounded-2xl p-4 space-y-1.5 text-left">
            <div class="flex justify-between text-sm">
              <span class="text-gray-500">Startnummer</span>
              <span class="font-black text-2xl text-msc-blue">#{{ result.participant.start_number }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-500">Name</span>
              <span class="font-semibold">{{ result.participant.first_name }} {{ result.participant.last_name }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-500">Klasse</span>
              <span class="font-semibold">{{ result.participant.class_name || '–' }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-500">Status</span>
              <span class="font-semibold text-amber-600">Gemeldet – bitte Check-in am Zelt</span>
            </div>
          </div>
          <p class="text-xs text-gray-400">Bitte gehe zur Nennannahme für Check-in und technische Abnahme.</p>
        </div>
        <button @click="resetForm" class="w-full btn-secondary py-3 text-sm font-semibold">
          Weitere Person anmelden
        </button>
      </div>

      <!-- DUPLICATE screen -->
      <div v-else-if="result?.status === 'duplicate'" class="space-y-4">
        <div class="card p-8 text-center space-y-4">
          <div class="h-20 w-20 rounded-full bg-amber-100 flex items-center justify-center mx-auto">
            <span class="text-4xl">⚠️</span>
          </div>
          <h2 class="font-black text-2xl text-amber-700">Bereits gemeldet</h2>
          <p class="text-gray-600 text-sm">Diese Person ist für die heutige Veranstaltung bereits in der Nennliste.</p>
          <div class="bg-amber-50 border border-amber-200 rounded-2xl p-4 space-y-1.5 text-left">
            <div class="flex justify-between text-sm">
              <span class="text-gray-500">Startnummer</span>
              <span class="font-black text-2xl text-msc-blue">#{{ result.participant.start_number }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-500">Name</span>
              <span class="font-semibold">{{ result.participant.first_name }} {{ result.participant.last_name }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-gray-500">Klasse</span>
              <span class="font-semibold">{{ result.participant.class_name || '–' }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-400">Falls das ein Fehler ist, wende dich bitte an die Nennannahme.</p>
        </div>
        <button @click="resetForm" class="w-full btn-secondary py-3 text-sm font-semibold">
          Zurück zum Formular
        </button>
      </div>

      <!-- FORM -->
      <form v-else @submit.prevent="submit" class="space-y-4">

        <!-- Event-Badge -->
        <div class="bg-msc-blue/10 border border-msc-blue/20 rounded-2xl px-4 py-3 flex items-center gap-3">
          <span class="text-2xl">🏁</span>
          <div>
            <div class="font-bold text-msc-blue text-sm">{{ eventInfo.name }}</div>
            <div class="text-xs text-gray-500">{{ formatDate(eventInfo.date) }} · {{ eventInfo.location }}</div>
          </div>
        </div>

        <!-- Name -->
        <div class="card p-4 space-y-3">
          <h3 class="text-xs font-bold uppercase tracking-widest text-gray-400">Persönliche Daten</h3>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs text-gray-500 font-semibold block mb-1">Vorname *</label>
              <input
                v-model="form.first_name"
                type="text"
                required
                autocomplete="given-name"
                placeholder="Max"
                class="input text-base"
              >
            </div>
            <div>
              <label class="text-xs text-gray-500 font-semibold block mb-1">Nachname *</label>
              <input
                v-model="form.last_name"
                type="text"
                required
                autocomplete="family-name"
                placeholder="Mustermann"
                class="input text-base"
              >
            </div>
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Jahrgang *</label>
            <input
              v-model.number="form.birth_year"
              type="number"
              required
              min="1950"
              :max="currentYear"
              placeholder="z.B. 2013"
              class="input text-xl font-bold text-center tabnum"
              @change="updateClassSuggestion"
            >
            <p v-if="suggestedClass" class="text-xs text-green-600 mt-1 font-semibold">
              → Klasse: {{ suggestedClass.name }}
            </p>
          </div>
        </div>

        <!-- Verein + Klasse -->
        <div class="card p-4 space-y-3">
          <h3 class="text-xs font-bold uppercase tracking-widest text-gray-400">Verein &amp; Klasse</h3>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">Verein</label>
            <select v-model.number="form.club_id" class="input text-base">
              <option :value="null">n.N. (noch nicht genannt)</option>
              <option v-for="c in clubs" :key="c.id" :value="c.id">
                {{ c.short_name || c.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">
              Klasse
              <span class="font-normal text-gray-400">(wird auto. per Jahrgang zugewiesen)</span>
            </label>
            <select v-model.number="form.class_id" class="input text-base">
              <option :value="null">– automatisch –</option>
              <option v-for="c in classes" :key="c.id" :value="c.id">
                {{ c.name }}
                <template v-if="c.min_birth_year || c.max_birth_year">
                  (Jg. {{ c.min_birth_year || '…' }}–{{ c.max_birth_year || '…' }})
                </template>
              </option>
            </select>
          </div>
        </div>

        <!-- Lizenznummer -->
        <div class="card p-4 space-y-3">
          <h3 class="text-xs font-bold uppercase tracking-widest text-gray-400">Lizenz</h3>
          <div>
            <label class="text-xs text-gray-500 font-semibold block mb-1">
              Lizenznummer
              <span class="font-normal text-gray-400">(optional)</span>
            </label>
            <input
              v-model="form.license_number"
              type="text"
              placeholder="z.B. HE-12345"
              autocomplete="off"
              class="input font-mono text-base uppercase"
            >
            <p class="text-xs text-gray-400 mt-1">Wird auch zur Duplikatserkennung verwendet</p>
          </div>
        </div>

        <!-- Error -->
        <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
          {{ error }}
        </div>

        <!-- Submit -->
        <button
          type="submit"
          :disabled="submitting || !form.first_name || !form.last_name || !form.birth_year"
          class="w-full bg-msc-blue hover:bg-msc-bluedark text-white font-black text-lg py-4 rounded-2xl transition disabled:opacity-40 shadow-lg"
        >
          <span v-if="submitting" class="flex items-center justify-center gap-2">
            <span class="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin inline-block"></span>
            Wird gesendet…
          </span>
          <span v-else>Jetzt anmelden →</span>
        </button>

        <p class="text-center text-xs text-gray-400">
          Probleme? Bitte wende dich an die Nennannahme.
        </p>
      </form>

    </main>

    <!-- Footer -->
    <footer class="text-center text-xs text-gray-400 py-4 border-t border-gray-100">
      RaceControl Pro · MSC Braach e.V. im ADAC
    </footer>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/client'

const loading    = ref(true)
const submitting = ref(false)
const error      = ref('')
const result     = ref(null)

const eventInfo = ref(null)
const classes   = ref([])
const clubs     = ref([])

const currentYear = new Date().getFullYear()

const form = ref({
  first_name: '',
  last_name: '',
  birth_year: null,
  club_id: null,
  class_id: null,
  license_number: '',
})

const suggestedClass = computed(() => {
  if (!form.value.birth_year || form.value.class_id) return null
  return classes.value.find(c => {
    const yr = form.value.birth_year
    const minOk = !c.min_birth_year || yr >= c.min_birth_year
    const maxOk = !c.max_birth_year || yr <= c.max_birth_year
    return minOk && maxOk
  }) || null
})

function updateClassSuggestion() {
  if (suggestedClass.value && !form.value.class_id) {
    // Don't auto-set — let the user see the suggestion but choose manually
  }
}

async function loadEvent() {
  loading.value = true
  try {
    const { data } = await api.get('/public/active-event')
    eventInfo.value = data.event
    classes.value   = data.classes
    clubs.value     = data.clubs
  } catch {
    eventInfo.value = null
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!eventInfo.value) return
  error.value    = ''
  submitting.value = true
  try {
    const payload = {
      first_name:     form.value.first_name.trim(),
      last_name:      form.value.last_name.trim(),
      birth_year:     form.value.birth_year || null,
      club_id:        form.value.club_id || null,
      class_id:       form.value.class_id || null,
      license_number: form.value.license_number?.trim() || null,
    }
    const { data } = await api.post(
      `/public/events/${eventInfo.value.id}/register`,
      payload
    )
    result.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || 'Fehler beim Senden – bitte erneut versuchen'
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  result.value = null
  error.value  = ''
  form.value = {
    first_name: '', last_name: '', birth_year: null,
    club_id: null, class_id: null, license_number: '',
  }
}

function formatDate(d) {
  if (!d) return ''
  const [y, m, day] = d.split('-')
  return `${day}.${m}.${y}`
}

onMounted(loadEvent)
</script>
