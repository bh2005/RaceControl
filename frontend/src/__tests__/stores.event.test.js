import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useEventStore } from '../stores/event.js'

vi.mock('../api/client.js', () => ({
  default: { post: vi.fn(), get: vi.fn() },
}))

import api from '../api/client.js'

const EVENTS = [
  { id: 1, name: 'Testlauf A', status: 'active', date: '2026-06-01' },
  { id: 2, name: 'Testlauf B', status: 'planned', date: '2026-07-01' },
]
const CLASSES = [
  { id: 10, name: 'Klasse A', event_id: 1 },
  { id: 11, name: 'Klasse B', event_id: 1 },
]

describe('useEventStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('Initialzustand: leere Arrays', () => {
    const store = useEventStore()
    expect(store.events).toEqual([])
    expect(store.classes).toEqual([])
    expect(store.activeEvent).toBeNull()
    expect(store.activeClass).toBeNull()
  })

  it('loadEvents lädt Events und setzt activeEvent auf aktives Event', async () => {
    api.get
      .mockResolvedValueOnce({ data: EVENTS })      // loadEvents → /events/
      .mockResolvedValueOnce({ data: CLASSES })      // selectEvent → /events/1/classes

    const store = useEventStore()
    await store.loadEvents()

    expect(store.events).toEqual(EVENTS)
    expect(store.activeEvent).toEqual(EVENTS[0])   // status='active'
    expect(store.classes).toEqual(CLASSES)
    expect(store.activeClass).toEqual(CLASSES[0])
  })

  it('loadEvents nimmt erstes Event wenn keines active ist', async () => {
    const noActiveEvents = [
      { id: 3, name: 'Event X', status: 'planned' },
    ]
    api.get
      .mockResolvedValueOnce({ data: noActiveEvents })
      .mockResolvedValueOnce({ data: [] })

    const store = useEventStore()
    await store.loadEvents()

    expect(store.activeEvent).toEqual(noActiveEvents[0])
  })

  it('loadEvents tut nichts bei leerem Array', async () => {
    api.get.mockResolvedValueOnce({ data: [] })
    const store = useEventStore()
    await store.loadEvents()
    expect(store.activeEvent).toBeNull()
  })

  it('selectEvent setzt activeEvent und lädt Klassen', async () => {
    api.get.mockResolvedValueOnce({ data: CLASSES })

    const store = useEventStore()
    await store.selectEvent(EVENTS[1])

    expect(store.activeEvent).toEqual(EVENTS[1])
    expect(store.classes).toEqual(CLASSES)
    expect(api.get).toHaveBeenCalledWith('/events/2/classes')
  })

  it('selectEvent setzt activeClass auf null wenn keine Klassen', async () => {
    api.get.mockResolvedValueOnce({ data: [] })
    const store = useEventStore()
    await store.selectEvent(EVENTS[0])
    expect(store.activeClass).toBeNull()
  })

  it('loadReglements befüllt reglements', async () => {
    const regs = [{ id: 1, name: 'KT-Reg', scoring_type: 'sum_all' }]
    api.get.mockResolvedValueOnce({ data: regs })
    const store = useEventStore()
    await store.loadReglements()
    expect(store.reglements).toEqual(regs)
    expect(api.get).toHaveBeenCalledWith('/reglements/')
  })

  it('loadClubs befüllt clubs', async () => {
    const clubs = [{ id: 1, name: 'MC Teststadt' }]
    api.get.mockResolvedValueOnce({ data: clubs })
    const store = useEventStore()
    await store.loadClubs()
    expect(store.clubs).toEqual(clubs)
    expect(api.get).toHaveBeenCalledWith('/clubs/')
  })
})
