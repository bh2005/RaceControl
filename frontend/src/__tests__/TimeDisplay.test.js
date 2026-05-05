import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TimeDisplay from '../components/TimeDisplay.vue'

describe('TimeDisplay', () => {
  it('renders a span with font-mono and tabnum classes', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 12.5 } })
    expect(wrapper.classes()).toContain('font-mono')
    expect(wrapper.classes()).toContain('tabnum')
  })

  it('defaults to race mode — 2 decimal places', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 12.5 } })
    expect(wrapper.text()).toBe('12.50')
  })

  it('race mode returns dash for null', () => {
    const wrapper = mount(TimeDisplay, { props: { value: null } })
    expect(wrapper.text()).toBe('–')
  })

  it('race mode explicit', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 9.99, mode: 'race' } })
    expect(wrapper.text()).toBe('9.99')
  })

  it('training mode — 3 decimal places', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 12.5, mode: 'training' } })
    expect(wrapper.text()).toBe('12.500')
  })

  it('training mode returns dash for null', () => {
    const wrapper = mount(TimeDisplay, { props: { value: null, mode: 'training' } })
    expect(wrapper.text()).toBe('–')
  })

  it('penalty mode — 1 decimal place', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 2.0, mode: 'penalty' } })
    expect(wrapper.text()).toBe('2.0')
  })

  it('delta-race mode', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 12.5, mode: 'delta-race', reference: 10.5 } })
    expect(wrapper.text()).toBe('+2.00')
  })

  it('delta-train mode', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 12.5, mode: 'delta-train', reference: 10.5 } })
    expect(wrapper.text()).toBe('+2.000')
  })

  it('downhill mode — returns dash for null', () => {
    const wrapper = mount(TimeDisplay, { props: { value: null, mode: 'downhill' } })
    expect(wrapper.text()).toBe('–')
  })

  it('downhill mode — formats under 60 seconds', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 45.5, mode: 'downhill' } })
    expect(wrapper.text()).toBe('45.50')
  })

  it('downhill mode — formats minutes:seconds', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 75.5, mode: 'downhill' } })
    expect(wrapper.text()).toBe('1:15.50')
  })

  it('unknown mode falls through to race', () => {
    const wrapper = mount(TimeDisplay, { props: { value: 8.5, mode: 'unknown' } })
    expect(wrapper.text()).toBe('8.50')
  })
})
