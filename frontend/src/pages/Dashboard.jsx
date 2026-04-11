import React, { useEffect, useMemo, useState } from 'react'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  LineElement, PointElement, ArcElement, Title, Tooltip, Legend, Filler,
} from 'chart.js'
import { Bar, Line, Doughnut } from 'react-chartjs-2'
import { balancesApi, reportsApi, operationsApi } from '../api/index'
import { Card, Spinner, PageHeader, EmptyState } from '../components/ui/index'
import Modal from '../components/ui/Modal'
import { useI18n } from '../i18n'
import { toZonedTime } from 'date-fns-tz'
import { formatCurrency, formatDate, currentMonthRange, monthName } from '../utils/index'
import { useTimezone } from '../hooks/index'
import styles from './Dashboard.module.css'

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, ArcElement, Title, Tooltip, Legend, Filler)

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
  const { lang, t } = useI18n()
  const timezone = useTimezone()
  const [balances, setBalances] = useState([])
  const [report, setReport] = useState(null)
  const [daily, setDaily] = useState([])
  const [loading, setLoading] = useState(true)

  const range = useMemo(() => currentMonthRange(timezone), [timezone])

  useEffect(() => {
    Promise.all([
      balancesApi.list(),
      reportsApi.get(range),
      reportsApi.dailyBalance(range),
    ]).then(([b, r, d]) => {
      setBalances(b.slice(0, 6))
      setReport(r)
      setDaily(d.items || [])
    }).finally(() => setLoading(false))
  }, [timezone])

  if (loading) return (
    <div className={styles.loading}><Spinner size={32} /></div>
  )

  const latest = balances[0]

  const trendLabels = (report?.monthly_trend || []).map(
    (tItem) => `${monthName(tItem.month, lang).slice(0, 3)} ${tItem.year}`
  )
  const trendData = {
    labels: trendLabels,
    datasets: [
      {
        label: t('income'),
        data: (report?.monthly_trend || []).map((t) => Number(t.total_income)),
        backgroundColor: 'rgba(62,207,142,0.7)',
        borderRadius: 6,
      },
      {
        label: t('expense'),
        data: (report?.monthly_trend || []).map((t) => Number(t.total_expense)),
        backgroundColor: 'rgba(245,99,58,0.7)',
        borderRadius: 6,
      },
    ],
  }

  const balanceChartData = {
    labels: daily.map((d) => d.date.slice(5)),
    datasets: [{
      label: t('closingBalance'),
      data: daily.map((d) => Number(d.balance)),
      borderColor: '#6c8fff',
      backgroundColor: 'rgba(108,143,255,0.1)',
      fill: true,
      tension: 0.4,
      pointBackgroundColor: '#6c8fff',
    }],
  }

  const dayOfMonth = toZonedTime(new Date(), timezone).getDate()
  const avgDailyExpense = Number(report?.total_expense || 0) / dayOfMonth

  return (
    <div>
      <PageHeader title={t('dashboardTitle')} subtitle={t('dashboardSubtitle')} />

      {/* KPI row */}
      <div className={styles.kpiGrid}>
        <KpiCard label={t('currentBalance')} value={formatCurrency(latest?.closing_balance || 0)} accent="primary" />
        <KpiCard label={t('monthIncome')} value={formatCurrency(report?.total_income || 0)} accent="income" />
        <KpiCard label={t('monthExpense')} value={formatCurrency(report?.total_expense || 0)} accent="expense" />
        <KpiCard label={t('avgDailyExpense')} value={formatCurrency(avgDailyExpense)} accent="expense" />
      </div>

      {/* Charts row */}
      <div className={styles.chartsRow}>
        <Card className={styles.chartCard}>
          <h3 className={styles.chartTitle}>{t('incomeVsExpenseTrend')}</h3>
          {trendLabels.length > 0
            ? <div className={styles.chartWrap}><Bar data={trendData} options={CHART_OPTS} /></div>
            : <EmptyState icon="📊" title={t('noTrendDataYet')} />
          }
        </Card>
        <Card className={styles.chartCard}>
          <h3 className={styles.chartTitle}>{t('balanceOverTime')}</h3>
          {daily.length > 0
            ? <div className={styles.chartWrap}><Line data={balanceChartData} options={CHART_OPTS} /></div>
            : <EmptyState icon="📈" title={t('noBalanceHistoryYet')} />
          }
        </Card>
      </div>

      {/* Bottom row: expense by category + by payment method */}
      <div className={styles.bottomRow}>
        {report && <ExpenseByCategoryCard report={report} t={t} range={range} />}
        {report && <PaymentMethodCard report={report} t={t} />}
      </div>
    </div>
  )
}

const COLORS = [
  '#6c8fff','#3ecf8e','#f5633a','#f5a623','#a78bfa',
  '#38bdf8','#fb7185','#34d399','#fbbf24','#60a5fa',
]

const DONUT_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'right', labels: { color: '#7b82a0', font: { family: 'DM Sans', size: 12 }, boxWidth: 12, padding: 10 } },
    tooltip: {
      callbacks: {
        label: (ctx) => ` ${ctx.label}: ${new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(ctx.parsed)}`,
      },
    },
  },
  cutout: '65%',
}

function ExpenseByCategoryCard({ report, t, range }) {
  const timezone = useTimezone()
  const [catModal, setCatModal] = useState(null)
  const [catOps, setCatOps] = useState([])
  const [catOpsLoading, setCatOpsLoading] = useState(false)

  const expCats = (report.by_category || [])
    .filter((c) => Number(c.total_expense) > 0)
    .sort((a, b) => Number(b.total_expense) - Number(a.total_expense))

  const donutData = {
    labels: expCats.map((c) => c.category_name),
    datasets: [{
      data: expCats.map((c) => Number(c.total_expense)),
      backgroundColor: expCats.map((c, i) => c.category_color || COLORS[i % COLORS.length]),
      borderWidth: 0,
    }],
  }

  const handleCatClick = async (cat) => {
    setCatModal(cat)
    setCatOpsLoading(true)
    setCatOps([])
    try {
      const result = await operationsApi.list({
        category_id: cat.category_id,
        date_from: range.date_from,
        date_to: range.date_to,
        size: 100,
      })
      setCatOps(result.items || [])
    } finally {
      setCatOpsLoading(false)
    }
  }

  return (
    <Card className={styles.expCatCard}>
      <h3 className={styles.chartTitle}>{t('currentMonthByCategory')}</h3>
      {expCats.length === 0 ? (
        <EmptyState icon="🏷" title={t('noCategoryData')} />
      ) : (
        <div className={styles.expCatBody}>
          <div className={styles.expCatDonut}>
            <Doughnut data={donutData} options={DONUT_OPTS} />
          </div>
          <div className={styles.expCatList}>
            {expCats.map((cat) => (
              <div
                key={cat.category_id}
                className={styles.expCatRow}
                onClick={() => handleCatClick(cat)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && handleCatClick(cat)}
              >
                <span className={styles.catIcon}>{cat.category_icon || '🏷'}</span>
                <span className={styles.catName}>{cat.category_name}</span>
                <span className="amount-expense">-{formatCurrency(cat.total_expense)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <Modal
        open={!!catModal}
        onClose={() => setCatModal(null)}
        title={`${catModal?.category_icon || '🏷'} ${catModal?.category_name || ''}`}
        size="lg"
      >
        {catOpsLoading ? (
          <div className={styles.catOpsLoading}><Spinner size={24} /></div>
        ) : catOps.length === 0 ? (
          <EmptyState icon="📭" title={t('noOperations')} />
        ) : (
          <table className={styles.catOpsTable}>
            <thead>
              <tr>
                <th>{t('tableDate')}</th>
                <th>{t('tableDescription')}</th>
                <th>{t('tableUser')}</th>
                <th className={styles.catOpsAmount}>{t('tableAmount')}</th>
              </tr>
            </thead>
            <tbody>
              {catOps.map((op) => (
                <tr key={op.id}>
                  <td className={styles.catOpsDate}>{formatDate(op.operation_date, timezone)}</td>
                  <td>{op.description || '—'}</td>
                  <td>{op.user?.name || '—'}</td>
                  <td className={`${styles.catOpsAmount} ${op.type === 'expense' ? 'amount-expense' : 'amount-income'}`}>
                    {op.type === 'expense' ? '-' : '+'}{formatCurrency(op.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Modal>
    </Card>
  )
}

function PaymentMethodCard({ report, t }) {
  const rows = (report.by_payment_type || [])
    .filter((p) => Number(p.total_income) > 0 || Number(p.total_expense) > 0)
    .sort((a, b) => Number(b.total_expense) - Number(a.total_expense))

  return (
    <Card>
      <h3 className={styles.chartTitle}>{t('byPaymentType')}</h3>
      {rows.length === 0 ? (
        <EmptyState icon="💳" title={t('noData')} />
      ) : (
        <table className={styles.pmTable}>
          <thead>
            <tr>
              <th>{t('payment')}</th>
              <th className={styles.pmNum}>{t('income')}</th>
              <th className={styles.pmNum}>{t('expense')}</th>
              <th className={styles.pmNum}>{t('count')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.payment_type}>
                <td>{p.payment_method_name}</td>
                <td className={`${styles.pmNum} amount-income`}>
                  {Number(p.total_income) > 0 ? `+${formatCurrency(p.total_income)}` : '—'}
                </td>
                <td className={`${styles.pmNum} amount-expense`}>
                  {Number(p.total_expense) > 0 ? `-${formatCurrency(p.total_expense)}` : '—'}
                </td>
                <td className={`${styles.pmNum} ${styles.pmCount}`}>{p.count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
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
