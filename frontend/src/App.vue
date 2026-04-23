<template>
  <div class="min-h-screen flex flex-col">
    <!-- Offline banner — visible on all views -->
    <Transition name="slide-down">
      <div v-if="!isOnline"
           class="fixed top-0 left-0 right-0 z-[100] bg-amber-500 text-gray-900 text-center text-sm font-bold py-2 px-4 shadow-lg">
        Keine Netzwerkverbindung – zuletzt geladene Daten werden angezeigt
      </div>
    </Transition>

    <AppHeader v-if="auth.isLoggedIn" />
    <main class="flex-1">
      <RouterView />
    </main>
    <StatusBar v-if="auth.isLoggedIn" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { useEventStore } from './stores/event'
import AppHeader from './components/AppHeader.vue'
import StatusBar from './components/StatusBar.vue'
import { useNetworkStatus } from './composables/useNetworkStatus'

const auth  = useAuthStore()
const store = useEventStore()
const { isOnline } = useNetworkStatus()

onMounted(async () => {
  if (auth.isLoggedIn) {
    await store.loadEvents()
    await store.loadClubs()
  }
})
</script>

<style>
.slide-down-enter-active, .slide-down-leave-active { transition: transform 0.25s ease; }
.slide-down-enter-from, .slide-down-leave-to      { transform: translateY(-100%); }
</style>
