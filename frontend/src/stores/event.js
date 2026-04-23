import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api/client'

export const useEventStore = defineStore('event', () => {
  const events        = ref([])
  const activeEvent   = ref(null)
  const classes       = ref([])
  const activeClass   = ref(null)
  const reglements    = ref([])
  const clubs         = ref([])

  async function loadEvents() {
    const { data } = await api.get('/events/')
    events.value = data
    if (!activeEvent.value && data.length) {
      const active = data.find(e => e.status === 'active') || data[0]
      await selectEvent(active)
    }
  }

  async function selectEvent(event) {
    activeEvent.value = event
    const { data } = await api.get(`/events/${event.id}/classes`)
    classes.value = data
    activeClass.value = data[0] || null
  }

  async function loadReglements() {
    const { data } = await api.get('/reglements/')
    reglements.value = data
  }

  async function loadClubs() {
    const { data } = await api.get('/clubs/')
    clubs.value = data
  }

  return {
    events, activeEvent, classes, activeClass, reglements, clubs,
    loadEvents, selectEvent, loadReglements, loadClubs
  }
})
