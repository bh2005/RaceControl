import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StatusBadge from '../components/StatusBadge.vue'

describe('StatusBadge', () => {
  it('renders the correct label for a known status', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'running' } })
    expect(wrapper.text()).toBe('Läuft ▶')
  })

  it('falls back to the raw status string for unknown status', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'unknown_xyz' } })
    expect(wrapper.text()).toBe('unknown_xyz')
  })

  it('uses light theme CSS classes by default', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'official' } })
    expect(wrapper.classes()).toContain('bg-green-100')
    expect(wrapper.classes()).toContain('text-green-700')
  })

  it('uses dark theme CSS classes when theme="dark"', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'official', theme: 'dark' } })
    expect(wrapper.classes()).toContain('bg-green-900/50')
    expect(wrapper.classes()).toContain('text-green-400')
  })

  it('falls back to planned CSS class for unknown status', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'bogus' } })
    expect(wrapper.classes()).toContain('bg-gray-100')
    expect(wrapper.classes()).toContain('text-gray-500')
  })

  it('renders slot content instead of computed label', () => {
    const wrapper = mount(StatusBadge, {
      props: { status: 'running' },
      slots: { default: 'Override' },
    })
    expect(wrapper.text()).toBe('Override')
  })

  it('renders without errors for all defined statuses', () => {
    const statuses = [
      'official', 'running', 'preliminary', 'paused', 'planned',
      'registered', 'checked_in', 'technical_ok', 'disqualified',
    ]
    for (const status of statuses) {
      const wrapper = mount(StatusBadge, { props: { status } })
      expect(wrapper.find('span').exists()).toBe(true)
    }
  })

  it('disqualified status shows DSQ label', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'disqualified' } })
    expect(wrapper.text()).toBe('DSQ')
  })

  it('planned status shows Geplant label', () => {
    const wrapper = mount(StatusBadge, { props: { status: 'planned' } })
    expect(wrapper.text()).toBe('Geplant')
  })
})
