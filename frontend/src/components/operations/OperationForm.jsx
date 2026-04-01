import React, { useState, useEffect } from 'react'
import { useCategories, useUsers } from '../../hooks/index'
import { Button, Alert } from '../ui/index'
import { OPERATION_TYPES, PAYMENT_TYPES, apiError } from '../../utils/index'
import { useI18n } from '../../i18n'
import { format } from 'date-fns'
import styles from './OperationForm.module.css'

const EMPTY = {
  amount: '',
  currency: 'EUR',
  type: 'expense',
  payment_type: 'card',
  description: '',
  is_recurring: false,
  recurring_end_date: '',
  operation_date: format(new Date(), "yyyy-MM-dd'T'HH:mm"),
  category_id: '',
  user_id: '',
}

export default function OperationForm({ initial = {}, onSubmit, onCancel, loading }) {
  const { lang } = useI18n()
  const [form, setForm] = useState({ ...EMPTY, ...initial })
  const [error, setError] = useState(null)
  const { categories } = useCategories()
  const { users } = useUsers()

  useEffect(() => {
    setForm({ ...EMPTY, ...initial })
  }, [initial])

  useEffect(() => {
    if (categories.length && !form.category_id) {
      const def = categories.find((c) => c.is_default) || categories[0]
      setForm((f) => ({ ...f, category_id: def?.id || '' }))
    }
    if (users.length && !form.user_id) {
      setForm((f) => ({ ...f, user_id: users[0]?.id || '' }))
    }
  }, [categories, users])

  const set = (key, val) => setForm((f) => ({ ...f, [key]: val }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const payload = {
        ...form,
        amount: parseFloat(form.amount),
        category_id: parseInt(form.category_id),
        user_id: parseInt(form.user_id),
        operation_date: new Date(form.operation_date).toISOString(),
        recurring_end_date: form.recurring_end_date
          ? new Date(form.recurring_end_date).toISOString()
          : null,
      }
      await onSubmit(payload)
    } catch (err) {
      setError(apiError(err))
    }
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      {error && <Alert type="error">{error}</Alert>}

      <div className={styles.typeToggle}>
        {OPERATION_TYPES.map((t) => (
          <button
            key={t.value}
            type="button"
            className={`${styles.typeBtn} ${form.type === t.value ? styles[`type_${t.value}`] : ''}`}
            onClick={() => set('type', t.value)}
          >
            {t.value === 'income' ? '▲' : '▼'} {lang === 'ru' ? (t.value === 'income' ? 'Доход' : 'Расход') : t.label}
          </button>
        ))}
      </div>

      <div className={styles.row}>
        <div className={styles.field}>
          <label>{lang === 'ru' ? 'Сумма (EUR)' : 'Amount (EUR)'}</label>
          <input
            type="number"
            step="0.01"
            min="0.01"
            required
            placeholder="0.00"
            inputMode="decimal"
            value={form.amount}
            onChange={(e) => set('amount', e.target.value)}
          />
        </div>
        <div className={styles.field}>
          <label>{lang === 'ru' ? 'Способ оплаты' : 'Payment Type'}</label>
          <select value={form.payment_type} onChange={(e) => set('payment_type', e.target.value)}>
            {PAYMENT_TYPES.map((p) => (
              <option key={p.value} value={p.value}>{lang === 'ru'
                ? ({ cash: 'Наличные', card: 'Карта', bank_transfer: 'Банковский перевод', other: 'Другое' }[p.value] || p.label)
                : p.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className={styles.row}>
        <div className={styles.field}>
          <label>{lang === 'ru' ? 'Категория' : 'Category'}</label>
          <select value={form.category_id} onChange={(e) => set('category_id', e.target.value)} required>
            <option value="">{lang === 'ru' ? 'Выберите категорию' : 'Select category'}</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div className={styles.field}>
          <label>{lang === 'ru' ? 'Пользователь' : 'User'}</label>
          <select value={form.user_id} onChange={(e) => set('user_id', e.target.value)} required>
            <option value="">{lang === 'ru' ? 'Выберите пользователя' : 'Select user'}</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className={styles.field}>
        <label>{lang === 'ru' ? 'Дата и время' : 'Date & Time'}</label>
        <input
          type="datetime-local"
          required
          value={form.operation_date}
          onChange={(e) => set('operation_date', e.target.value)}
        />
      </div>

      <div className={styles.field}>
        <label>{lang === 'ru' ? 'Описание' : 'Description'}</label>
        <textarea
          rows={3}
          placeholder={lang === 'ru' ? 'Необязательная заметка...' : 'Optional note...'}
          value={form.description}
          onChange={(e) => set('description', e.target.value)}
        />
      </div>

      <div className={styles.recurringRow}>
        <label className={styles.checkLabel}>
          <input
            type="checkbox"
            checked={form.is_recurring}
            onChange={(e) => set('is_recurring', e.target.checked)}
          />
          {lang === 'ru' ? 'Повторяется' : 'Recurring'}
        </label>
        {form.is_recurring && (
          <div className={styles.field} style={{ flex: 1 }}>
            <label>{lang === 'ru' ? 'Дата окончания (необязательно)' : 'End Date (optional)'}</label>
            <input
              type="date"
              value={form.recurring_end_date}
              onChange={(e) => set('recurring_end_date', e.target.value)}
            />
          </div>
        )}
      </div>

      <div className={styles.actions}>
        <Button type="button" variant="secondary" onClick={onCancel}>{lang === 'ru' ? 'Отмена' : 'Cancel'}</Button>
        <Button type="submit" loading={loading}>{lang === 'ru' ? 'Сохранить операцию' : 'Save Operation'}</Button>
      </div>
    </form>
  )
}
