import { format, parseISO, startOfMonth, endOfMonth, subMonths } from 'date-fns'

const pad = (value) => String(value).padStart(2, '0')

export const formatCurrency = (amount, currency = 'EUR') =>
  new Intl.NumberFormat('de-DE', { style: 'currency', currency }).format(Number(amount))

export const formatDate = (date) => {
  if (!date) return '—'
  const d = typeof date === 'string' ? parseISO(date) : date
  return format(d, 'dd MMM yyyy')
}

export const formatDateTime = (date) => {
  if (!date) return '—'
  const d = typeof date === 'string' ? parseISO(date) : date
  return format(d, 'dd MMM yyyy, HH:mm')
}

export const toLocalDateTimeInput = (date = new Date()) => {
  const d = typeof date === 'string' ? parseISO(date) : date
  if (!(d instanceof Date) || Number.isNaN(d.getTime())) return ''
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export const toLocalDateInput = (date) => {
  if (!date) return ''
  const d = typeof date === 'string' ? parseISO(date) : date
  if (!(d instanceof Date) || Number.isNaN(d.getTime())) return ''
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export const localDateTimeInputToIso = (value) => (value ? new Date(value).toISOString() : null)

export const prevMonthRange = () => {
  const prev = subMonths(new Date(), 1)
  return {
    date_from: startOfMonth(prev).toISOString(),
    date_to: endOfMonth(prev).toISOString(),
  }
}

export const currentMonthRange = () => ({
  date_from: startOfMonth(new Date()).toISOString(),
  date_to: endOfMonth(new Date()).toISOString(),
})

export const monthName = (month, lang = 'en') =>
  new Date(2000, month - 1, 1).toLocaleString(lang === 'ru' ? 'ru-RU' : 'en-US', { month: 'long' })


export const OPERATION_TYPES = [
  { value: 'income', label: 'Income' },
  { value: 'expense', label: 'Expense' },
]

export const apiError = (err) =>
  err?.response?.data?.detail || err?.message || 'Something went wrong'
