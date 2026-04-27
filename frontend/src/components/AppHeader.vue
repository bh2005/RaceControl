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
        <!-- Primäre Links -->
        <RouterLink
          v-for="item in primaryItems"
          :key="item.to"
          :to="item.to"
          class="px-3 py-1.5 rounded-lg text-sm font-medium transition"
          :class="$route.path === item.to
            ? 'bg-white/20 font-bold'
            : 'hover:bg-white/10 text-blue-100'"
        >
          {{ item.label }}
        </RouterLink>

        <!-- Mehr-Dropdown (nur wenn sekundäre Items vorhanden) -->
        <div v-if="secondaryItems.length" class="relative" ref="dropdownRef">
          <button
            @click="menuOpen = !menuOpen"
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition flex items-center gap-1"
            :class="menuOpen || secondaryActive
              ? 'bg-white/20 font-bold'
              : 'hover:bg-white/10 text-blue-100'"
          >
            Mehr
            <span class="text-xs opacity-70">{{ menuOpen ? '▲' : '▼' }}</span>
          </button>

          <Transition name="dropdown">
            <div
              v-if="menuOpen"
              class="absolute right-0 top-full mt-1 bg-white rounded-xl shadow-xl border border-gray-200 py-1 min-w-44 z-50"
            >
              <RouterLink
                v-for="item in secondaryItems"
                :key="item.to"
                :to="item.to"
                @click="menuOpen = false"
                class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-blue-50 hover:text-msc-blue transition font-medium"
                :class="$route.path === item.to ? 'bg-blue-50 text-msc-blue font-bold' : ''"
              >
                {{ item.label }}
              </RouterLink>
            </div>
          </Transition>
        </div>
      </nav>

      <!-- Event-Anzeige + User -->
      <div class="flex items-center gap-4">
        <div class="text-right hidden lg:block">
          <div class="font-black text-xl tabnum text-white tracking-tight leading-none">{{ currentTime }}</div>
        </div>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useEventStore } from '../stores/event'

const auth   = useAuthStore()
const store  = useEventStore()
const router = useRouter()
const route  = useRoute()

const currentTime = ref('')
const menuOpen    = ref(false)
const dropdownRef = ref(null)
let clockTimer    = null

function updateClock() {
  currentTime.value = new Date().toLocaleTimeString('de-DE', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

// Schließen wenn außerhalb geklickt
function onClickOutside(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    menuOpen.value = false
  }
}

onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  document.addEventListener('click', onClickOutside)
})
onUnmounted(() => {
  clearInterval(clockTimer)
  document.removeEventListener('click', onClickOutside)
})

// primary: true → immer in der Bar
// primary: false → im Mehr-Dropdown
const allNav = [
  { to: '/zeitnahme',      label: 'Zeitnahme',          roles: ['admin', 'zeitnahme'],                                     primary: true  },
  { to: '/nennung',        label: 'Nennung',             roles: ['admin', 'nennung'],                                       primary: true  },
  { to: '/schiedsrichter', label: 'Schiedsrichter',      roles: ['admin', 'schiedsrichter'],                                primary: true  },
  { to: '/admin',          label: 'Admin',               roles: ['admin'],                                                  primary: true  },
  { to: '/marshal',        label: '🚩 Streckenposten',   roles: ['marshal'],                                                primary: true  },
  { to: '/livetiming',     label: 'Livetiming',          roles: null,                                                       primary: false },
  { to: '/speaker',        label: '🎙 Sprecher',          roles: ['admin', 'schiedsrichter', 'zeitnahme', 'viewer'],            primary: false },
  { to: '/nachrichten',    label: '📢 Nachrichten',      roles: ['admin', 'zeitnahme', 'nennung', 'schiedsrichter', 'viewer'], primary: false },
  { to: '/marshal',        label: '🚩 Streckenposten',   roles: ['admin'],                                                  primary: false },
  { to: '/dokumente',      label: '📄 Dokumente',        roles: null,                                                       primary: false },
  { to: '/nennen',         label: 'Online-Nennung',      roles: null,                                                       primary: false },
]

const visibleNav = computed(() =>
  allNav.filter(n => !n.roles || n.roles.includes(auth.role))
)

const primaryItems   = computed(() => visibleNav.value.filter(n =>  n.primary))
const secondaryItems = computed(() => visibleNav.value.filter(n => !n.primary))

const secondaryActive = computed(() =>
  secondaryItems.value.some(n => n.to === route.path)
)

function handleLogout() {
  auth.logout()
  router.push('/')
}
</script>

<style scoped>
.tabnum { font-variant-numeric: tabular-nums; }

.dropdown-enter-active, .dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-enter-from, .dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
