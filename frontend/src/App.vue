<template>
  <div class="min-h-screen flex flex-col">
    <!-- Offline banner -->
    <Transition name="slide-down">
      <div v-if="!isOnline"
           class="fixed top-0 left-0 right-0 z-[100] bg-amber-500 text-gray-900 text-center text-sm font-bold py-2 px-4 shadow-lg">
        Keine Netzwerkverbindung – zuletzt geladene Daten werden angezeigt
      </div>
    </Transition>

    <!-- Nennungsschluss-Ankündigung -->
    <Transition name="notif-slide">
      <div v-if="notification"
           class="fixed left-0 right-0 z-[90] bg-cyan-600 text-white text-center font-bold py-3 px-6 shadow-xl cursor-pointer flex items-center justify-center gap-3"
           :style="!isOnline ? 'top:40px' : 'top:0'"
           @click="notification = null">
        <span class="text-lg">📢</span>
        <span>{{ notification.message }}</span>
        <span class="opacity-50 text-sm ml-2">✕</span>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from './stores/auth'
import { useEventStore } from './stores/event'
import AppHeader from './components/AppHeader.vue'
import StatusBar from './components/StatusBar.vue'
import { useNetworkStatus } from './composables/useNetworkStatus'
import { useRealtimeUpdate } from './composables/useRealtimeUpdate'

const auth  = useAuthStore()
const store = useEventStore()
const { isOnline } = useNetworkStatus()

const notification = ref(null)
let notifTimer = null

useRealtimeUpdate((msg) => {
  if (msg.type !== 'notification') return
  notification.value = msg
  clearTimeout(notifTimer)
  notifTimer = setTimeout(() => { notification.value = null }, 30000)
})

onUnmounted(() => clearTimeout(notifTimer))

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

.notif-slide-enter-active, .notif-slide-leave-active { transition: transform 0.3s ease, opacity 0.3s ease; }
.notif-slide-enter-from, .notif-slide-leave-to      { transform: translateY(-100%); opacity: 0; }
</style>
