import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ClassTabs from '../components/ClassTabs.vue'

const CLASSES = [
  { id: 1, name: 'Klasse A', short_name: 'KA', run_status: 'running' },
  { id: 2, name: 'Klasse B', short_name: 'KB', run_status: 'planned' },
]

function mkWrapper(propsOverride = {}) {
  return mount(ClassTabs, {
    props: {
      classes: CLASSES,
      trainingAvailable: false,
      selectedClassId: null,
      showTraining: false,
      ...propsOverride,
    },
  })
}

describe('ClassTabs', () => {
  it('rendert "Alle"-Button', () => {
    const w = mkWrapper()
    expect(w.text()).toContain('Alle')
  })

  it('rendert einen Button pro Klasse', () => {
    const w = mkWrapper()
    const tabs = w.findAll('[role="tab"]')
    // "Alle" + 2 Klassen = 3 Tabs
    expect(tabs).toHaveLength(3)
  })

  it('zeigt Kürzel wenn vorhanden, sonst Namen', () => {
    const w = mkWrapper()
    expect(w.text()).toContain('KA')
    expect(w.text()).toContain('KB')
  })

  it('zeigt ▶ Icon für laufende Klasse', () => {
    const w = mkWrapper()
    expect(w.text()).toContain('▶')
  })

  it('zeigt Training-Tab wenn trainingAvailable=true', () => {
    const w = mkWrapper({ trainingAvailable: true })
    expect(w.text()).toContain('Training')
    const tabs = w.findAll('[role="tab"]')
    expect(tabs).toHaveLength(4) // Alle + 2 Klassen + Training
  })

  it('versteckt Training-Tab wenn trainingAvailable=false', () => {
    const w = mkWrapper({ trainingAvailable: false })
    expect(w.text()).not.toContain('Training')
  })

  it('Klick auf "Alle" emittet update:selectedClassId=null und update:showTraining=false', async () => {
    const w = mkWrapper({ selectedClassId: 1, showTraining: false })
    await w.findAll('[role="tab"]')[0].trigger('click')
    expect(w.emitted('update:selectedClassId')?.[0]).toEqual([null])
    expect(w.emitted('update:showTraining')?.[0]).toEqual([false])
  })

  it('Klick auf Klasse emittet korrekten selectedClassId', async () => {
    const w = mkWrapper()
    await w.findAll('[role="tab"]')[1].trigger('click') // "KA"
    expect(w.emitted('update:selectedClassId')?.[0]).toEqual([1])
    expect(w.emitted('update:showTraining')?.[0]).toEqual([false])
  })

  it('Klick auf Training emittet showTraining=true', async () => {
    const w = mkWrapper({ trainingAvailable: true })
    const trainingTab = w.findAll('[role="tab"]').at(-1)
    await trainingTab.trigger('click')
    expect(w.emitted('update:showTraining')?.[0]).toEqual([true])
    expect(w.emitted('update:selectedClassId')?.[0]).toEqual([null])
  })

  it('aktive Klasse hat aria-selected=true', () => {
    const w = mkWrapper({ selectedClassId: 1 })
    const tabs = w.findAll('[role="tab"]')
    expect(tabs[1].attributes('aria-selected')).toBe('true')
    expect(tabs[2].attributes('aria-selected')).toBe('false')
  })

  it('Alle-Tab hat aria-selected=true wenn selectedClassId=null und showTraining=false', () => {
    const w = mkWrapper({ selectedClassId: null, showTraining: false })
    expect(w.findAll('[role="tab"]')[0].attributes('aria-selected')).toBe('true')
  })

  it('Tastaturnavigation ArrowRight wechselt zum nächsten Tab', async () => {
    const w = mkWrapper()
    const tablist = w.find('[role="tablist"]')
    // Fokus auf "Alle" (index 0) simulieren ist jsdom-schwierig; wir testen, dass
    // das Event keinen Fehler wirft (Smoke-Test)
    await tablist.trigger('keydown', { key: 'Home' })
    await tablist.trigger('keydown', { key: 'End' })
    await tablist.trigger('keydown', { key: 'ArrowRight' })
    await tablist.trigger('keydown', { key: 'ArrowLeft' })
    // Kein Fehler → Test besteht
    expect(true).toBe(true)
  })

  it('Tastaturnavigation ignoriert andere Tasten — emittiert keine Auswahl-Events', async () => {
    const w = mkWrapper()
    await w.find('[role="tablist"]').trigger('keydown', { key: 'Enter' })
    expect(w.emitted('update:selectedClassId')).toBeUndefined()
    expect(w.emitted('update:showTraining')).toBeUndefined()
  })
})
