<template>
  <div ref="tablistEl" role="tablist" aria-label="Klassen-Filter"
       class="max-w-lg md:max-w-2xl lg:max-w-4xl mx-auto px-4 pb-2 flex gap-2 overflow-x-auto"
       @keydown="onTabKeydown">
    <button
      role="tab"
      :aria-selected="!showTraining && selectedClassId === null"
      :tabindex="!showTraining && selectedClassId === null ? 0 : -1"
      @click="selectAll"
      class="shrink-0 text-xs font-bold rounded-full px-3 py-1 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/80"
      :class="!showTraining && selectedClassId === null ? 'bg-white text-msc-blue' : 'bg-white/10 text-white border border-white/20'"
    >
      Alle
    </button>
    <button
      v-for="c in classes"
      :key="c.id"
      role="tab"
      :aria-selected="!showTraining && selectedClassId === c.id"
      :tabindex="!showTraining && selectedClassId === c.id ? 0 : -1"
      :aria-label="`${c.short_name || c.name}${c.run_status === 'running' ? ', läuft gerade' : ''}`"
      @click="selectClass(c.id)"
      class="shrink-0 text-xs font-semibold rounded-full px-3 py-1 transition border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/80"
      :class="!showTraining && selectedClassId === c.id
        ? 'bg-msc-red text-white border-msc-red font-bold'
        : 'bg-white/10 text-white border-white/20'"
    >
      {{ c.short_name || c.name }}
      <span v-if="c.run_status === 'running'" aria-hidden="true" class="ml-1">▶</span>
    </button>
    <button
      v-if="trainingAvailable"
      role="tab"
      :aria-selected="showTraining"
      :tabindex="showTraining ? 0 : -1"
      @click="selectTraining"
      class="shrink-0 text-xs font-semibold rounded-full px-3 py-1 transition border focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/80"
      :class="showTraining
        ? 'bg-cyan-400 text-gray-900 border-cyan-400 font-bold'
        : 'bg-white/10 text-white border-white/20'"
    >
      <span aria-hidden="true">🏋</span> Training
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  classes:          { type: Array,   required: true },
  trainingAvailable:{ type: Boolean, default: false },
  selectedClassId:  { default: null },
  showTraining:     { type: Boolean, default: false },
})

const emit = defineEmits(['update:selectedClassId', 'update:showTraining'])

function selectAll()        { emit('update:showTraining', false); emit('update:selectedClassId', null) }
function selectClass(id)    { emit('update:showTraining', false); emit('update:selectedClassId', id) }
function selectTraining()   { emit('update:showTraining', true);  emit('update:selectedClassId', null) }

const tablistEl = ref(null)

function onTabKeydown(e) {
  if (!['ArrowRight', 'ArrowLeft', 'Home', 'End'].includes(e.key)) return
  const tabs = [...tablistEl.value.querySelectorAll('[role="tab"]')]
  const current = tabs.indexOf(document.activeElement)
  if (current === -1) return
  e.preventDefault()
  let next = current
  if (e.key === 'ArrowRight')      next = (current + 1) % tabs.length
  else if (e.key === 'ArrowLeft')  next = (current - 1 + tabs.length) % tabs.length
  else if (e.key === 'Home')       next = 0
  else if (e.key === 'End')        next = tabs.length - 1
  tabs[next].focus()
  tabs[next].click()
}
</script>
