import { subMonths, startOfMonth, endOfMonth } from 'date-fns'
import { format, toZonedTime, fromZonedTime } from 'date-fns-tz'

const pad = (value) => String(value).padStart(2, '0')

export const formatCurrency = (amount, currency = 'EUR') =>
  new Intl.NumberFormat('de-DE', { style: 'currency', currency }).format(Number(amount))

export const formatDate = (date, timezone = 'UTC') => {
  if (!date) return '—'
  const d = typeof date === 'string' ? new Date(date) : date
  return format(toZonedTime(d, timezone), 'dd MMM yyyy', { timeZone: timezone })
}

export const formatDateTime = (date, timezone = 'UTC') => {
  if (!date) return '—'
  const d = typeof date === 'string' ? new Date(date) : date
  return format(toZonedTime(d, timezone), 'dd MMM yyyy, HH:mm', { timeZone: timezone })
}

export const toLocalDateTimeInput = (date = new Date(), timezone = 'UTC') => {
  const d = typeof date === 'string' ? new Date(date) : date
  if (!(d instanceof Date) || Number.isNaN(d.getTime())) return ''
  const zoned = toZonedTime(d, timezone)
  return format(zoned, "yyyy-MM-dd'T'HH:mm", { timeZone: timezone })
}

export const toLocalDateInput = (date, timezone = 'UTC') => {
  if (!date) return ''
  const d = typeof date === 'string' ? new Date(date) : date
  if (!(d instanceof Date) || Number.isNaN(d.getTime())) return ''
  const zoned = toZonedTime(d, timezone)
  return format(zoned, 'yyyy-MM-dd', { timeZone: timezone })
}

export const localDateTimeInputToIso = (value, timezone = 'UTC') =>
  value ? fromZonedTime(new Date(value), timezone).toISOString() : null

export const prevMonthRange = (timezone = 'UTC') => {
  const nowUtc = new Date()
  const nowZoned = toZonedTime(nowUtc, timezone)
  const prev = subMonths(nowZoned, 1)
  return {
    date_from: fromZonedTime(startOfMonth(prev), timezone).toISOString(),
    date_to: fromZonedTime(endOfMonth(prev), timezone).toISOString(),
  }
}

export const currentMonthRange = (timezone = 'UTC') => {
  const nowUtc = new Date()
  const nowZoned = toZonedTime(nowUtc, timezone)
  return {
    date_from: fromZonedTime(startOfMonth(nowZoned), timezone).toISOString(),
    date_to: fromZonedTime(endOfMonth(nowZoned), timezone).toISOString(),
  }
}

export const monthName = (month, lang = 'en') =>
  new Date(2000, month - 1, 1).toLocaleString(lang === 'ru' ? 'ru-RU' : 'en-US', { month: 'long' })


export const OPERATION_TYPES = [
  { value: 'income', label: 'Income' },
  { value: 'expense', label: 'Expense' },
]

export const apiError = (err) =>
  err?.response?.data?.detail || err?.message || 'Something went wrong'
