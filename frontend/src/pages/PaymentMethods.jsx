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
  const [isCreate, setIsCreate] = useState(false)
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

  const openCreate = () => {
    setIsCreate(true)
    setEditing(null)
    setForm(EMPTY)
  }

  const openEdit = (item) => {
    setIsCreate(false)
    setEditing(item)
    setForm({ name: item.name })
  }

  const closeModal = () => {
    setIsCreate(false)
    setEditing(null)
    setForm(EMPTY)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      if (isCreate) {
        await paymentMethodsApi.create({ name: form.name.trim() })
      } else if (editing) {
        await paymentMethodsApi.update(editing.id, { name: form.name.trim() })
      }
      closeModal()
      await load()
    } catch (e) {
      setError(apiError(e))
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (item) => {
    if (!confirm(t('confirmDeletePaymentMethod'))) return
    try {
      setError(null)
      await paymentMethodsApi.delete(item.id)
      await load()
    } catch (e) {
      setError(apiError(e))
    }
  }

  return (
    <div>
      {error && <Alert type="error">{error}</Alert>}

      <div className={styles.toolbar}>
        <Button size="sm" onClick={openCreate}>{t('newPaymentMethod')}</Button>
      </div>

      {loading ? (
        <div className={styles.center}><Spinner size={28} /></div>
      ) : items.length === 0 ? (
        <EmptyState icon="💳" title={t('noPaymentMethods')} description={t('paymentMethodsSubtitle')} />
      ) : (
        <div className={styles.grid}>
          {items.map((item) => (
            <Card key={item.id} className={styles.card}>
              <div>
                <p className={styles.name}>{item.name}</p>
                <p className={styles.key}>{item.key}</p>
              </div>
              <div className={styles.actions}>
                <Button
                  size="sm"
                  variant="ghost"
                  className={styles.iconAction}
                  title={t('edit')}
                  aria-label={t('edit')}
                  onClick={() => openEdit(item)}
                >
                  ✎
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  className={styles.iconAction}
                  title={t('delete')}
                  aria-label={t('delete')}
                  onClick={() => handleDelete(item)}
                >
                  🗑
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={isCreate || !!editing}
        onClose={closeModal}
        title={isCreate ? t('createPaymentMethod') : t('editPaymentMethod')}
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={closeModal}>{t('cancel')}</Button>
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


