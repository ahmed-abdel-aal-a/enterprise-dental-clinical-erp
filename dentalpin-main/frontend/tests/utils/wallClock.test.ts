import { describe, expect, it } from 'vitest'
import { clinicNow, parseWallClock } from '~/utils/wallClock'

describe('parseWallClock', () => {
  it('keeps the clinic wall-clock hour regardless of the offset', () => {
    for (const iso of [
      '2026-08-14T12:00:00+02:00',
      '2026-08-14T12:00:00-05:00',
      '2026-08-14T12:00:00Z',
      '2026-08-14T12:00:00.123+05:30',
      '2026-08-14T12:00:00'
    ]) {
      const d = parseWallClock(iso)
      expect([d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes()]).toEqual([2026, 7, 14, 12, 0])
    }
  })

  it('rejects non-ISO input', () => {
    expect(() => parseWallClock('yesterday')).toThrow()
  })
})

describe('clinicNow', () => {
  it('returns the clinic wall-clock, not the browser one', () => {
    const tokyo = clinicNow('Asia/Tokyo')
    const lima = clinicNow('America/Lima')
    // Tokyo is 14h ahead of Lima year-round (no DST on either side).
    const diffH = ((tokyo.getTime() - lima.getTime()) / 3_600_000 + 24) % 24
    expect(Math.round(diffH)).toBe(14)
  })

  it('falls back to the browser clock for unknown zones', () => {
    expect(Math.abs(clinicNow('Not/AZone').getTime() - Date.now())).toBeLessThan(2000)
    expect(Math.abs(clinicNow(null).getTime() - Date.now())).toBeLessThan(2000)
  })
})
