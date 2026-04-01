import { format, parseISO, startOfMonth, endOfMonth, subMonths } from 'date-fns'

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

export const prevMonthRange = () => {
  const prev = subMonths(new Date(), 1)
  return {
    date_from: startOfMonth(prev).toISOString(),
    date_to: endOfMonth(prev).toISOString(),
  }
}

export const monthName = (month) =>
  new Date(2000, month - 1, 1).toLocaleString('default', { month: 'long' })

export const PAYMENT_TYPES = [
  { value: 'cash', label: 'Cash' },
  { value: 'card', label: 'Card' },
  { value: 'bank_transfer', label: 'Bank Transfer' },
  { value: 'other', label: 'Other' },
]

export const OPERATION_TYPES = [
  { value: 'income', label: 'Income' },
  { value: 'expense', label: 'Expense' },
]

export const apiError = (err) =>
  err?.response?.data?.detail || err?.message || 'Something went wrong'
