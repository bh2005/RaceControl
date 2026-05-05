import { describe, it, expect } from 'vitest'
import { fmtRace, fmtTrain, fmtPenalty, fmtDelta, fmtDeltaTrain, fmtDownhill } from '../utils/format'

describe('fmtRace', () => {
  it('formats to 2 decimal places', () => {
    expect(fmtRace(12.5)).toBe('12.50')
    expect(fmtRace(0)).toBe('0.00')
  })
  it('returns dash for null', () => {
    expect(fmtRace(null)).toBe('–')
  })
  it('returns dash for undefined', () => {
    expect(fmtRace(undefined)).toBe('–')
  })
})

describe('fmtTrain', () => {
  it('formats to 3 decimal places', () => {
    expect(fmtTrain(12.5)).toBe('12.500')
    expect(fmtTrain(0)).toBe('0.000')
  })
  it('returns dash for null', () => {
    expect(fmtTrain(null)).toBe('–')
  })
})

describe('fmtPenalty', () => {
  it('formats to 1 decimal place', () => {
    expect(fmtPenalty(5.0)).toBe('5.0')
    expect(fmtPenalty(2.0)).toBe('2.0')
  })
})

describe('fmtDelta', () => {
  it('shows positive delta with 2 decimals', () => {
    expect(fmtDelta(12.5, 10.5)).toBe('+2.00')
    expect(fmtDelta(11.0, 11.0)).toBe('+0.00')
  })
})

describe('fmtDeltaTrain', () => {
  it('shows positive delta with 3 decimals', () => {
    expect(fmtDeltaTrain(12.5, 10.5)).toBe('+2.000')
  })
})

describe('fmtDownhill', () => {
  it('returns dash for null', () => {
    expect(fmtDownhill(null)).toBe('–')
  })
  it('returns dash for undefined', () => {
    expect(fmtDownhill(undefined)).toBe('–')
  })
  it('formats seconds under 60 to 2 decimal places', () => {
    expect(fmtDownhill(45.5)).toBe('45.50')
  })
  it('formats to minutes:seconds when >= 60', () => {
    expect(fmtDownhill(75.5)).toBe('1:15.50')
  })
  it('pads seconds with leading zero', () => {
    expect(fmtDownhill(65.0)).toBe('1:05.00')
  })
  it('handles exactly 60 seconds', () => {
    expect(fmtDownhill(60.0)).toBe('1:00.00')
  })
})
