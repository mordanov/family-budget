import React, { useState, useEffect } from 'react'
import { balancesApi } from '../api/index'
import { Card, PageHeader, Spinner, EmptyState, Button, Alert } from '../components/ui/index'
import { useI18n } from '../i18n'
import Modal from '../components/ui/Modal'
import { formatCurrency, monthName, apiError } from '../utils/index'
import styles from './Balances.module.css'

export default function BalancesPage() {
  const { lang, t } = useI18n()
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
      <PageHeader title={t('monthlyBalancesTitle')} subtitle={t('monthlyBalancesSubtitle')} />

      {error && <Alert type="error">{error}</Alert>}

      {loading ? (
        <div className={styles.center}><Spinner size={28} /></div>
      ) : balances.length === 0 ? (
        <EmptyState icon="⚖" title={t('noBalanceRecords')} description={t('balancesAutoHint')} />
      ) : (
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>{t('period')}</th>
                <th>{t('openingBalance')}</th>
                <th>{t('totalIncome')}</th>
                <th>{t('totalExpense')}</th>
                <th>{t('closingBalance')}</th>
                <th>{t('adjusted')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {balances.map((b) => {
                const net = Number(b.closing_balance) - Number(b.opening_balance)
                return (
                  <tr key={b.id} className={styles.row}>
                    <td className={styles.period}>
                      <span className={styles.month}>{monthName(b.month, lang)}</span>
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
                        <span className={styles.adjBadge}>✎ {t('manual')}</span>
                      )}
                    </td>
                    <td>
                      <Button size="sm" variant="secondary" onClick={() => openEdit(b)}>
                        {t('editOpening')}
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={!!editing} onClose={() => setEditing(null)} title={t('setOpeningBalance')} size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditing(null)}>{t('cancel')}</Button>
            <Button onClick={handleSave} loading={saving}>{t('save')}</Button>
          </>
        }
      >
        {editing && (
          <div className={styles.editForm}>
            <p className={styles.editPeriod}>
              {monthName(editing.month, lang)} {editing.year}
            </p>
            <label>{t('openingBalanceEur')}</label>
            <input
              type="number"
              step="0.01"
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              autoFocus
            />
            <p className={styles.hint}>{t('openingBalanceHint')}</p>
          </div>
        )}
      </Modal>
    </div>
  )
}
