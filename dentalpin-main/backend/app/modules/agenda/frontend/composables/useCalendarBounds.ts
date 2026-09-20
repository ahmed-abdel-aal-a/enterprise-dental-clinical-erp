/**
 * Compute [startHour, endHour] bounds for the calendar based on the
 * clinic's actual opening hours. Falls back to 8–21 when the schedules
 * module is uninstalled (fetch returns null).
 *
 * Hours are interpreted in the *clinic* timezone (parsed from the ISO
 * string verbatim) — never the browser's. Otherwise a clinic in NY
 * viewed from a Madrid browser would shift its 9 AM into 3 PM.
 */
import { useScheduleAvailability } from './useScheduleAvailability'
import { parseIsoParts } from '../utils/date'

const DEFAULT_START = 8
const DEFAULT_END = 21

export interface CalendarBounds {
  startHour: number
  endHour: number
}

export function useCalendarBounds() {
  const { fetchOpenRanges } = useScheduleAvailability()

  async function compute(range: { start: Date, end: Date }): Promise<CalendarBounds> {
    const isoStart = range.start.toISOString().slice(0, 10)
    const isoEnd = range.end.toISOString().slice(0, 10)
    const open = await fetchOpenRanges({ start: isoStart, end: isoEnd })
    if (!open || open.length === 0) {
      return { startHour: DEFAULT_START, endHour: DEFAULT_END }
    }

    let minHour = 24
    let maxHour = 0
    for (const r of open) {
      const s = parseIsoParts(r.start)
      const e = parseIsoParts(r.end)
      minHour = Math.min(minHour, s.hour)
      // Round up the end hour so the last slot is included.
      const endHour = e.minute > 0 || e.second > 0 ? e.hour + 1 : e.hour
      maxHour = Math.max(maxHour, endHour)
    }
    // Safety clamp: keep within [0, 24] and at least 1 hour wide.
    minHour = Math.max(0, Math.min(minHour, 23))
    maxHour = Math.max(minHour + 1, Math.min(maxHour, 24))
    return { startHour: minHour, endHour: maxHour }
  }

  return { compute }
}
