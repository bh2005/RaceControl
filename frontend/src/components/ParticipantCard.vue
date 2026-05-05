<template>
  <div class="card p-4 space-y-3">
    <h2 class="font-bold text-gray-800 flex items-center gap-2">
      <span class="h-2.5 w-2.5 rounded-full" :class="participant ? 'bg-amber-400' : 'bg-green-500'"></span>
      {{ participant
        ? `Bearbeiten: ${form.start_number ? '#' + form.start_number : form.last_name}`
        : 'Nachnennung' }}
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

    <div v-if="participant">
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
      v-if="participant && participant.license_number && participant.fee_paid && participant.helmet_ok"
      @click="handlePrint"
      class="w-full bg-green-700 hover:bg-green-800 text-white text-sm font-bold py-2 rounded-xl transition flex items-center justify-center gap-2"
    >
      🖨 Offizielles Nennungsformular
    </button>
    <div
      v-else-if="participant"
      class="text-center text-xs text-gray-400 bg-gray-50 rounded-lg py-1.5"
      :title="!participant.license_number ? 'Lizenznummer fehlt' : !participant.fee_paid ? 'Nenngeld fehlt' : 'Helmkontrolle fehlt'"
    >
      🖨 Formular: {{ !participant.license_number ? 'Lizenznr. fehlt' : !participant.fee_paid ? 'Nenngeld offen' : 'Helm ausstehend' }}
    </div>

    <div v-if="error" class="text-xs text-red-600 bg-red-50 rounded px-2 py-1">{{ error }}</div>
    <div class="flex gap-2 pt-1">
      <button @click="$emit('save', { ...form })" class="flex-1 btn-primary py-2">Speichern</button>
      <button @click="$emit('cancel')" class="btn-secondary py-2 px-3 text-sm">Abbrechen</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../api/client'
import { useEventStore } from '../stores/event'
import { printNennungsformular } from '../utils/printNennung'

const props = defineProps({
  participant: { default: null },
  error:       { type: String, default: '' },
})
defineEmits(['save', 'cancel'])

const store = useEventStore()

const EMPTY = () => ({
  start_number: null, first_name: '', last_name: '',
  birth_year: null, gender: null, club_id: null, class_id: null,
  license_number: '', status: 'registered',
  fee_paid: false, helmet_ok: false,
})

const form = ref(props.participant ? { ...props.participant } : EMPTY())

watch(() => props.participant, (p) => {
  form.value = p ? { ...p } : EMPTY()
})

function handlePrint() {
  if (props.participant && store.activeEvent) {
    printNennungsformular(api, store.activeEvent, store.classes, props.participant)
  }
}
</script>
