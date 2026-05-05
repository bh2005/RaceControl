<template>
  <span class="font-mono tabnum">{{ display }}</span>
</template>

<script setup>
import { computed } from 'vue'
import { fmtRace, fmtTrain, fmtPenalty, fmtDelta, fmtDeltaTrain, fmtDownhill } from '../utils/format'

const props = defineProps({
  value:     { default: null },
  mode:      { type: String, default: 'race' }, // 'race' | 'training' | 'penalty' | 'delta-race' | 'delta-train' | 'downhill'
  reference: { default: null }, // Referenzzeit für delta-* Modi
})

const display = computed(() => {
  switch (props.mode) {
    case 'training':    return fmtTrain(props.value)
    case 'penalty':     return fmtPenalty(props.value)
    case 'delta-race':  return fmtDelta(props.value, props.reference)
    case 'delta-train': return fmtDeltaTrain(props.value, props.reference)
    case 'downhill':    return fmtDownhill(props.value)
    default:            return fmtRace(props.value)
  }
})
</script>
