import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ParticipantCard from '../components/ParticipantCard.vue'

vi.mock('../api/client', () => ({ default: {} }))

vi.mock('../utils/printNennung', () => ({
  printNennungsformular: vi.fn(),
}))

vi.mock('../stores/event', () => ({
  useEventStore: () => ({
    clubs:       [{ id: 1, name: 'MSC Test', short_name: 'MSC' }],
    classes:     [{ id: 1, name: 'Klasse A' }],
    activeEvent: { id: 1, name: 'Test Event', date: '2026-01-01' },
  }),
}))

const FULL_PARTICIPANT = {
  id: 1, start_number: 5, first_name: 'Max', last_name: 'Muster',
  birth_year: 2010, gender: 'm', club_id: 1, class_id: 1,
  license_number: 'HE-001', status: 'technical_ok',
  fee_paid: true, helmet_ok: true,
}

describe('ParticipantCard', () => {
  it('shows "Nachnennung" heading when no participant', () => {
    const wrapper = mount(ParticipantCard)
    expect(wrapper.text()).toContain('Nachnennung')
  })

  it('shows "Bearbeiten: #X" heading with start number', () => {
    const wrapper = mount(ParticipantCard, { props: { participant: FULL_PARTICIPANT } })
    expect(wrapper.text()).toContain('Bearbeiten')
    expect(wrapper.text()).toContain('#5')
  })

  it('shows last name in heading when start number is absent', () => {
    const p = { ...FULL_PARTICIPANT, start_number: null }
    const wrapper = mount(ParticipantCard, { props: { participant: p } })
    expect(wrapper.text()).toContain('Muster')
  })

  it('emits save with form data when Speichern is clicked', async () => {
    const wrapper = mount(ParticipantCard)
    await wrapper.find('button.btn-primary').trigger('click')
    expect(wrapper.emitted('save')).toBeTruthy()
    expect(wrapper.emitted('save')[0][0]).toMatchObject({
      first_name: '', last_name: '', status: 'registered',
      fee_paid: false, helmet_ok: false,
    })
  })

  it('emits cancel when Abbrechen is clicked', async () => {
    const wrapper = mount(ParticipantCard)
    const btn = wrapper.findAll('button').find(b => b.text() === 'Abbrechen')
    await btn.trigger('click')
    expect(wrapper.emitted('cancel')).toBeTruthy()
  })

  it('displays error message from error prop', () => {
    const wrapper = mount(ParticipantCard, { props: { error: 'Fehler beim Speichern' } })
    expect(wrapper.text()).toContain('Fehler beim Speichern')
  })

  it('print button visible when participant has license + fee + helmet', () => {
    const wrapper = mount(ParticipantCard, { props: { participant: FULL_PARTICIPANT } })
    const printBtn = wrapper.findAll('button').find(b => b.text().includes('Nennungsformular'))
    expect(printBtn).toBeDefined()
  })

  it('print button hidden when license_number is missing', () => {
    const p = { ...FULL_PARTICIPANT, license_number: '' }
    const wrapper = mount(ParticipantCard, { props: { participant: p } })
    const printBtn = wrapper.findAll('button').find(b => b.text().includes('Nennungsformular'))
    expect(printBtn).toBeUndefined()
  })

  it('print button hidden when fee_paid is false', () => {
    const p = { ...FULL_PARTICIPANT, fee_paid: false }
    const wrapper = mount(ParticipantCard, { props: { participant: p } })
    const printBtn = wrapper.findAll('button').find(b => b.text().includes('Nennungsformular'))
    expect(printBtn).toBeUndefined()
  })

  it('print button hidden when no participant', () => {
    const wrapper = mount(ParticipantCard)
    const printBtn = wrapper.findAll('button').find(b => b.text().includes('Nennungsformular'))
    expect(printBtn).toBeUndefined()
  })

  it('form resets to empty when participant prop changes to null', async () => {
    const wrapper = mount(ParticipantCard, { props: { participant: FULL_PARTICIPANT } })
    await wrapper.setProps({ participant: null })
    const inputs = wrapper.findAll('input[type="text"]')
    for (const input of inputs) {
      expect(input.element.value).toBe('')
    }
  })

  it('form updates when participant prop changes', async () => {
    const wrapper = mount(ParticipantCard, { props: { participant: FULL_PARTICIPANT } })
    const p2 = { ...FULL_PARTICIPANT, start_number: 99, first_name: 'Anna' }
    await wrapper.setProps({ participant: p2 })
    expect(wrapper.text()).toContain('#99')
  })

  it('shows Startklar when fee_paid and helmet_ok are checked', () => {
    const wrapper = mount(ParticipantCard, { props: { participant: FULL_PARTICIPANT } })
    expect(wrapper.text()).toContain('Startklar')
  })

  it('shows status select only when editing existing participant', () => {
    const newWrapper = mount(ParticipantCard)
    expect(newWrapper.text()).not.toContain('Gemeldet')

    const editWrapper = mount(ParticipantCard, { props: { participant: FULL_PARTICIPANT } })
    expect(editWrapper.text()).toContain('Gemeldet')
  })
})
