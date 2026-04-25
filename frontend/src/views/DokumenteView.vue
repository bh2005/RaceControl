<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">📄 Dokumente & Reglemente</h1>

    <div v-if="loading" class="text-gray-500 text-center py-12">Lade Dokumente…</div>
    <div v-else-if="error" class="text-red-600 text-center py-12">{{ error }}</div>
    <div v-else-if="!files.length" class="text-gray-400 text-center py-12">
      Keine Dokumente vorhanden.
    </div>

    <template v-else>
      <div
        v-for="(items, label) in grouped"
        :key="label"
        class="mb-8"
      >
        <h2 class="text-lg font-semibold text-gray-700 mb-3 border-b pb-1">{{ label }}</h2>
        <div class="grid gap-3 sm:grid-cols-2">
          <a
            v-for="file in items"
            :key="file.path"
            :href="file.url"
            target="_blank"
            rel="noopener"
            class="flex items-center gap-3 p-4 rounded-xl border border-gray-200 bg-white hover:bg-blue-50 hover:border-blue-300 transition group"
          >
            <span class="text-3xl leading-none">{{ fileIcon(file) }}</span>
            <div class="flex-1 min-w-0">
              <div class="font-medium text-gray-800 truncate group-hover:text-blue-700">
                {{ file.name }}
              </div>
              <div class="text-xs text-gray-400 mt-0.5">{{ formatSize(file.size) }}</div>
            </div>
            <span class="text-xs text-gray-400 shrink-0 uppercase tracking-wide">{{ ext(file.name) }}</span>
          </a>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/client'

const files   = ref([])
const loading = ref(true)
const error   = ref(null)

onMounted(async () => {
  try {
    const { data } = await api.get('/assets/files')
    files.value = data.filter(f => !f.category || f.category !== 'logos')
  } catch (e) {
    error.value = 'Dokumente konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
})

const grouped = computed(() => {
  const map = {}
  for (const f of files.value) {
    const label = f.category_label || 'Sonstiges'
    if (!map[label]) map[label] = []
    map[label].push(f)
  }
  return map
})

function ext(name) {
  return name.split('.').pop().toUpperCase()
}

function fileIcon(file) {
  const mime = file.mime || ''
  if (mime === 'application/pdf') return '📕'
  if (mime.startsWith('image/')) return '🖼️'
  if (mime.includes('word') || file.name.endsWith('.docx')) return '📝'
  if (mime.includes('excel') || file.name.endsWith('.xlsx')) return '📊'
  return '📄'
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>
