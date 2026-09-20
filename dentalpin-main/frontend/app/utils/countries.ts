/**
 * Country / currency / timezone option builders shared by the first-run
 * wizard and the clinic settings page. Labels come from the runtime
 * (`Intl.DisplayNames`), so no i18n keys are needed.
 */

export const COUNTRY_CODES = [
  'AD', 'AE', 'AF', 'AG', 'AL', 'AM', 'AO', 'AR', 'AT', 'AU', 'AZ',
  'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BN', 'BO', 'BR', 'BS', 'BT', 'BW', 'BY', 'BZ',
  'CA', 'CD', 'CF', 'CG', 'CH', 'CI', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CY', 'CZ',
  'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ',
  'EC', 'EE', 'EG', 'ER', 'ES', 'ET',
  'FI', 'FJ', 'FM', 'FR',
  'GA', 'GB', 'GD', 'GE', 'GH', 'GM', 'GN', 'GQ', 'GR', 'GT', 'GW', 'GY',
  'HN', 'HR', 'HT', 'HU',
  'ID', 'IE', 'IL', 'IN', 'IQ', 'IR', 'IS', 'IT',
  'JM', 'JO', 'JP',
  'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KZ',
  'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY',
  'MA', 'MC', 'MD', 'ME', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MR', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ',
  'NA', 'NE', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NZ',
  'OM',
  'PA', 'PE', 'PG', 'PH', 'PK', 'PL', 'PT', 'PW', 'PY',
  'QA',
  'RO', 'RS', 'RU', 'RW',
  'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SI', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SY', 'SZ',
  'TD', 'TG', 'TH', 'TJ', 'TL', 'TM', 'TN', 'TO', 'TR', 'TT', 'TV', 'TW', 'TZ',
  'UA', 'UG', 'US', 'UY', 'UZ',
  'VA', 'VC', 'VE', 'VN', 'VU',
  'WS',
  'XK',
  'YE',
  'ZA', 'ZM', 'ZW'
]

export interface SelectOption { value: string, label: string }

function displayNames(locale: string, type: Intl.DisplayNamesType): Intl.DisplayNames | null {
  try {
    return new Intl.DisplayNames([locale], { type })
  } catch {
    return null
  }
}

export function countryOptions(locale: string): SelectOption[] {
  const names = displayNames(locale, 'region')
  const collator = new Intl.Collator(locale, { sensitivity: 'base' })
  return COUNTRY_CODES
    .map(code => ({ value: code, label: names?.of(code) ?? code }))
    .sort((a, b) => collator.compare(a.label, b.label))
}

export function translateCountry(locale: string, value: string | undefined | null): string {
  if (!value) return ''
  if (/^[A-Za-z]{2}$/.test(value)) {
    return displayNames(locale, 'region')?.of(value.toUpperCase()) ?? value
  }
  return value
}

/** Full ISO 4217 list from the runtime — the backend accepts any `^[A-Z]{3}$`. */
export function currencyOptions(locale: string): SelectOption[] {
  const names = displayNames(locale, 'currency')
  const collator = new Intl.Collator(locale, { sensitivity: 'base' })
  return Intl.supportedValuesOf('currency')
    .map(code => ({ value: code, label: names?.of(code) ? `${code} — ${names.of(code)}` : code }))
    .sort((a, b) => collator.compare(a.label, b.label))
}

/** Full IANA list from the runtime. */
export function timezoneOptions(): SelectOption[] {
  return Intl.supportedValuesOf('timeZone').map(tz => ({ label: tz, value: tz }))
}

/** Best-effort ISO2 guess from the browser (`es-ES` → `ES`). */
export function guessBrowserCountry(): string | null {
  if (typeof navigator === 'undefined') return null
  for (const lang of navigator.languages ?? [navigator.language]) {
    const region = lang.split('-')[1]?.toUpperCase()
    if (region && COUNTRY_CODES.includes(region)) return region
  }
  return null
}

export function browserTimezone(): string | null {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || null
  } catch {
    return null
  }
}
