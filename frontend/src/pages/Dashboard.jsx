import React, { useEffect, useState } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  LineElement, PointElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'
import { balancesApi, reportsApi } from '../api/index'
import { Card, Spinner, PageHeader, EmptyState } from '../components/ui/index'
import { useI18n } from '../i18n'
import { formatCurrency, prevMonthRange, monthName } from '../utils/index'
import styles from './Dashboard.module.css'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend, Filler)

const CHART_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { labels: { color: '#7b82a0', font: { family: 'DM Sans' } } } },
  scales: {
    x: { ticks: { color: '#7b82a0' }, grid: { color: 'rgba(46,50,80,0.5)' } },
    y: { ticks: { color: '#7b82a0' }, grid: { color: 'rgba(46,50,80,0.5)' } },
  },
}

export default function DashboardPage() {
  const { lang } = useI18n()
  const [balances, setBalances] = useState([])
  const [report, setReport] = useState(null)
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const range = prevMonthRange()
    Promise.all([
      balancesApi.list(),
      reportsApi.get(range),
      reportsApi.forecast(),
    ]).then(([b, r, f]) => {
      setBalances(b.slice(0, 6))
      setReport(r)
      setForecast(f)
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className={styles.loading}><Spinner size={32} /></div>
  )

  const latest = balances[0]

  const trendLabels = (report?.monthly_trend || []).map(
    (t) => `${monthName(t.month).slice(0, 3)} ${t.year}`
  )
  const trendData = {
    labels: trendLabels,
    datasets: [
      {
        label: 'Income',
        data: (report?.monthly_trend || []).map((t) => Number(t.total_income)),
        backgroundColor: 'rgba(62,207,142,0.7)',
        borderRadius: 6,
      },
      {
        label: 'Expense',
        data: (report?.monthly_trend || []).map((t) => Number(t.total_expense)),
        backgroundColor: 'rgba(245,99,58,0.7)',
        borderRadius: 6,
      },
    ],
  }

  const balanceChartData = {
    labels: [...balances].reverse().map((b) => `${monthName(b.month).slice(0, 3)} ${b.year}`),
    datasets: [{
      label: 'Closing Balance',
      data: [...balances].reverse().map((b) => Number(b.closing_balance)),
      borderColor: '#6c8fff',
      backgroundColor: 'rgba(108,143,255,0.1)',
      fill: true,
      tension: 0.4,
      pointBackgroundColor: '#6c8fff',
    }],
  }

  return (
    <div>
      <PageHeader title={lang === 'ru' ? 'Дашборд' : 'Dashboard'} subtitle={lang === 'ru' ? 'Обзор семейных финансов' : 'Overview of your family finances'} />

      {/* KPI row */}
      <div className={styles.kpiGrid}>
        <KpiCard label="Current Balance" value={formatCurrency(latest?.closing_balance || 0)} accent="primary" />
        <KpiCard label="Last Month Income" value={formatCurrency(report?.total_income || 0)} accent="income" />
        <KpiCard label="Last Month Expense" value={formatCurrency(report?.total_expense || 0)} accent="expense" />
        <KpiCard label="Net Last Month" value={formatCurrency(report?.net_balance || 0)}
          accent={Number(report?.net_balance || 0) >= 0 ? 'income' : 'expense'} />
      </div>

      {/* Charts row */}
      <div className={styles.chartsRow}>
        <Card className={styles.chartCard}>
          <h3 className={styles.chartTitle}>Income vs Expense Trend</h3>
          {trendLabels.length > 0
            ? <div className={styles.chartWrap}><Bar data={trendData} options={CHART_OPTS} /></div>
            : <EmptyState icon="📊" title="No trend data yet" />
          }
        </Card>
        <Card className={styles.chartCard}>
          <h3 className={styles.chartTitle}>Balance Over Time</h3>
          {balances.length > 0
            ? <div className={styles.chartWrap}><Line data={balanceChartData} options={CHART_OPTS} /></div>
            : <EmptyState icon="📈" title="No balance history yet" />
          }
        </Card>
      </div>

      {/* Forecast + Category breakdown */}
      <div className={styles.bottomRow}>
        {forecast && (
          <Card>
            <h3 className={styles.chartTitle}>
              Next Month Forecast — {monthName(forecast.month)} {forecast.year}
            </h3>
            <div className={styles.forecastSummary}>
              <span className={styles.forecastIncome}>
                +{formatCurrency(forecast.total_estimated_income)}
              </span>
              <span className={styles.forecastExpense}>
                -{formatCurrency(forecast.total_estimated_expense)}
              </span>
              <span className={`${styles.forecastNet} ${Number(forecast.estimated_net) >= 0 ? styles.pos : styles.neg}`}>
                Net: {formatCurrency(forecast.estimated_net)}
              </span>
            </div>
            <div className={styles.forecastList}>
              {forecast.items.slice(0, 8).map((item, i) => (
                <div key={i} className={styles.forecastItem}>
                  <span className={styles.forecastCat}>{item.category_name}</span>
                  <span className={styles.forecastSource}>{item.source}</span>
                  <span className={item.type === 'income' ? 'amount-income' : 'amount-expense'}>
                    {item.type === 'income' ? '+' : '-'}{formatCurrency(item.estimated_amount)}
                  </span>
                </div>
              ))}
            </div>
          </Card>
        )}

        {report && (
          <Card>
            <h3 className={styles.chartTitle}>Last Month by Category</h3>
            <div className={styles.catList}>
              {(report.by_category || []).slice(0, 8).map((cat) => (
                <div key={cat.category_id} className={styles.catRow}>
                  <span
                    className={styles.catDot}
                    style={{ background: cat.category_color || '#9E9E9E' }}
                  />
                  <span className={styles.catName}>{cat.category_name}</span>
                  <span className="amount-expense">-{formatCurrency(cat.total_expense)}</span>
                  <span className="amount-income">+{formatCurrency(cat.total_income)}</span>
                </div>
              ))}
              {!report.by_category?.length && (
                <EmptyState icon="🏷" title="No category data" />
              )}
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}

function KpiCard({ label, value, accent }) {
  const accentMap = {
    primary: 'var(--color-primary)',
    income: 'var(--color-income)',
    expense: 'var(--color-expense)',
  }
  return (
    <Card className={styles.kpiCard}>
      <span className={styles.kpiLabel}>{label}</span>
      <span className={styles.kpiValue} style={{ color: accentMap[accent] }}>{value}</span>
    </Card>
  )
}
