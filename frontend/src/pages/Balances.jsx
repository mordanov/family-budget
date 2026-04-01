import React, { useState, useEffect } from 'react'
import { balancesApi } from '../api/index'
import { Card, PageHeader, Spinner, EmptyState, Button, Alert } from '../components/ui/index'
import Modal from '../components/ui/Modal'
import { formatCurrency, monthName, apiError } from '../utils/index'
import styles from './Balances.module.css'

export default function BalancesPage() {
  const [balances, setBalances] = useState([])
  const [loading, setLoading]   = useState(true)
  const [editing, setEditing]   = useState(null)
  const [inputVal, setInputVal] = useState('')
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState(null)

  const load = async () => {
    setLoading(true)
    try { setBalances(await balancesApi.list()) }
    catch (e) { setError(apiError(e)) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const openEdit = (b) => {
    setEditing(b)
    setInputVal(b.manual_opening_balance ?? b.opening_balance ?? '0')
  }

  const handleSave = async () => {
    setSaving(true); setError(null)
    try {
      await balancesApi.setOpening(editing.year, editing.month, parseFloat(inputVal))
      setEditing(null)
      load()
    } catch (e) { setError(apiError(e)) }
    finally { setSaving(false) }
  }

  return (
    <div>
      <PageHeader title="Monthly Balances" subtitle="Debit & credit summaries, editable opening balances" />

      {error && <Alert type="error">{error}</Alert>}

      {loading ? (
        <div className={styles.center}><Spinner size={28} /></div>
      ) : balances.length === 0 ? (
        <EmptyState icon="⚖" title="No balance records yet" description="Balances are created automatically when you add operations." />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Period</th>
                <th>Opening Balance</th>
                <th>Total Income</th>
                <th>Total Expense</th>
                <th>Closing Balance</th>
                <th>Adjusted</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {balances.map((b) => {
                const net = Number(b.closing_balance) - Number(b.opening_balance)
                return (
                  <tr key={b.id} className={styles.row}>
                    <td className={styles.period}>
                      <span className={styles.month}>{monthName(b.month)}</span>
                      <span className={styles.year}>{b.year}</span>
                    </td>
                    <td className={styles.mono}>{formatCurrency(b.opening_balance)}</td>
                    <td className={`${styles.mono} amount-income`}>+{formatCurrency(b.total_income)}</td>
                    <td className={`${styles.mono} amount-expense`}>-{formatCurrency(b.total_expense)}</td>
                    <td className={`${styles.mono} ${styles.closing}`}
                      style={{color: Number(b.closing_balance)>=0?'var(--color-income)':'var(--color-expense)'}}>
                      {formatCurrency(b.closing_balance)}
                    </td>
                    <td>
                      {b.is_manually_adjusted && (
                        <span className={styles.adjBadge}>✎ manual</span>
                      )}
                    </td>
                    <td>
                      <Button size="sm" variant="secondary" onClick={() => openEdit(b)}>
                        Edit Opening
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={!!editing} onClose={() => setEditing(null)} title="Set Opening Balance" size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditing(null)}>Cancel</Button>
            <Button onClick={handleSave} loading={saving}>Save</Button>
          </>
        }
      >
        {editing && (
          <div className={styles.editForm}>
            <p className={styles.editPeriod}>
              {monthName(editing.month)} {editing.year}
            </p>
            <label>Opening Balance (EUR)</label>
            <input
              type="number"
              step="0.01"
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              autoFocus
            />
            <p className={styles.hint}>
              This overrides the auto-calculated opening balance for this month.
              All subsequent months will be recalculated from this value.
            </p>
          </div>
        )}
      </Modal>
    </div>
  )
}
