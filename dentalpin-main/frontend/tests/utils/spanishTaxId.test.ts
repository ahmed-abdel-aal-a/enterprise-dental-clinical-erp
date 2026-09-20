import { describe, expect, it } from 'vitest'
import { isValidSpanishTaxId } from '~/utils/spanishTaxId'

describe('isValidSpanishTaxId', () => {
  it('accepts valid DNI / NIE / CIF', () => {
    expect(isValidSpanishTaxId('12345678Z')).toBe(true)
    expect(isValidSpanishTaxId('x-1234567-l')).toBe(true)
    expect(isValidSpanishTaxId('B12345674')).toBe(true) // digit control
    expect(isValidSpanishTaxId('P1234567D')).toBe(true) // letter control
  })
  it('rejects bad checksums and formats', () => {
    expect(isValidSpanishTaxId('12345678A')).toBe(false)
    expect(isValidSpanishTaxId('B12345678')).toBe(false)
    expect(isValidSpanishTaxId('')).toBe(false)
    expect(isValidSpanishTaxId('1234')).toBe(false)
  })
})
