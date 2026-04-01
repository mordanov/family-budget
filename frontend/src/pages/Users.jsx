import React, { useState, useEffect } from 'react'
import { usersApi } from '../api/index'
import { Button, Card, PageHeader, EmptyState, Alert, Spinner } from '../components/ui/index'
import { useI18n } from '../i18n'
import Modal from '../components/ui/Modal'
import { formatDate, apiError } from '../utils/index'
import styles from './Users.module.css'

const EMPTY = { name: '', email: '', password: '' }

export default function UsersPage() {
  const { lang } = useI18n()
  const [users, setUsers]       = useState([])
  const [loading, setLoading]   = useState(true)
  const [modalOpen, setModal]   = useState(false)
  const [editing, setEditing]   = useState(null)
  const [form, setForm]         = useState(EMPTY)
  const [saving, setSaving]     = useState(false)
  const [error, setError]       = useState(null)

  const load = async () => {
    setLoading(true)
    try { setUsers(await usersApi.list()) }
    catch (e) { setError(apiError(e)) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const openCreate = () => { setEditing(null); setForm(EMPTY); setModal(true) }
  const openEdit   = (u) => { setEditing(u); setForm({ name: u.name, email: u.email, password: '' }); setModal(true) }

  const handleSubmit = async (e) => {
    e.preventDefault(); setSaving(true); setError(null)
    try {
      const payload = { ...form }
      if (!payload.password) delete payload.password
      if (editing) await usersApi.update(editing.id, payload)
      else         await usersApi.create(payload)
      setModal(false); load()
    } catch (err) { setError(apiError(err)) }
    finally { setSaving(false) }
  }

  const handleDeactivate = async (id) => {
    if (!confirm('Deactivate this user? They will no longer be able to log in.')) return
    try { await usersApi.delete(id); load() }
    catch (e) { setError(apiError(e)) }
  }

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div>
      <PageHeader
        title={lang === 'ru' ? 'Пользователи' : 'Users'}
        subtitle={lang === 'ru' ? 'Управление членами семьи' : 'Manage family members'}
        action={<Button onClick={openCreate}>{lang === 'ru' ? '+ Новый пользователь' : '+ New User'}</Button>}
      />

      {error && <Alert type="error">{error}</Alert>}

      {loading ? (
        <div className={styles.center}><Spinner size={28} /></div>
      ) : users.length === 0 ? (
        <EmptyState icon="👤" title="No users found" />
      ) : (
        <div className={styles.grid}>
          {users.map(u => (
            <Card key={u.id} className={styles.userCard}>
              <div className={styles.avatar}>{u.name[0].toUpperCase()}</div>
              <div className={styles.info}>
                <span className={styles.name}>{u.name}</span>
                <span className={styles.email}>{u.email}</span>
                <span className={styles.since}>Since {formatDate(u.created_at)}</span>
              </div>
              <div className={`${styles.status} ${u.is_active ? styles.active : styles.inactive}`}>
                {u.is_active ? 'Active' : 'Inactive'}
              </div>
              <div className={styles.actions}>
                <Button size="sm" variant="secondary" onClick={() => openEdit(u)}>Edit</Button>
                {u.is_active && (
                  <Button size="sm" variant="danger" onClick={() => handleDeactivate(u.id)}>
                    Deactivate
                  </Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => setModal(false)}
        title={editing ? 'Edit User' : 'New User'}
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setModal(false)}>Cancel</Button>
            <Button type="submit" form="user-form" loading={saving}>Save</Button>
          </>
        }
      >
        <form id="user-form" onSubmit={handleSubmit} className={styles.form}>
          {error && <Alert type="error">{error}</Alert>}
          <div className={styles.field}>
            <label>Name *</label>
            <input required value={form.name} onChange={e => set('name', e.target.value)} placeholder="Full name" />
          </div>
          <div className={styles.field}>
            <label>Email *</label>
            <input required type="email" value={form.email} onChange={e => set('email', e.target.value)} placeholder="email@family.local" />
          </div>
          <div className={styles.field}>
            <label>{editing ? 'New Password (leave blank to keep)' : 'Password *'}</label>
            <input
              type="password"
              value={form.password}
              onChange={e => set('password', e.target.value)}
              required={!editing}
              minLength={6}
              placeholder={editing ? '••••••' : 'Minimum 6 characters'}
            />
          </div>
        </form>
      </Modal>
    </div>
  )
}
