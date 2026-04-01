import React, { useState, useEffect } from 'react'
import { categoriesApi } from '../api/index'
import { Button, Card, PageHeader, EmptyState, Alert, Spinner } from '../components/ui/index'
import { useI18n } from '../i18n'
import Modal from '../components/ui/Modal'
import { apiError } from '../utils/index'
import styles from './Categories.module.css'

const EMPTY_FORM = { name: '', description: '', color: '#6c8fff', icon: '' }

export default function CategoriesPage() {
  const { t } = useI18n()
  const [categories, setCategories] = useState([])
  const [loading, setLoading]       = useState(true)
  const [modalOpen, setModalOpen]   = useState(false)
  const [editing, setEditing]       = useState(null)
  const [form, setForm]             = useState(EMPTY_FORM)
  const [saving, setSaving]         = useState(false)
  const [error, setError]           = useState(null)

  const load = async () => {
    setLoading(true)
    try { setCategories(await categoriesApi.list()) }
    catch (e) { setError(apiError(e)) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setModalOpen(true) }
  const openEdit   = (c) => { setEditing(c); setForm({ name:c.name, description:c.description||'', color:c.color||'#6c8fff', icon:c.icon||'' }); setModalOpen(true) }

  const handleSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError(null)
    try {
      if (editing) await categoriesApi.update(editing.id, form)
      else         await categoriesApi.create(form)
      setModalOpen(false); load()
    } catch (err) { setError(apiError(err)) }
    finally { setSaving(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm(t('confirmDeleteCategory'))) return
    try { await categoriesApi.delete(id); load() }
    catch (e) { setError(apiError(e)) }
  }

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div>
      <PageHeader
        title={t('categoriesTitle')}
        subtitle={t('categoriesSubtitle')}
        action={<Button onClick={openCreate}>{t('newCategory')}</Button>}
      />

      {error && <Alert type="error">{error}</Alert>}

      {loading ? (
        <div className={styles.center}><Spinner size={28} /></div>
      ) : categories.length === 0 ? (
        <EmptyState icon="🏷" title={t('noCategories')} />
      ) : (
        <div className={styles.grid}>
          {categories.map(cat => (
            <Card key={cat.id} className={styles.catCard}>
              <div className={styles.catHeader}>
                <div className={styles.colorDot} style={{ background: cat.color || '#9E9E9E' }} />
                <span className={styles.catName}>{cat.name}</span>
                {cat.is_default && <span className={styles.defaultBadge}>{t('defaultCategory')}</span>}
              </div>
              {cat.description && <p className={styles.catDesc}>{cat.description}</p>}
              <div className={styles.catActions}>
                <Button size="sm" variant="ghost" onClick={() => openEdit(cat)}>{t('edit')}</Button>
                {!cat.is_default && (
                  <Button size="sm" variant="danger" onClick={() => handleDelete(cat.id)}>{t('delete')}</Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editing ? t('editCategory') : t('createCategory')}
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setModalOpen(false)}>{t('cancel')}</Button>
            <Button type="submit" form="cat-form" loading={saving}>{t('save')}</Button>
          </>
        }
      >
        <form id="cat-form" onSubmit={handleSubmit} className={styles.form}>
          {error && <Alert type="error">{error}</Alert>}
          <div className={styles.field}>
            <label>{t('categoryName')}</label>
            <input required value={form.name} onChange={e => set('name', e.target.value)} placeholder="e.g. Groceries" />
          </div>
          <div className={styles.field}>
            <label>{t('categoryDescription')}</label>
            <input value={form.description} onChange={e => set('description', e.target.value)} placeholder={t('optional')} />
          </div>
          <div className={styles.row}>
            <div className={styles.field}>
              <label>{t('color')}</label>
              <div className={styles.colorRow}>
                <input type="color" value={form.color} onChange={e => set('color', e.target.value)} className={styles.colorInput} />
                <input value={form.color} onChange={e => set('color', e.target.value)} placeholder="#6c8fff" style={{flex:1}} />
              </div>
            </div>
            <div className={styles.field}>
              <label>{t('icon')}</label>
              <input value={form.icon} onChange={e => set('icon', e.target.value)} placeholder="🛒" maxLength={10} />
            </div>
          </div>
        </form>
      </Modal>
    </div>
  )
}
