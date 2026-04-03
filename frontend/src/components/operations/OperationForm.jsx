import React, { useMemo, useRef, useState, useEffect } from 'react'
import { useCategories, usePaymentMethods, useUsers, useTimezone } from '../../hooks/index'
import { Button, Alert } from '../ui/index'
import {
  OPERATION_TYPES,
  apiError,
  localDateTimeInputToIso,
  toLocalDateInput,
  toLocalDateTimeInput,
} from '../../utils/index'
import { useI18n } from '../../i18n'
import styles from './OperationForm.module.css'

const createEmpty = (timezone = 'UTC') => ({
  amount: '',
  currency: 'EUR',
  type: 'expense',
  payment_method_id: '',
  description: '',
  is_recurring: false,
  recurring_end_date: '',
  operation_date: toLocalDateTimeInput(new Date(), timezone),
  category_id: '',
  user_id: '',
})

const normalizeInitial = (initial = {}, timezone = 'UTC') => ({
  ...createEmpty(timezone),
  ...initial,
  payment_method_id: initial.payment_method_id || initial.payment_method?.id || '',
  operation_date: initial.operation_date
    ? toLocalDateTimeInput(initial.operation_date, timezone)
    : toLocalDateTimeInput(new Date(), timezone),
  recurring_end_date: initial.recurring_end_date ? toLocalDateInput(initial.recurring_end_date, timezone) : '',
})

export default function OperationForm({ initial = {}, onSubmit, onCancel, loading, allowCreateAttachments = false }) {
  const { t } = useI18n()
  const timezone = useTimezone()
  const fileInputRef = useRef(null)
  const [form, setForm] = useState(() => normalizeInitial(initial, timezone))
  const [selectedFiles, setSelectedFiles] = useState([])
  const [error, setError] = useState(null)
  const { categories } = useCategories()
  const { users } = useUsers()
  const { paymentMethods } = usePaymentMethods()

  const isEditing = Boolean(initial?.id)
  const canAttachOnCreate = allowCreateAttachments && !isEditing
  const operationTypes = useMemo(() => OPERATION_TYPES, [])

  useEffect(() => {
    setForm(normalizeInitial(initial, timezone))
    setSelectedFiles([])
  }, [initial, timezone])

  useEffect(() => {
    if (categories.length && !form.category_id) {
      const def = categories.find((c) => c.is_default) || categories[0]
      setForm((f) => ({ ...f, category_id: def?.id || '' }))
    }
    if (users.length && !form.user_id) {
      setForm((f) => ({ ...f, user_id: users[0]?.id || '' }))
    }
    if (paymentMethods.length && !form.payment_method_id) {
      const preferred = paymentMethods.find((item) => item.key === 'card') || paymentMethods[0]
      setForm((f) => ({ ...f, payment_method_id: preferred?.id || '' }))
    }
  }, [categories, users, paymentMethods, form.category_id, form.user_id, form.payment_method_id])

  const set = (key, val) => setForm((f) => ({ ...f, [key]: val }))

  const addFiles = (files) => {
    const nextFiles = Array.from(files || [])
    if (!nextFiles.length) return
    setSelectedFiles((current) => [...current, ...nextFiles])
  }

  const removeSelectedFile = (index) => {
    setSelectedFiles((current) => current.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const payload = {
        ...form,
        amount: parseFloat(form.amount),
        category_id: parseInt(form.category_id),
        user_id: parseInt(form.user_id),
        payment_method_id: parseInt(form.payment_method_id),
        operation_date: localDateTimeInputToIso(form.operation_date, timezone),
        recurring_end_date: form.recurring_end_date
          ? localDateTimeInputToIso(`${form.recurring_end_date}T00:00:00`, timezone)
          : null,
      }
      await onSubmit(payload, { files: selectedFiles })
    } catch (err) {
      setError(apiError(err))
    }
  }

  return (
    <form onSubmit={handleSubmit} className={styles.form}>
      {error && <Alert type="error">{error}</Alert>}

      <div className={styles.typeToggle}>
        {operationTypes.map((typeOption) => (
          <button
            key={typeOption.value}
            type="button"
            className={`${styles.typeBtn} ${form.type === typeOption.value ? styles[`type_${typeOption.value}`] : ''}`}
            onClick={() => set('type', typeOption.value)}
          >
            {typeOption.value === 'income' ? '▲' : '▼'} {typeOption.value === 'income' ? t('income') : t('expense')}
          </button>
        ))}
      </div>

      <div className={styles.row}>
        <div className={styles.field}>
          <label>{t('tableAmount')} (EUR)</label>
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
          <label>{t('paymentType')}</label>
          <select value={form.payment_method_id} onChange={(e) => set('payment_method_id', e.target.value)} required>
            <option value="">{t('selectPaymentMethod')}</option>
            {paymentMethods.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className={styles.row}>
        <div className={styles.field}>
          <label>{t('category')}</label>
          <select value={form.category_id} onChange={(e) => set('category_id', e.target.value)} required>
            <option value="">{t('selectCategory')}</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div className={styles.field}>
          <label>{t('user')}</label>
          <select value={form.user_id} onChange={(e) => set('user_id', e.target.value)} required>
            <option value="">{t('selectUser')}</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className={styles.field}>
        <label>{t('dateTime')}</label>
        <input
          type="datetime-local"
          required
          value={form.operation_date}
          onChange={(e) => set('operation_date', e.target.value)}
        />
      </div>

      <div className={styles.field}>
        <label>{t('tableDescription')}</label>
        <textarea
          rows={3}
          placeholder={t('optionalNote')}
          value={form.description}
          onChange={(e) => set('description', e.target.value)}
        />
      </div>

      {canAttachOnCreate && (
        <div className={styles.field}>
          <label>{t('attachments')}</label>
          <div className={styles.attachCreateRow}>
            <Button type="button" variant="secondary" onClick={() => fileInputRef.current?.click()}>
              {t('addAttachments')}
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              hidden
              accept="image/*,application/pdf"
              multiple
              onChange={(e) => {
                addFiles(e.target.files)
                e.target.value = ''
              }}
            />
            <span className={styles.attachHint}>{t('attachmentsWillBeSavedTogether')}</span>
          </div>
          {!!selectedFiles.length && (
            <div className={styles.selectedFiles}>
              {selectedFiles.map((file, index) => (
                <div key={`${file.name}-${index}`} className={styles.selectedFileItem}>
                  <span>{file.name}</span>
                  <Button type="button" size="sm" variant="ghost" onClick={() => removeSelectedFile(index)}>
                    ✕
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className={styles.recurringRow}>
        <label className={styles.checkLabel}>
          <input
            type="checkbox"
            checked={form.is_recurring}
            onChange={(e) => set('is_recurring', e.target.checked)}
          />
          {t('recurring')}
        </label>
        {form.is_recurring && (
          <div className={styles.field} style={{ flex: 1 }}>
            <label>{t('endDateOptional')}</label>
            <input
              type="date"
              value={form.recurring_end_date}
              onChange={(e) => set('recurring_end_date', e.target.value)}
            />
          </div>
        )}
      </div>

      <div className={styles.actions}>
        <Button type="button" variant="secondary" onClick={onCancel}>{t('cancel')}</Button>
        <Button type="submit" loading={loading}>{t('saveOperation')}</Button>
      </div>
    </form>
  )
}
