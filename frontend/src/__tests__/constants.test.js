import { describe, it, expect } from 'vitest'
import * as C from '../constants/contest.js'

describe('contest constants', () => {
  it('PROTEST_WINDOW_MIN is 30', () => expect(C.PROTEST_WINDOW_MIN).toBe(30))
  it('AUTO_CLOSE_DELAY_MS is 6000', () => expect(C.AUTO_CLOSE_DELAY_MS).toBe(6_000))
  it('FLASH_DURATION_MS is 1800', () => expect(C.FLASH_DURATION_MS).toBe(1_800))
  it('MARSHAL_TIMEOUT_MS is 60000', () => expect(C.MARSHAL_TIMEOUT_MS).toBe(60_000))
  it('MARSHAL_TIMEOUT_SPEAKER_MS is 30000', () => expect(C.MARSHAL_TIMEOUT_SPEAKER_MS).toBe(30_000))
  it('DEBOUNCE_SAVE_MS is 400', () => expect(C.DEBOUNCE_SAVE_MS).toBe(400))
  it('POLL_INTERVAL_MS is 30000', () => expect(C.POLL_INTERVAL_MS).toBe(30_000))
  it('DEFAULT_RUNS is 2', () => expect(C.DEFAULT_RUNS).toBe(2))
  it('RECENT_RUNS_LIMIT is 8', () => expect(C.RECENT_RUNS_LIMIT).toBe(8))
  it('SPEAKER_LOG_LIMIT is 50', () => expect(C.SPEAKER_LOG_LIMIT).toBe(50))
  it('SPEAKER_RANK_TARGETS contains 1, 3, 10', () => {
    expect(C.SPEAKER_RANK_TARGETS).toEqual([1, 3, 10])
  })
})
