import React, { useState, useEffect, useCallback } from 'react'
import { operationsApi, attachmentsApi } from '../api/index'
import { Button, PageHeader, Badge, EmptyState, Alert, Spinner, Card } from '../components/ui/index'
import Modal from '../components/ui/Modal'
import OperationForm from '../components/operations/OperationForm'
import { formatCurrency, formatDateTime, apiError } from '../utils/index'
import { useCategories, useUsers } from '../hooks/index'
import styles from './Operations.module.css'

export default function OperationsPage() {
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
      } else {
        await operationsApi.create(payload)
      }
      setModalOpen(false)
      load()
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
        title="Operations"
        subtitle={`${data.total} operations total`}
        action={<Button onClick={openCreate}>+ New Operation</Button>}
      />

      {error && <Alert type="error">{error}</Alert>}

      {/* Filters */}
      <Card className={styles.filters}>
        <select onChange={(e) => setFilter('type', e.target.value)} defaultValue="">
          <option value="">All Types</option>
          <option value="income">Income</option>
          <option value="expense">Expense</option>
        </select>
        <select onChange={(e) => setFilter('category_id', e.target.value)} defaultValue="">
          <option value="">All Categories</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
        <select onChange={(e) => setFilter('user_id', e.target.value)} defaultValue="">
          <option value="">All Users</option>
          {users.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}
        </select>
        <select onChange={(e) => setFilter('payment_type', e.target.value)} defaultValue="">
          <option value="">All Payment Types</option>
          <option value="cash">Cash</option>
          <option value="card">Card</option>
          <option value="bank_transfer">Bank Transfer</option>
          <option value="other">Other</option>
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
        <EmptyState icon="💸" title="No operations found" description="Create your first operation to get started." />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Category</th>
                <th>User</th>
                <th>Payment</th>
                <th>Description</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((op) => (
                <tr key={op.id} className={styles.row}>
                  <td className={styles.date}>{formatDateTime(op.operation_date)}</td>
                  <td><Badge type={op.type} /></td>
                  <td className={`${styles.amount} ${op.type === 'income' ? 'amount-income' : 'amount-expense'}`}>
                    {op.type === 'income' ? '+' : '-'}{formatCurrency(op.amount)}
                    {op.is_recurring && <span className={styles.recurBadge}>↻</span>}
                  </td>
                  <td>
                    <span className={styles.catChip}>
                      <span style={{ background: op.category?.color || '#9E9E9E' }} className={styles.catDot} />
                      {op.category?.name}
                    </span>
                  </td>
                  <td>{op.user?.name}</td>
                  <td className={styles.muted}>{op.payment_type?.replace('_', ' ')}</td>
                  <td className={styles.desc}>{op.description || '—'}</td>
                  <td>
                    <div className={styles.actions}>
                      <Button size="sm" variant="ghost" onClick={() => openEdit(op)}>Edit</Button>
                      <Button size="sm" variant="danger" onClick={() => handleDelete(op.id)}>Del</Button>
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
            ← Prev
          </Button>
          <span className={styles.pageInfo}>Page {data.page} of {data.pages}</span>
          <Button size="sm" variant="secondary" disabled={data.page >= data.pages}
            onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}>
            Next →
          </Button>
        </div>
      )}

      {/* Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? 'Edit Operation' : 'New Operation'}
        size="md"
      >
        <OperationForm
          initial={editing || {}}
          onSubmit={handleSubmit}
          onCancel={() => setModalOpen(false)}
          loading={submitting}
        />
      </Modal>
    </div>
  )
}
