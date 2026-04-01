import React from 'react'
import styles from './ui.module.css'
import { useI18n } from '../../i18n'

export function Button({
  children, variant = 'primary', size = 'md',
  loading = false, disabled = false, onClick, type = 'button', className = '',
  ...rest
}) {
  return (
    <button
      type={type}
      className={`${styles.btn} ${styles[`btn_${variant}`]} ${styles[`btn_${size}`]} ${className}`}
      onClick={onClick}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <Spinner size={14} />}
      {children}
    </button>
  )
}

export function Spinner({ size = 20 }) {
  return (
    <span
      className={styles.spinner}
      style={{ width: size, height: size, borderWidth: size > 16 ? 2 : 1.5 }}
    />
  )
}

export function Card({ children, className = '', style }) {
  return <div className={`${styles.card} ${className}`} style={style}>{children}</div>
}

export function Badge({ type }) {
  const { lang } = useI18n()
  const incomeLabel = lang === 'ru' ? 'Доход' : 'Income'
  const expenseLabel = lang === 'ru' ? 'Расход' : 'Expense'
  return (
    <span className={`badge ${type === 'income' ? 'badge-income' : 'badge-expense'}`}>
      {type === 'income' ? `▲ ${incomeLabel}` : `▼ ${expenseLabel}`}
    </span>
  )
}

export function EmptyState({ icon = '📭', title, description }) {
  return (
    <div className={styles.empty}>
      <span className={styles.emptyIcon}>{icon}</span>
      <p className={styles.emptyTitle}>{title}</p>
      {description && <p className={styles.emptyDesc}>{description}</p>}
    </div>
  )
}

export function Alert({ type = 'error', children }) {
  return <div className={`${styles.alert} ${styles[`alert_${type}`]}`}>{children}</div>
}

export function PageHeader({ title, subtitle, action }) {
  return (
    <div className={styles.pageHeader}>
      <div>
        <h1 className={styles.pageTitle}>{title}</h1>
        {subtitle && <p className={styles.pageSubtitle}>{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}
