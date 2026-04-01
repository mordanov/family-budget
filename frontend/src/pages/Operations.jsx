import React, { useState, useEffect, useCallback } from 'react'
import { operationsApi, attachmentsApi } from '../api/index'
import { Button, PageHeader, Badge, EmptyState, Alert, Spinner, Card } from '../components/ui/index'
import Modal from '../components/ui/Modal'
import OperationForm from '../components/operations/OperationForm'
import AttachmentManager from '../components/operations/AttachmentManager'
import { useI18n } from '../i18n'
import { formatCurrency, formatDateTime, apiError } from '../utils/index'
import { useCategories, useUsers } from '../hooks/index'
import styles from './Operations.module.css'

export default function OperationsPage() {
  const { lang, t } = useI18n()
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 1 })
  const [filters, setFilters] = useState({ page: 1, size: 20 })
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [detailOp, setDetailOp] = useState(null)
  const { categories } = useCategories()
  const { users } = useUsers()

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

  const openCreate = () => { setEditing(null); setModalOpen(true) }
  const openEdit = (op) => {
    const init = {
      ...op,
      category_id: op.category.id,
      user_id: op.user.id,
      operation_date: op.operation_date?.slice(0, 16),
      recurring_end_date: op.recurring_end_date?.slice(0, 10) || '',
    }
    setEditing(init)
    setModalOpen(true)
  }

  const handleSubmit = async (payload) => {
    setSubmitting(true)
    try {
      if (editing?.id) {
        await operationsApi.update(editing.id, payload)
        setModalOpen(false)
      } else {
        const created = await operationsApi.create(payload)
        const init = {
          ...created,
          category_id: created.category.id,
          user_id: created.user.id,
          operation_date: created.operation_date?.slice(0, 16),
          recurring_end_date: created.recurring_end_date?.slice(0, 10) || '',
        }
        setEditing(init)
      }
      await load()
    } catch (e) {
      throw e
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this operation?')) return
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
          <option value="income">{lang === 'ru' ? 'Доход' : 'Income'}</option>
          <option value="expense">{lang === 'ru' ? 'Расход' : 'Expense'}</option>
        </select>
        <select onChange={(e) => setFilter('category_id', e.target.value)} defaultValue="">
          <option value="">{t('allCategories')}</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select onChange={(e) => setFilter('user_id', e.target.value)} defaultValue="">
          <option value="">{t('allUsers')}</option>
          {users.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
        </select>
        <select onChange={(e) => setFilter('payment_type', e.target.value)} defaultValue="">
          <option value="">{t('allPaymentTypes')}</option>
          <option value="cash">{lang === 'ru' ? 'Наличные' : 'Cash'}</option>
          <option value="card">Card</option>
          <option value="bank_transfer">{lang === 'ru' ? 'Банковский перевод' : 'Bank Transfer'}</option>
          <option value="other">{lang === 'ru' ? 'Другое' : 'Other'}</option>
        </select>
        <input
          type="date"
          placeholder="From"
          onChange={(e) => setFilter('date_from', e.target.value ? new Date(e.target.value).toISOString() : undefined)}
        />
        <input
          type="date"
          placeholder="To"
          onChange={(e) => setFilter('date_to', e.target.value ? new Date(e.target.value + 'T23:59:59').toISOString() : undefined)}
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
                <th>{lang === 'ru' ? 'Дата' : 'Date'}</th>
                <th>{lang === 'ru' ? 'Тип' : 'Type'}</th>
                <th>{lang === 'ru' ? 'Сумма' : 'Amount'}</th>
                <th>{lang === 'ru' ? 'Категория' : 'Category'}</th>
                <th>{lang === 'ru' ? 'Пользователь' : 'User'}</th>
                <th>{lang === 'ru' ? 'Оплата' : 'Payment'}</th>
                <th>{lang === 'ru' ? 'Описание' : 'Description'}</th>
                <th>{t('attachments')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((op) => (
                <tr key={op.id} className={styles.row}>
                  <td data-label={lang === 'ru' ? 'Дата' : 'Date'} className={styles.date}>{formatDateTime(op.operation_date)}</td>
                  <td data-label={lang === 'ru' ? 'Тип' : 'Type'}><Badge type={op.type} /></td>
                  <td data-label={lang === 'ru' ? 'Сумма' : 'Amount'} className={`${styles.amount} ${op.type === 'income' ? 'amount-income' : 'amount-expense'}`}>
                    {op.type === 'income' ? '+' : '-'}{formatCurrency(op.amount)}
                    {op.is_recurring && <span className={styles.recurBadge}>↻</span>}
                  </td>
                  <td data-label={lang === 'ru' ? 'Категория' : 'Category'}>
                    <span className={styles.catChip}>
                      <span style={{ background: op.category?.color || '#9E9E9E' }} className={styles.catDot} />
                      {op.category?.name}
                    </span>
                  </td>
                  <td data-label={lang === 'ru' ? 'Пользователь' : 'User'}>{op.user?.name}</td>
                  <td data-label={lang === 'ru' ? 'Оплата' : 'Payment'} className={styles.muted}>{op.payment_type?.replace('_', ' ')}</td>
                  <td data-label={lang === 'ru' ? 'Описание' : 'Description'} className={styles.desc}>{op.description || '—'}</td>
                  <td data-label={t('attachments')} className={styles.attachmentsCell}>
                    {op.attachments?.length || 0}
                  </td>
                  <td data-label={lang === 'ru' ? 'Действия' : 'Actions'}>
                    <div className={styles.actions}>
                      <Button size="sm" variant="ghost" onClick={() => openEdit(op)}>{lang === 'ru' ? 'Изменить' : 'Edit'}</Button>
                      <Button size="sm" variant="danger" onClick={() => handleDelete(op.id)}>{lang === 'ru' ? 'Удалить' : 'Delete'}</Button>
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
            {lang === 'ru' ? '← Назад' : '← Prev'}
          </Button>
          <span className={styles.pageInfo}>{lang === 'ru' ? `Страница ${data.page} из ${data.pages}` : `Page ${data.page} of ${data.pages}`}</span>
          <Button size="sm" variant="secondary" disabled={data.page >= data.pages}
            onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}>
            {lang === 'ru' ? 'Далее →' : 'Next →'}
          </Button>
        </div>
      )}

      {/* Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? (lang === 'ru' ? 'Изменить операцию' : 'Edit Operation') : (lang === 'ru' ? 'Новая операция' : 'New Operation')}
        size="lg"
      >
        <OperationForm
          initial={editing || {}}
          onSubmit={handleSubmit}
          onCancel={() => setModalOpen(false)}
          loading={submitting}
        />
        {editing?.id ? (
          <AttachmentManager operationId={editing.id} />
        ) : (
          <p className={styles.attachmentsHint}>
            {lang === 'ru'
              ? 'Сохраните операцию, чтобы добавить фото, снимок камеры или PDF.'
              : 'Save the operation first to add camera photos, images or PDF files.'}
          </p>
        )}
      </Modal>
    </div>
  )
}
