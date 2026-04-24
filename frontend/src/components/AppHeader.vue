<template>
  <header class="bg-msc-blue text-white shadow-lg sticky top-0 z-20">
    <div class="max-w-7xl mx-auto px-4 py-2 flex items-center justify-between">

      <!-- Logo + Titel -->
      <div class="flex items-center gap-3">
        <img src="/msc-logo.svg" alt="MSC Braach" class="h-10 w-10 rounded-full border-2 border-white/30">
        <div>
          <div class="font-bold text-lg leading-tight">RaceControl Pro</div>
          <div class="text-xs text-blue-200">MSC Braach e.V. im ADAC</div>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex items-center gap-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
          :class="$route.path === item.to
            ? 'bg-white/20 font-bold'
            : 'hover:bg-white/10 text-blue-100'"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <!-- Event-Anzeige + User -->
      <div class="flex items-center gap-4">
        <div v-if="store.activeEvent" class="text-right text-sm hidden lg:block">
          <div class="font-semibold text-blue-100">{{ store.activeEvent.name }}</div>
          <div class="text-xs text-blue-300">{{ store.activeEvent.date }}</div>
        </div>
        <div class="flex items-center gap-2">
          <div class="text-right text-sm">
            <div class="font-semibold">{{ auth.user?.role }}</div>
          </div>
          <button
            @click="handleLogout"
            class="h-8 w-8 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center font-bold transition text-sm"
            title="Abmelden"
          >
            ⏻
          </button>
        </div>
      </div>

    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useEventStore } from '../stores/event'

const auth   = useAuthStore()
const store  = useEventStore()
const router = useRouter()

const allNav = [
  { to: '/zeitnahme',      label: 'Zeitnahme',      roles: ['admin', 'zeitnahme'] },
  { to: '/nennung',        label: 'Nennung',         roles: ['admin', 'nennung'] },
  { to: '/schiedsrichter', label: 'Schiedsrichter',  roles: ['admin', 'schiedsrichter'] },
  { to: '/livetiming',     label: 'Livetiming',      roles: null },
  { to: '/speaker',        label: 'Sprecher',         roles: ['admin', 'schiedsrichter', 'zeitnahme'] },
  { to: '/nennen',         label: 'Online-Nennung',  roles: null },
  { to: '/admin',          label: 'Admin',           roles: ['admin'] },
]

const navItems = computed(() =>
  allNav.filter(n => !n.roles || n.roles.includes(auth.role))
)

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>
