import React, { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button, Card, PageHeader, Alert } from '../components/ui/index'
import { useI18n } from '../i18n'
import { useAuthStore } from '../store/authStore'
import { usersApi } from '../api/index'
import { apiError } from '../utils/index'
import CategoriesPage from './Categories'
import UsersPage from './Users'
import PaymentMethodsPage from './PaymentMethods'
import styles from './Settings.module.css'

const TABS = ['profile', 'categories', 'users', 'payment-methods']

// Common IANA timezones for the picker
const TIMEZONES = [
  'UTC',
  'Europe/London',
  'Europe/Berlin',
  'Europe/Paris',
  'Europe/Madrid',
  'Europe/Rome',
  'Europe/Warsaw',
  'Europe/Kiev',
  'Europe/Moscow',
  'Europe/Istanbul',
  'Asia/Dubai',
  'Asia/Kolkata',
  'Asia/Bangkok',
  'Asia/Singapore',
  'Asia/Tokyo',
  'Asia/Seoul',
  'Asia/Shanghai',
  'Australia/Sydney',
  'Pacific/Auckland',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Anchorage',
  'America/Sao_Paulo',
  'America/Argentina/Buenos_Aires',
]

function ProfileTab() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)
  const updateUser = useAuthStore((s) => s.updateUser)
  const [timezone, setTimezone] = useState(user?.timezone || 'UTC')
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)

  const handleSave = async () => {
    setSaving(true)
    setSuccess(false)
    setError(null)
    try {
      const updated = await usersApi.updateMe(user.id, { timezone })
      updateUser(updated)
      setSuccess(true)
    } catch (e) {
      setError(apiError(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card style={{ maxWidth: 480 }}>
      {success && <Alert type="success">{t('timezoneSaved')}</Alert>}
      {error && <Alert type="error">{error}</Alert>}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <label>
          <strong>{t('timezoneLabel')}</strong>
          <select
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            style={{ display: 'block', width: '100%', marginTop: '0.25rem' }}
          >
            {TIMEZONES.map((tz) => (
              <option key={tz} value={tz}>{tz}</option>
            ))}
          </select>
        </label>
        <Button onClick={handleSave} loading={saving}>{t('save')}</Button>
      </div>
    </Card>
  )
}

export default function SettingsPage() {
  const { t } = useI18n()
  const [searchParams, setSearchParams] = useSearchParams()
  const initial = TABS.includes(searchParams.get('tab')) ? searchParams.get('tab') : 'profile'
  const [active, setActive] = useState(initial)

  return (
    <div>
      <PageHeader title={t('settingsTitle')} subtitle={t('settingsSubtitle')} />

      <Card className={styles.tabsCard}>
        <div className={styles.tabs}>
          {TABS.map((key) => (
            <Button
              key={key}
              variant={active === key ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => {
                setActive(key)
                setSearchParams({ tab: key })
              }}
            >
              {key === 'profile' && t('settingsProfileTitle')}
              {key === 'categories' && t('settingsCategoriesTitle')}
              {key === 'users' && t('settingsUsersTitle')}
              {key === 'payment-methods' && t('settingsPaymentMethodsTitle')}
            </Button>
          ))}
        </div>
      </Card>

      <div className={styles.content}>
        {active === 'profile' && <ProfileTab />}
        {active === 'categories' && <CategoriesPage />}
        {active === 'users' && <UsersPage />}
        {active === 'payment-methods' && <PaymentMethodsPage />}
      </div>
    </div>
  )
}
