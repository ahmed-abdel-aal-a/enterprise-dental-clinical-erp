/**
 * Compute blocked-time segments (clinic closed, professional off) for the
 * desktop calendar grid. Returns segments keyed by date so consumers can
 * paint per-day overlays without re-deriving slot math.
 *
 * 404-tolerant via `useScheduleAvailability` — if the schedules module is
 * uninstalled the result is an empty array and the calendar renders normally.
 */
import type { Ref } from 'vue'
import { useScheduleAvailability } from './useScheduleAvailability'
import type { IsoParts } from '../utils/date'
import { formatLocalDate, isoPartsToDateKey, parseIsoParts } from '../utils/date'

export interface BlockedSegment {
  dateKey: string
  professionalId: string | null
  startSlot: number
  endSlot: number
  state: 'clinic_closed' | 'professional_off'
  reason: string | null
}

interface ProfessionalLike { id: string }

export function useBlockedSegments(opts: {
  startHour: Ref<number>
  endHour: Ref<number>
  slotMinutes: number
}) {
  const { fetch: fetchAvailability } = useScheduleAvailability()

  function timeToSlotIndex(parts: IsoParts): number {
    const mins = parts.hour * 60 + parts.minute
    return (mins - opts.startHour.value * 60) / opts.slotMinutes
  }

  function gridSlotsPerDay(): number {
    return ((opts.endHour.value - opts.startHour.value) * 60) / opts.slotMinutes
  }

  function rangesToSegments(
    ranges: Array<{
      start: string
      end: string
      state: 'open' | 'clinic_closed' | 'professional_off'
      professional_id: string | null
      reason: string | null
    }>,
    professionalId: string | null
  ): BlockedSegment[] {
    const out: BlockedSegment[] = []
    const maxSlot = gridSlotsPerDay()
    for (const r of ranges) {
      if (r.state === 'open') continue
      // Parse in clinic-local components — the backend serializes ranges
      // with the clinic's timezone offset, but the calendar grid is
      // rendered in clinic-local hours regardless of the browser TZ.
      const startParts = parseIsoParts(r.start)
      const endParts = parseIsoParts(r.end)
      const startSlot = Math.max(0, timeToSlotIndex(startParts))
      const endSlot = Math.min(maxSlot, timeToSlotIndex(endParts))
      if (endSlot <= startSlot) continue
      out.push({
        dateKey: isoPartsToDateKey(startParts),
        professionalId,
        startSlot,
        endSlot,
        state: r.state,
        reason: r.reason
      })
    }
    return out
  }

  /**
   * Fetch availability for [start, end] and return blocked segments.
   *
   * - Omit `professionals` to get a single clinic-wide call (week view).
   * - Pass professionals to get per-professional segments (day view per-pro
   *   columns). Each professional triggers its own backend call so the
   *   resolver can compose clinic + professional precedence correctly.
   */
  async function compute(args: {
    start: Date
    end: Date
    professionals?: ProfessionalLike[]
  }): Promise<BlockedSegment[]> {
    const isoStart = formatLocalDate(args.start)
    const isoEnd = formatLocalDate(args.end)

    if (!args.professionals || args.professionals.length === 0) {
      const payload = await fetchAvailability({ start: isoStart, end: isoEnd })
      if (!payload) return []
      return rangesToSegments(payload.ranges, null)
    }

    const payloads = await Promise.all(
      args.professionals.map(prof =>
        fetchAvailability({
          start: isoStart,
          end: isoEnd,
          professional_id: prof.id
        }).then(p => ({ prof, payload: p }))
      )
    )
    const out: BlockedSegment[] = []
    for (const { prof, payload } of payloads) {
      if (!payload) continue
      out.push(...rangesToSegments(payload.ranges, prof.id))
    }
    return out
  }

  return { compute }
}
