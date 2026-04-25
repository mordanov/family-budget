import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { Button, Alert } from '../components/ui/index'
import { useI18n } from '../i18n'
import styles from './Login.module.css'

export default function LoginPage() {
  const [loginValue, setLoginValue] = useState('')
  const [password, setPassword] = useState('')
  const [rememberMe, setRememberMe] = useState(
    () => localStorage.getItem('remember_me') === 'true'
  )
  const { t } = useI18n()
  const { login, loading, error, clearError } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    clearError()
    localStorage.setItem('remember_me', String(rememberMe))
    try {
      await login(loginValue, password, rememberMe)
      navigate('/operations')
    } catch {}
  }

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.logo}>💰</div>
        <h1 className={styles.title}>{t('appName')}</h1>
        <p className={styles.subtitle}>{t('signInSubtitle')}</p>

        {error && <Alert type="error">{error}</Alert>}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label>{t('loginLabel')}</label>
            <input
              type="text"
              placeholder={t('loginPlaceholder')}
              value={loginValue}
              onChange={(e) => setLoginValue(e.target.value)}
              autoComplete="username"
              inputMode="email"
              autoCapitalize="none"
              spellCheck={false}
              required
              autoFocus
            />
          </div>
          <div className={styles.field}>
            <label>{t('password')}</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              enterKeyHint="go"
              required
            />
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '13px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
            />
            {t('rememberMe')}
          </label>
          <Button type="submit" size="lg" loading={loading} className={styles.submitBtn}>
            {t('signIn')}
          </Button>
        </form>

        <p className={styles.hint}>
          {t('defaultUsersHint')}: <code>user1@family.local</code> / <code>password1</code>
        </p>
      </div>
    </div>
  )
}
