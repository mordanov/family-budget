import React from 'react'
import { Link } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useI18n } from '../i18n'
import styles from './NotFound.module.css'

export default function NotFoundPage() {
  const { token } = useAuthStore()
  const { t } = useI18n()

  return (
    <div className={styles.wrap}>
      <div className={styles.card}>
        <div className={styles.code}>404</div>
        <h1 className={styles.title}>{t('notFoundTitle')}</h1>
        <p className={styles.text}>{t('notFoundText')}</p>
        <Link className={styles.link} to={token ? '/operations' : '/login'}>
          {token ? t('goOperations') : t('goLogin')}
        </Link>
      </div>
    </div>
  )
}

