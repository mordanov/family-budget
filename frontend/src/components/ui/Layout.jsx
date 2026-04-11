import React, { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import { useI18n } from '../../i18n'
import styles from './Layout.module.css'

const NAV = [
  { to: '/operations', icon: '↕', labelKey: 'navOperations' },
  { to: '/dashboard', icon: '⬛', labelKey: 'navDashboard' },
  { to: '/reports', icon: '📊', labelKey: 'navReports' },
  { to: '/forecast', icon: '🔮', labelKey: 'navForecast' },
  { to: '/balances', icon: '⚖', labelKey: 'navBalances' },
  { to: '/settings', icon: '⚙', labelKey: 'navSettings' },
]

export default function AppLayout() {
  const { user, logout } = useAuthStore()
  const { lang, switchLanguage, t } = useI18n()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <div className={`${styles.layout} ${collapsed ? styles.collapsed : ''}`}>
      <aside className={styles.sidebar}>
        <div className={styles.logo}>
          <span className={styles.logoIcon}>💰</span>
          {!collapsed && <span className={styles.logoText}>{t('appName')}</span>}
        </div>

        <nav className={styles.nav}>
          {NAV.map(({ to, icon, labelKey }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.navActive : ''}`
              }
            >
              <span className={styles.navIcon}>{icon}</span>
              {!collapsed && <span>{t(labelKey)}</span>}
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          {!collapsed && (
            <div className={styles.userInfo}>
              <div className={styles.userAvatar}>
                {user?.name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div className={styles.userDetails}>
                <span className={styles.userName}>{user?.name}</span>
                <span className={styles.userEmail}>{user?.email}</span>
              </div>
            </div>
          )}
          {!collapsed && (
            <div className={styles.langSwitch}>
              <button
                className={`${styles.langBtn} ${lang === 'en' ? styles.langBtnActive : ''}`}
                onClick={() => switchLanguage('en')}
                type="button"
                aria-label="Switch language to English"
              >
                EN
              </button>
              <button
                className={`${styles.langBtn} ${lang === 'ru' ? styles.langBtnActive : ''}`}
                onClick={() => switchLanguage('ru')}
                type="button"
                aria-label="Переключить язык на русский"
              >
                RU
              </button>
            </div>
          )}
          <button
            className={styles.logoutBtn}
            onClick={handleLogout}
            title={t('logout')}
            aria-label={t('logout')}
            type="button"
          >
            ⇥
          </button>
        </div>

        <button
          className={styles.collapseBtn}
          onClick={() => setCollapsed((c) => !c)}
          title={collapsed ? t('expand') : t('collapse')}
        >
          {collapsed ? '›' : '‹'}
        </button>
      </aside>

      <main className={styles.main}>
        <div className={styles.content}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
