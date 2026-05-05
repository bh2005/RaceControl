<template>
  <footer class="fixed bottom-0 left-0 right-0 bg-gray-800 text-white text-xs px-4 py-1.5 flex items-center justify-between z-10">
    <div class="flex items-center gap-4">
      <span class="flex items-center gap-1.5">
        <span class="h-2 w-2 rounded-full" :class="online ? 'bg-green-400' : 'bg-red-400'"></span>
        {{ online ? 'Verbunden' : 'Keine Verbindung' }}
      </span>
      <span v-if="store.activeEvent" class="text-gray-400">
        {{ store.activeEvent.name }}
      </span>
    </div>
    <div class="hidden md:flex items-center gap-4 text-gray-400">
      <span><kbd class="bg-gray-700 rounded px-1">Tab</kbd> Nächstes Feld</span>
      <span><kbd class="bg-gray-700 rounded px-1">Enter</kbd> Bestätigen</span>
      <span><kbd class="bg-gray-700 rounded px-1">1–9</kbd> Strafe</span>
      <span><kbd class="bg-gray-700 rounded px-1">Ctrl+Z</kbd> Undo</span>
    </div>
    <div class="flex items-center gap-3 text-gray-400">
      <RouterLink to="/lizenz" class="hover:text-gray-200 transition text-xs">GPL-2.0</RouterLink>
      <span>RaceControl Pro v{{ version }}</span>
    </div>
  </footer>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useEventStore } from '../stores/event'
import { version } from '../../package.json'

const store  = useEventStore()
const online = ref(navigator.onLine)

function update() { online.value = navigator.onLine }
onMounted(() => {
  window.addEventListener('online', update)
  window.addEventListener('offline', update)
})
onUnmounted(() => {
  window.removeEventListener('online', update)
  window.removeEventListener('offline', update)
})
</script>
