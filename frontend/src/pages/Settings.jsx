import React, { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button, Card, PageHeader } from '../components/ui/index'
import { useI18n } from '../i18n'
import CategoriesPage from './Categories'
import UsersPage from './Users'
import PaymentMethodsPage from './PaymentMethods'
import styles from './Settings.module.css'

const TABS = ['categories', 'users', 'payment-methods']

export default function SettingsPage() {
  const { t } = useI18n()
  const [searchParams, setSearchParams] = useSearchParams()
  const initial = TABS.includes(searchParams.get('tab')) ? searchParams.get('tab') : 'categories'
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
              {key === 'categories' && t('settingsCategoriesTitle')}
              {key === 'users' && t('settingsUsersTitle')}
              {key === 'payment-methods' && t('settingsPaymentMethodsTitle')}
            </Button>
          ))}
        </div>
      </Card>

      <div className={styles.content}>
        {active === 'categories' && <CategoriesPage />}
        {active === 'users' && <UsersPage />}
        {active === 'payment-methods' && <PaymentMethodsPage />}
      </div>
    </div>
  )
}



