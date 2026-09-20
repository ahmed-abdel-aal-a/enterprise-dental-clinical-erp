/**
 * Spanish NIF / NIE / CIF checksum — client-side port of
 * `backend/app/modules/verifactu/services/nif_validator.py`. Advisory only:
 * the wizard shows a warning, the server enforces just the format.
 */

const DNI_LETTERS = 'TRWAGMYFPDXBNJZSQVHLCKE'
const CIF_LETTER_TABLE = 'JABCDEFGHI'
const CIF_LETTER_ONLY = 'PQSNW'
const CIF_DIGIT_ONLY = 'ABEH'

export function normalizeTaxId(value: string): string {
  return value.trim().toUpperCase().replace(/[\s\-.]/g, '')
}

function checkDni(v: string): boolean {
  if (!/^\d{8}[A-Z]$/.test(v)) return false
  return v[8] === DNI_LETTERS[Number(v.slice(0, 8)) % 23]
}

function checkNie(v: string): boolean {
  if (!/^[XYZ]\d{7}[A-Z]$/.test(v)) return false
  const digits = { X: '0', Y: '1', Z: '2' }[v[0] as 'X' | 'Y' | 'Z'] + v.slice(1, 8)
  return v[8] === DNI_LETTERS[Number(digits) % 23]
}

function checkCif(v: string): boolean {
  if (!/^[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]$/.test(v)) return false
  const orgType = v[0]!
  const control = v[8]!
  let total = 0
  for (let i = 0; i < 7; i++) {
    const d = Number(v[i + 1])
    if (i % 2 === 0) {
      const doubled = d * 2
      total += Math.floor(doubled / 10) + (doubled % 10)
    } else {
      total += d
    }
  }
  const expectedDigit = (10 - (total % 10)) % 10
  const expectedLetter = CIF_LETTER_TABLE[expectedDigit]!
  if (CIF_LETTER_ONLY.includes(orgType)) return control === expectedLetter
  if (CIF_DIGIT_ONLY.includes(orgType)) return control === String(expectedDigit)
  return control === String(expectedDigit) || control === expectedLetter
}

export function isValidSpanishTaxId(value: string | null | undefined): boolean {
  if (!value) return false
  const v = normalizeTaxId(value)
  if (!v) return false
  if (/^\d/.test(v)) return checkDni(v)
  if (/^[XYZ]/.test(v)) return checkNie(v)
  return checkCif(v)
}
