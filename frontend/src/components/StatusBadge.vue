<template>
  <span :class="['text-xs font-semibold rounded px-1.5 py-0.5', badgeClass]">
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  theme:  { type: String, default: 'light' }, // 'light' | 'dark'
})

const LIGHT = {
  official:     'bg-green-100 text-green-700',
  running:      'bg-blue-100 text-blue-700',
  preliminary:  'bg-amber-100 text-amber-700',
  paused:       'bg-orange-100 text-orange-700',
  planned:      'bg-gray-100 text-gray-500',
  registered:   'bg-sky-100 text-sky-700',
  checked_in:   'bg-yellow-100 text-yellow-700',
  technical_ok: 'bg-green-100 text-green-700',
  disqualified: 'bg-red-100 text-red-700',
}

const DARK = {
  official:     'bg-green-900/50 text-green-400 border border-green-800',
  running:      'bg-blue-900/50 text-blue-300 border border-blue-700',
  preliminary:  'bg-amber-900/50 text-amber-400 border border-amber-700',
  paused:       'bg-orange-900/50 text-orange-400 border border-orange-700',
  planned:      'bg-gray-800 text-gray-500',
  registered:   'bg-sky-900/50 text-sky-300 border border-sky-700',
  checked_in:   'bg-yellow-900/50 text-yellow-300 border border-yellow-700',
  technical_ok: 'bg-green-900/50 text-green-400 border border-green-800',
  disqualified: 'bg-red-900/50 text-red-400 border border-red-800',
}

const LABELS = {
  official:     'Offiziell',
  running:      'Läuft ▶',
  preliminary:  'Vorläufig',
  paused:       'Unterbrochen ⏸',
  planned:      'Geplant',
  registered:   'Angemeldet',
  checked_in:   'Eingecheckt',
  technical_ok: 'Tech. OK',
  disqualified: 'DSQ',
}

const map = computed(() => props.theme === 'dark' ? DARK : LIGHT)
const badgeClass = computed(() => map.value[props.status] ?? map.value.planned)
const label      = computed(() => LABELS[props.status] ?? props.status)
</script>
