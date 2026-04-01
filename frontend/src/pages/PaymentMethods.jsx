import React, { useEffect, useState } from 'react'
import { paymentMethodsApi } from '../api'
import { Alert, Button, Card, EmptyState, Spinner } from '../components/ui'
import Modal from '../components/ui/Modal'
import { useI18n } from '../i18n'
import { apiError } from '../utils'
import styles from './PaymentMethods.module.css'

const EMPTY = { name: '' }

export default function PaymentMethodsPage() {
  const { t } = useI18n()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      setItems(await paymentMethodsApi.list())
    } catch (e) {
      setError(apiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const openEdit = (item) => {
    setEditing(item)
    setForm({ name: item.name })
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!editing) return
    setSaving(true)
    setError(null)
    try {
      await paymentMethodsApi.update(editing.id, { name: form.name.trim() })
      setEditing(null)
      await load()
    } catch (e) {
      setError(apiError(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      {error && <Alert type="error">{error}</Alert>}

      {loading ? (
        <div className={styles.center}><Spinner size={28} /></div>
      ) : items.length === 0 ? (
        <EmptyState icon="💳" title={t('noData')} />
      ) : (
        <div className={styles.grid}>
          {items.map((item) => (
            <Card key={item.id} className={styles.card}>
              <div>
                <p className={styles.name}>{item.name}</p>
                <p className={styles.key}>{item.key}</p>
              </div>
              <Button size="sm" variant="secondary" onClick={() => openEdit(item)}>
                {t('edit')}
              </Button>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title={t('editPaymentMethod')}
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEditing(null)}>{t('cancel')}</Button>
            <Button type="submit" form="pm-form" loading={saving}>{t('save')}</Button>
          </>
        }
      >
        <form id="pm-form" onSubmit={handleSave} className={styles.form}>
          <label>{t('paymentMethodName')}</label>
          <input
            required
            value={form.name}
            onChange={(e) => setForm({ name: e.target.value })}
            maxLength={60}
          />
        </form>
      </Modal>
    </div>
  )
}


