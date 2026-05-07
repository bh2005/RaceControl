import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { esc, fmtDate, printOpen } from '../utils/print.js'

describe('esc()', () => {
  it('escapes ampersands', () => expect(esc('a & b')).toBe('a &amp; b'))
  it('escapes less-than', () => expect(esc('<div>')).toBe('&lt;div&gt;'))
  it('escapes greater-than', () => expect(esc('a > b')).toBe('a &gt; b'))
  it('handles null/undefined gracefully', () => {
    expect(esc(null)).toBe('')
    expect(esc(undefined)).toBe('')
  })
  it('passes plain text unchanged', () => expect(esc('Hello World')).toBe('Hello World'))
  it('converts numbers to string', () => expect(esc(42)).toBe('42'))
})

describe('fmtDate()', () => {
  it('formats ISO date to German format', () => {
    expect(fmtDate('2026-06-01')).toBe('01.06.2026')
  })
  it('returns empty string for falsy input', () => {
    expect(fmtDate('')).toBe('')
    expect(fmtDate(null)).toBe('')
    expect(fmtDate(undefined)).toBe('')
  })
  it('handles single-digit day and month', () => {
    expect(fmtDate('2026-01-05')).toBe('05.01.2026')
  })
})

describe('printOpen()', () => {
  let mockWindow

  beforeEach(() => {
    mockWindow = {
      document: { write: vi.fn(), close: vi.fn() },
      print: vi.fn(),
    }
    vi.spyOn(window, 'open').mockReturnValue(mockWindow)
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('opens a new browser window', () => {
    printOpen('Testdruck', '<p>Inhalt</p>')
    expect(window.open).toHaveBeenCalledWith('', '_blank', 'width=1100,height=800')
  })

  it('writes HTML including the title', () => {
    printOpen('Mein Titel', '<p>Test</p>')
    const written = mockWindow.document.write.mock.calls[0][0]
    expect(written).toContain('Mein Titel')
    expect(written).toContain('<p>Test</p>')
  })

  it('calls print() after 400 ms', () => {
    printOpen('T', '<p/>')
    expect(mockWindow.print).not.toHaveBeenCalled()
    vi.advanceTimersByTime(400)
    expect(mockWindow.print).toHaveBeenCalledOnce()
  })

  it('shows alert when popup is blocked', () => {
    window.open.mockReturnValue(null)
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})
    printOpen('T', '<p/>')
    expect(alertSpy).toHaveBeenCalledOnce()
  })

  it('escapes special chars in the title', () => {
    printOpen('<script>xss</script>', '')
    const written = mockWindow.document.write.mock.calls[0][0]
    expect(written).not.toContain('<script>')
    expect(written).toContain('&lt;script&gt;')
  })
})
