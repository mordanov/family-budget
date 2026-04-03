import React, { useState, useEffect, useCallback } from 'react'
import { operationsApi } from '../api/index'
import { Button, PageHeader, Badge, EmptyState, Alert, Spinner, Card } from '../components/ui/index'
import Modal from '../components/ui/Modal'
import OperationForm from '../components/operations/OperationForm'
import AttachmentManager from '../components/operations/AttachmentManager'
import { useI18n } from '../i18n'
import { formatCurrency, formatDateTime, apiError, toLocalDateInput, toLocalDateTimeInput } from '../utils/index'
import { fromZonedTime } from 'date-fns-tz'
import { useCategories, usePaymentMethods, useUsers, useTimezone } from '../hooks/index'
import styles from './Operations.module.css'

function toFilterDateStart(value, timezone) {
  return value ? fromZonedTime(new Date(`${value}T00:00:00`), timezone).toISOString() : undefined
}

function toFilterDateEnd(value, timezone) {
  return value ? fromZonedTime(new Date(`${value}T23:59:59`), timezone).toISOString() : undefined
}

function mapOperationToInitial(op, timezone, { copy = false } = {}) {
  return {
    ...(copy ? {} : { id: op.id }),
    amount: op.amount,
    currency: op.currency,
    type: op.type,
    payment_method_id: op.payment_method?.id || op.payment_method_id || '',
    description: op.description || '',
    is_recurring: op.is_recurring,
    recurring_end_date: op.recurring_end_date ? toLocalDateInput(op.recurring_end_date, timezone) : '',
    operation_date: copy ? toLocalDateTimeInput(new Date(), timezone) : toLocalDateTimeInput(op.operation_date, timezone),
    category_id: op.category?.id || op.category_id,
    user_id: op.user?.id || op.user_id,
  }
}

export default function OperationsPage() {
  const { t } = useI18n()
  const timezone = useTimezone()
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 1 })
  const [filters, setFilters] = useState({ page: 1, size: 15 })
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState('create')
  const [editing, setEditing] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const { categories } = useCategories()
  const { users } = useUsers()
  const { paymentMethods } = usePaymentMethods()

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v != null && v !== ''))
      const result = await operationsApi.list(params)
      setData(result)
    } catch (e) {
      setError(apiError(e))
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  const openCreate = () => {
    setModalMode('create')
    setEditing(null)
    setModalOpen(true)
  }
  const openEdit = (op) => {
    setModalMode('edit')
    setEditing(mapOperationToInitial(op, timezone))
    setModalOpen(true)
  }
  const openCopy = (op) => {
    setModalMode('copy')
    setEditing(mapOperationToInitial(op, timezone, { copy: true }))
    setModalOpen(true)
  }

  const handleSubmit = async (payload, { files = [] } = {}) => {
    setSubmitting(true)
    try {
      if (modalMode === 'edit' && editing?.id) {
        await operationsApi.update(editing.id, payload)
      } else if (files.length) {
        await operationsApi.createWithAttachments(payload, files)
      } else {
        await operationsApi.create(payload)
      }
      setEditing(null)
      setModalOpen(false)
      await load()
    } catch (e) {
      throw e
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm(t('confirmDeleteOperation'))) return
    try {
      await operationsApi.delete(id)
      load()
    } catch (e) {
      setError(apiError(e))
    }
  }

  const setFilter = (k, v) => setFilters((f) => ({ ...f, [k]: v || undefined, page: 1 }))

  return (
    <div>
      <PageHeader
        title={t('operationsTitle')}
        subtitle={t('operationsSubtitle', { count: data.total })}
        action={<Button onClick={openCreate}>{t('newOperation')}</Button>}
      />

      {error && <Alert type="error">{error}</Alert>}

      {/* Filters */}
      <Card className={styles.filters}>
        <select onChange={(e) => setFilter('type', e.target.value)} defaultValue="">
          <option value="">{t('allTypes')}</option>
          <option value="income">{t('income')}</option>
          <option value="expense">{t('expense')}</option>
        </select>
        <select onChange={(e) => setFilter('category_id', e.target.value)} defaultValue="">
          <option value="">{t('allCategories')}</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select onChange={(e) => setFilter('user_id', e.target.value)} defaultValue="">
          <option value="">{t('allUsers')}</option>
          {users.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
        </select>
        <select onChange={(e) => setFilter('payment_method_id', e.target.value)} defaultValue="">
          <option value="">{t('allPaymentTypes')}</option>
          {paymentMethods.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        <input
          type="date"
          placeholder={t('dateFrom')}
          onChange={(e) => setFilter('date_from', toFilterDateStart(e.target.value, timezone))}
        />
        <input
          type="date"
          placeholder={t('dateTo')}
          onChange={(e) => setFilter('date_to', toFilterDateEnd(e.target.value, timezone))}
        />
      </Card>

      {/* Table */}
      {loading ? (
        <div className={styles.loadingRow}><Spinner /></div>
      ) : data.items.length === 0 ? (
        <EmptyState icon="💸" title={t('noOperations')} description={t('createFirstOperation')} />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>{t('tableDate')}</th>
                <th>{t('tableType')}</th>
                <th>{t('tableAmount')}</th>
                <th>{t('tableCategory')}</th>
                <th>{t('tableUser')}</th>
                <th>{t('tablePayment')}</th>
                <th>{t('tableDescription')}</th>
                <th>{t('attachments')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((op) => (
                <tr key={op.id} className={styles.row}>
                  <td data-label={t('tableDate')} className={styles.date}>{formatDateTime(op.operation_date, timezone)}</td>
                  <td data-label={t('tableType')} className={styles.typeCell}><Badge type={op.type} /></td>
                  <td data-label={t('tableAmount')} className={`${styles.amount} ${op.type === 'income' ? 'amount-income' : 'amount-expense'}`}>
                    {op.type === 'income' ? '+' : '-'}{formatCurrency(op.amount)}
                    {op.is_recurring && <span className={styles.recurBadge}>↻</span>}
                  </td>
                  <td data-label={t('tableCategory')}>
                    <span className={styles.catChip}>
                      <span style={{ background: op.category?.color || '#9E9E9E' }} className={styles.catDot} />
                      {op.category?.name}
                    </span>
                  </td>
                  <td data-label={t('tableUser')}>{op.user?.name}</td>
                  <td data-label={t('tablePayment')} className={styles.muted}>{op.payment_method?.name || op.payment_type?.replace('_', ' ')}</td>
                  <td data-label={t('tableDescription')} className={styles.desc}>{op.description || '—'}</td>
                  <td data-label={t('attachments')} className={styles.attachmentsCell}>
                    {op.attachments?.length || 0}
                  </td>
                  <td data-label={t('tableActions')}>
                    <div className={styles.actions}>
                      <Button size="sm" variant="ghost" className={styles.iconAction} title={t('copy')} aria-label={t('copy')} onClick={() => openCopy(op)}>⧉</Button>
                      <Button size="sm" variant="ghost" className={styles.iconAction} title={t('edit')} aria-label={t('edit')} onClick={() => openEdit(op)}>✎</Button>
                      <Button size="sm" variant="danger" className={styles.iconAction} title={t('delete')} aria-label={t('delete')} onClick={() => handleDelete(op.id)}>🗑</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {data.pages > 1 && (
        <div className={styles.pagination}>
          <Button size="sm" variant="secondary" disabled={data.page <= 1}
            onClick={() => setFilters((f) => ({ ...f, page: f.page - 1 }))}>
            {`← ${t('prev')}`}
          </Button>
          <span className={styles.pageInfo}>{t('pageOf', { page: data.page, pages: data.pages })}</span>
          <Button size="sm" variant="secondary" disabled={data.page >= data.pages}
            onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}>
            {`${t('next')} →`}
          </Button>
        </div>
      )}

      {/* Modal */}
      <Modal
        open={modalOpen}
        onClose={() => { setModalOpen(false); setEditing(null) }}
        title={modalMode === 'edit' ? t('operationsEditTitle') : modalMode === 'copy' ? t('operationsCopyTitle') : t('operationsNewTitle')}
        size="lg"
      >
        <OperationForm
          initial={editing || {}}
          onSubmit={handleSubmit}
          onCancel={() => { setModalOpen(false); setEditing(null) }}
          loading={submitting}
          allowCreateAttachments
        />
        {modalMode === 'edit' && editing?.id ? (
          <AttachmentManager operationId={editing.id} />
        ) : null}
      </Modal>
    </div>
  )
}
