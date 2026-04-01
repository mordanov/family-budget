import React, { useState, useEffect } from 'react'
import {
  Chart as ChartJS, ArcElement, CategoryScale, LinearScale,
  BarElement, Title, Tooltip, Legend,
} from 'chart.js'
import { Doughnut, Bar } from 'react-chartjs-2'
import { reportsApi } from '../api/index'
import { Card, PageHeader, Spinner, EmptyState, Button, Alert } from '../components/ui/index'
import { useI18n } from '../i18n'
import { formatCurrency, prevMonthRange, monthName, apiError } from '../utils/index'
import { format, parseISO, startOfMonth, endOfMonth, subMonths } from 'date-fns'
import styles from './Reports.module.css'

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const CHART_DEFAULTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: '#7b82a0', font: { family: 'DM Sans', size: 12 } } },
  },
}

const BAR_OPTS = {
  ...CHART_DEFAULTS,
  scales: {
    x: { ticks: { color: '#7b82a0' }, grid: { color: 'rgba(46,50,80,0.5)' } },
    y: { ticks: { color: '#7b82a0' }, grid: { color: 'rgba(46,50,80,0.5)' } },
  },
}

const DONUT_OPTS = { ...CHART_DEFAULTS, cutout: '65%' }

const COLORS = [
  '#6c8fff','#3ecf8e','#f5633a','#f5a623','#a78bfa',
  '#38bdf8','#fb7185','#34d399','#fbbf24','#60a5fa',
]

export default function ReportsPage() {
  const { lang, t } = useI18n()
  const prev = prevMonthRange()
  const [dateFrom, setDateFrom] = useState(prev.date_from.slice(0,10))
  const [dateTo, setDateTo]     = useState(prev.date_to.slice(0,10))
  const [report, setReport]     = useState(null)
  const [forecast, setForecast] = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  const load = async () => {
    setLoading(true); setError(null)
    try {
      const [r, f] = await Promise.all([
        reportsApi.get({
          date_from: new Date(dateFrom).toISOString(),
          date_to:   new Date(dateTo + 'T23:59:59').toISOString(),
        }),
        reportsApi.forecast(),
      ])
      setReport(r); setForecast(f)
    } catch (e) { setError(apiError(e)) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, []) // eslint-disable-line

  const setPreset = (months) => {
    const to   = endOfMonth(subMonths(new Date(), months - 1))
    const from = startOfMonth(subMonths(new Date(), months - 1))
    setDateFrom(format(from, 'yyyy-MM-dd'))
    setDateTo(format(to, 'yyyy-MM-dd'))
  }

  // Chart data
  const expenseByCategory = (report?.by_category || []).filter(c => Number(c.total_expense) > 0)
  const donutData = {
    labels: expenseByCategory.map(c => c.category_name),
    datasets: [{
      data: expenseByCategory.map(c => Number(c.total_expense)),
      backgroundColor: expenseByCategory.map((c, i) => c.category_color || COLORS[i % COLORS.length]),
      borderWidth: 0,
      hoverOffset: 6,
    }],
  }

  const trendLabels = (report?.monthly_trend || []).map(
    t => `${monthName(t.month, lang).slice(0,3)} ${t.year}`
  )
  const trendData = {
    labels: trendLabels,
    datasets: [
      {
        label: t('income'),
        data: (report?.monthly_trend || []).map(t => Number(t.total_income)),
        backgroundColor: 'rgba(62,207,142,0.75)',
        borderRadius: 5,
      },
      {
        label: t('expense'),
        data: (report?.monthly_trend || []).map(t => Number(t.total_expense)),
        backgroundColor: 'rgba(245,99,58,0.75)',
        borderRadius: 5,
      },
    ],
  }

  return (
    <div>
      <PageHeader title={t('reportsTitle')} subtitle={t('reportsSubtitle')} />

      {/* Filter bar */}
      <Card className={styles.filterBar}>
        <div className={styles.presets}>
          {[1, 3, 6, 12].map(m => (
            <Button key={m} size="sm" variant="secondary" onClick={() => setPreset(m)}>
                {m === 1 ? t('lastMonth') : t('lastMonths', { count: m })}
            </Button>
          ))}
        </div>
        <div className={styles.dateRange}>
          <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
          <span className={styles.dateSep}>→</span>
          <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
          <Button onClick={load} loading={loading}>{t('apply')}</Button>
        </div>
      </Card>

      {error && <Alert type="error">{error}</Alert>}

      {loading ? (
        <div className={styles.center}><Spinner size={32} /></div>
      ) : report ? (
        <>
          {/* KPI row */}
          <div className={styles.kpiRow}>
            <Card className={styles.kpi}>
              <span className={styles.kpiLabel}>{t('totalIncome')}</span>
              <span className={styles.kpiVal} style={{color:'var(--color-income)'}}>
                {formatCurrency(report.total_income)}
              </span>
            </Card>
            <Card className={styles.kpi}>
              <span className={styles.kpiLabel}>{t('totalExpense')}</span>
              <span className={styles.kpiVal} style={{color:'var(--color-expense)'}}>
                {formatCurrency(report.total_expense)}
              </span>
            </Card>
            <Card className={styles.kpi}>
              <span className={styles.kpiLabel}>{t('netBalance')}</span>
              <span className={styles.kpiVal} style={{
                color: Number(report.net_balance) >= 0
                  ? 'var(--color-income)' : 'var(--color-expense)'
              }}>
                {formatCurrency(report.net_balance)}
              </span>
            </Card>
          </div>

          {/* Charts row */}
          <div className={styles.chartsRow}>
            <Card>
              <h3 className={styles.sectionTitle}>{t('monthlyTrend')}</h3>
              {trendLabels.length > 0
                ? <div className={styles.barWrap}><Bar data={trendData} options={BAR_OPTS} /></div>
                : <EmptyState icon="📊" title={t('noDataForPeriod')} />
              }
            </Card>
            <Card>
              <h3 className={styles.sectionTitle}>{t('expensesByCategory')}</h3>
              {expenseByCategory.length > 0
                ? <div className={styles.donutWrap}><Doughnut data={donutData} options={DONUT_OPTS} /></div>
                : <EmptyState icon="🏷" title={t('noExpenseData')} />
              }
            </Card>
          </div>

          {/* Breakdown tables */}
          <div className={styles.breakdownRow}>
            <BreakdownTable
              title={t('byCategory')}
              rows={report.by_category}
              columns={[t('category'), t('income'), t('expense'), t('count')]}
              renderRow={r => [
                <span key="n" className={styles.catName}>
                  <span className={styles.dot} style={{background: r.category_color || '#9E9E9E'}} />
                  {r.category_name}
                </span>,
                <span key="i" className="amount-income">{formatCurrency(r.total_income)}</span>,
                <span key="e" className="amount-expense">{formatCurrency(r.total_expense)}</span>,
                r.count,
              ]}
            />
            <BreakdownTable
              title={t('byUser')}
              rows={report.by_user}
              columns={[t('user'), t('income'), t('expense'), t('count')]}
              renderRow={r => [
                r.user_name,
                <span key="i" className="amount-income">{formatCurrency(r.total_income)}</span>,
                <span key="e" className="amount-expense">{formatCurrency(r.total_expense)}</span>,
                r.count,
              ]}
            />
            <BreakdownTable
              title={t('byPaymentType')}
              rows={report.by_payment_type}
              columns={[t('payment'), t('income'), t('expense'), t('count')]}
              renderRow={r => [
                <span key="p" className={styles.ptLabel}>{r.payment_method_name || r.payment_type.replace('_',' ')}</span>,
                <span key="i" className="amount-income">{formatCurrency(r.total_income)}</span>,
                <span key="e" className="amount-expense">{formatCurrency(r.total_expense)}</span>,
                r.count,
              ]}
            />
          </div>

          {/* Forecast */}
          {forecast && (
            <Card className={styles.forecastCard}>
              <h3 className={styles.sectionTitle}>
                {t('nextMonthForecast')} — {monthName(forecast.month, lang)} {forecast.year}
              </h3>
              <div className={styles.forecastKpis}>
                <div>
                  <span className={styles.kpiLabel}>{t('estIncome')}</span>
                  <span className="amount-income">{formatCurrency(forecast.total_estimated_income)}</span>
                </div>
                <div>
                  <span className={styles.kpiLabel}>{t('estExpense')}</span>
                  <span className="amount-expense">{formatCurrency(forecast.total_estimated_expense)}</span>
                </div>
                <div>
                  <span className={styles.kpiLabel}>{t('estNet')}</span>
                  <span style={{color: Number(forecast.estimated_net)>=0?'var(--color-income)':'var(--color-expense)'}}>
                    {formatCurrency(forecast.estimated_net)}
                  </span>
                </div>
              </div>
              <table className={styles.forecastTable}>
                <thead>
                  <tr>
                    <th>{t('category')}</th><th>{t('type')}</th><th>{t('source')}</th><th>{t('estimated')}</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.items.map((item, i) => (
                    <tr key={i}>
                      <td>{item.category_name}</td>
                      <td><span className={`badge ${item.type==='income'?'badge-income':'badge-expense'}`}>{item.type === 'income' ? t('income') : t('expense')}</span></td>
                      <td className={styles.source}>{item.source === 'recurring' ? t('sourceRecurring') : t('sourceAverage')}</td>
                      <td className={item.type==='income'?'amount-income':'amount-expense'}>
                        {item.type==='income'?'+':'-'}{formatCurrency(item.estimated_amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}
        </>
      ) : null}
    </div>
  )
}

function BreakdownTable({ title, rows, columns, renderRow }) {
  const { t } = useI18n()
  return (
    <Card>
      <h3 style={{fontSize:'14px',fontWeight:600,marginBottom:'14px'}}>{title}</h3>
      {rows?.length ? (
        <table style={{width:'100%',borderCollapse:'collapse',fontSize:'13px'}}>
          <thead>
            <tr>
              {columns.map(c => (
                <th key={c} style={{textAlign:'left',padding:'6px 8px',color:'var(--color-text-muted)',
                  fontSize:'11px',textTransform:'uppercase',fontWeight:600,letterSpacing:'0.5px',
                  borderBottom:'1px solid var(--color-border)'}}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} style={{borderBottom:'1px solid var(--color-border)'}}>
                {renderRow(r).map((cell, j) => (
                  <td key={j} style={{padding:'8px 8px'}}>{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <EmptyState icon="📋" title={t('noData')} />
      )}
    </Card>
  )
}
