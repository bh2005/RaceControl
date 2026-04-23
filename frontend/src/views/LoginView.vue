<template>
  <div class="min-h-screen bg-msc-blue flex items-center justify-center p-4">
    <div class="w-full max-w-sm">

      <!-- Logo -->
      <div class="flex flex-col items-center mb-8">
        <img src="/msc-logo.svg" alt="MSC Braach" class="h-24 w-24 rounded-full border-4 border-white/30 shadow-xl mb-4">
        <h1 class="text-white font-black text-3xl">RaceControl Pro</h1>
        <p class="text-blue-200 text-sm mt-1">MSC Braach e.V. im ADAC</p>
      </div>

      <!-- Login-Formular -->
      <div class="bg-white rounded-2xl shadow-2xl p-6">
        <h2 class="font-bold text-gray-800 text-lg mb-4 text-center">Anmelden</h2>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="text-xs font-semibold text-gray-500 block mb-1">Benutzername</label>
            <input
              v-model="username"
              type="text"
              autocomplete="username"
              class="input"
              placeholder="admin"
              ref="usernameInput"
              required
            >
          </div>
          <div>
            <label class="text-xs font-semibold text-gray-500 block mb-1">Passwort</label>
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              class="input"
              placeholder="••••••"
              required
            >
          </div>

          <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-3 py-2">
            {{ error }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full btn-primary py-3 text-base disabled:opacity-60"
          >
            {{ loading ? 'Anmelden…' : 'Anmelden' }}
          </button>
        </form>
      </div>

      <p class="text-center text-blue-300 text-xs mt-6">v0.1.0</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useEventStore } from '../stores/event'

const auth     = useAuthStore()
const store    = useEventStore()
const router   = useRouter()
const username = ref('')
const password = ref('')
const error    = ref('')
const loading  = ref(false)
const usernameInput = ref(null)

onMounted(() => usernameInput.value?.focus())

async function handleLogin() {
  error.value   = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    await store.loadEvents()
    await store.loadClubs()
    const dest = auth.role === 'viewer' ? '/livetiming'
               : auth.role === 'nennung' ? '/nennung'
               : auth.role === 'schiedsrichter' ? '/schiedsrichter'
               : '/zeitnahme'
    router.push(dest)
  } catch {
    error.value = 'Ungültige Zugangsdaten'
  } finally {
    loading.value = false
  }
}
</script>
