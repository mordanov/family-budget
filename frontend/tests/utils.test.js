import { describe, it, expect } from 'vitest'
import { formatCurrency, formatDate, monthName, apiError } from '../src/utils/index'

describe('formatCurrency', () => {
  it('formats positive numbers', () => {
    const result = formatCurrency(1234.56)
    expect(result).toContain('1.234,56')
  })
  it('formats zero', () => {
    expect(formatCurrency(0)).toContain('0,00')
  })
  it('formats negative numbers', () => {
    const result = formatCurrency(-500)
    expect(result).toContain('500')
  })
})

describe('monthName', () => {
  it('returns correct month names', () => {
    expect(monthName(1)).toBe('January')
    expect(monthName(6)).toBe('June')
    expect(monthName(12)).toBe('December')
  })
})

describe('formatDate', () => {
  it('returns dash for null', () => {
    expect(formatDate(null)).toBe('—')
    expect(formatDate(undefined)).toBe('—')
  })
  it('formats ISO string', () => {
    const result = formatDate('2024-06-15T12:00:00Z')
    expect(result).toContain('15')
    expect(result).toContain('Jun')
    expect(result).toContain('2024')
  })
})

describe('apiError', () => {
  it('extracts detail from axios error', () => {
    const err = { response: { data: { detail: 'Not found' } } }
    expect(apiError(err)).toBe('Not found')
  })
  it('falls back to message', () => {
    const err = { message: 'Network Error' }
    expect(apiError(err)).toBe('Network Error')
  })
  it('falls back to default', () => {
    expect(apiError({})).toBe('Something went wrong')
  })
})
