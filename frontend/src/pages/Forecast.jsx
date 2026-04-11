import React, { useEffect, useMemo, useState } from 'react'
import { reportsApi } from '../api/index'
import { Card, PageHeader, Spinner, EmptyState, Alert } from '../components/ui/index'
import { useI18n } from '../i18n'
import { formatCurrency, currentMonthRange, monthName, apiError } from '../utils/index'
import { useTimezone } from '../hooks/index'
import { toZonedTime } from 'date-fns-tz'
import styles from './Forecast.module.css'

function TrendBadge({ slope, t }) {
  if (slope > 5) return <span className={`${styles.trendBadge} ${styles.trendUp}`}>📈 {t('trendUp')}</span>
  if (slope < -5) return <span className={`${styles.trendBadge} ${styles.trendDown}`}>📉 {t('trendDown')}</span>
  return <span className={`${styles.trendBadge} ${styles.trendFlat}`}>➡️ {t('trendFlat')}</span>
}

export default function ForecastPage() {
  const { lang, t } = useI18n()
  const timezone = useTimezone()
  const [data, setData] = useState(null)
  const [daily, setDaily] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const dayOfMonth = useMemo(() => toZonedTime(new Date(), timezone).getDate(), [timezone])
  const range = useMemo(() => currentMonthRange(timezone), [timezone])

  useEffect(() => {
    setLoading(true)
    setError(null)
    Promise.all([
      reportsApi.forecastDetailed({ days_elapsed: dayOfMonth }),
      reportsApi.dailyBalance(range),
    ])
      .then(([f, d]) => {
        setData(f)
        setDaily(d.items || [])
      })
      .catch((e) => setError(apiError(e)))
      .finally(() => setLoading(false))
  }, [dayOfMonth, range])

  // Today's running balance from the daily series
  const todayBalance = daily.length > 0 ? Number(daily[daily.length - 1].balance) : null

  const projectedBalance = todayBalance !== null && data
    ? todayBalance - (Number(data.current_month_expense_projected) - Number(data.current_month_expense_actual))
    : null

  // Next month name
  const now = new Date()
  const nextMonthDate = new Date(now.getFullYear(), now.getMonth() + 1, 1)
  const nextMonthLabel = `${monthName(nextMonthDate.getMonth() + 1, lang)} ${nextMonthDate.getFullYear()}`
  const currentMonthLabel = `${monthName(now.getMonth() + 1, lang)} ${now.getFullYear()}`

  return (
    <div>
      <PageHeader title={t('forecastTitle')} subtitle={t('forecastSubtitle')} />

      {error && <Alert type="error">{error}</Alert>}

      {loading ? (
        <div className={styles.center}><Spinner size={32} /></div>
      ) : data ? (
        <>
          {/* Current month KPI row */}
          <h3 className={styles.sectionHeading}>
            {t('currentMonthProjection')} — {currentMonthLabel}
          </h3>
          <div className={styles.kpiGrid}>
            <Card className={styles.kpiCard}>
              <span className={styles.kpiLabel}>{t('daysElapsed')}</span>
              <span className={styles.kpiValue} style={{ color: 'var(--color-primary)' }}>
                {data.days_elapsed} / {data.days_in_month}
              </span>
              <div className={styles.progressBar}>
                <div
                  className={styles.progressFill}
                  style={{ width: `${(data.days_elapsed / data.days_in_month) * 100}%` }}
                />
              </div>
            </Card>
            <Card className={styles.kpiCard}>
              <span className={styles.kpiLabel}>{t('actualExpense')}</span>
              <span className={styles.kpiValue} style={{ color: 'var(--color-expense)' }}>
                {formatCurrency(data.current_month_expense_actual)}
              </span>
            </Card>
            <Card className={styles.kpiCard}>
              <span className={styles.kpiLabel}>{t('projectedExpense')}</span>
              <span className={styles.kpiValue} style={{ color: 'var(--color-expense)' }}>
                {formatCurrency(data.current_month_expense_projected)}
              </span>
            </Card>
            {projectedBalance !== null && (
              <Card className={styles.kpiCard}>
                <span className={styles.kpiLabel}>{t('projectedBalance')}</span>
                <span
                  className={styles.kpiValue}
                  style={{ color: projectedBalance >= 0 ? 'var(--color-income)' : 'var(--color-expense)' }}
                >
                  {formatCurrency(projectedBalance)}
                </span>
              </Card>
            )}
          </div>

          {/* Category forecast table */}
          <h3 className={styles.sectionHeading}>{t('forecastByCategory')}</h3>
          <Card>
            {data.categories.length === 0 ? (
              <EmptyState icon="🔮" title={t('noForecastData')} />
            ) : (
              <table className={styles.forecastTable}>
                <thead>
                  <tr>
                    <th>{t('category')}</th>
                    <th className={styles.numCol}>{t('currentMonthActual')}</th>
                    <th className={styles.numCol}>{t('currentMonthProjected')}</th>
                    <th className={styles.numCol}>{t('nextMonth')}</th>
                    <th className={styles.trendCol}>{t('trend')}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.categories.map((cat) => (
                    <tr key={cat.category_id}>
                      <td className={styles.catCell}>
                        {cat.category_icon && (
                          <span className={styles.catIcon}>{cat.category_icon}</span>
                        )}
                        {!cat.category_icon && (
                          <span
                            className={styles.catDot}
                            style={{ background: cat.category_color || '#9E9E9E' }}
                          />
                        )}
                        <span>{cat.category_name}</span>
                      </td>
                      <td className={`${styles.numCol} amount-expense`}>
                        {Number(cat.current_month_actual) > 0
                          ? `-${formatCurrency(cat.current_month_actual)}`
                          : '—'}
                      </td>
                      <td className={`${styles.numCol} amount-expense`}>
                        {Number(cat.current_month_projected) > 0
                          ? `-${formatCurrency(cat.current_month_projected)}`
                          : '—'}
                      </td>
                      <td className={`${styles.numCol} amount-expense`}>
                        {Number(cat.next_month_projected) > 0
                          ? `-${formatCurrency(cat.next_month_projected)}`
                          : '—'}
                      </td>
                      <td className={styles.trendCol}>
                        <TrendBadge slope={cat.trend_slope} t={t} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>

          {/* Next month KPI row */}
          <h3 className={styles.sectionHeading}>
            {t('nextMonthProjection')} — {nextMonthLabel}
          </h3>
          <div className={styles.kpiGridSmall}>
            <Card className={styles.kpiCard}>
              <span className={styles.kpiLabel}>{t('estExpense')}</span>
              <span className={styles.kpiValue} style={{ color: 'var(--color-expense)' }}>
                {formatCurrency(data.next_month_projected_expense)}
              </span>
            </Card>
            <Card className={styles.kpiCard}>
              <span className={styles.kpiLabel}>{t('estNet')}</span>
              <span
                className={styles.kpiValue}
                style={{
                  color: Number(data.next_month_projected_income) - Number(data.next_month_projected_expense) >= 0
                    ? 'var(--color-income)' : 'var(--color-expense)',
                }}
              >
                {formatCurrency(
                  Number(data.next_month_projected_income) - Number(data.next_month_projected_expense)
                )}
              </span>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  )
}
