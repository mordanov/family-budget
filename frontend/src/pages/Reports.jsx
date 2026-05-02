import React, { useState, useEffect } from 'react'
import {
  Chart as ChartJS, ArcElement, CategoryScale, LinearScale,
  BarElement, Title, Tooltip, Legend,
} from 'chart.js'
import { Doughnut, Bar } from 'react-chartjs-2'
import { reportsApi, operationsApi } from '../api/index'
import { Card, PageHeader, Spinner, EmptyState, Button, Alert } from '../components/ui/index'
import Modal from '../components/ui/Modal'
import { useI18n } from '../i18n'
import { formatCurrency, formatDateTime, prevMonthRange, monthName, apiError } from '../utils/index'
import { useTimezone } from '../hooks/index'
import { fromZonedTime, toZonedTime } from 'date-fns-tz'
import { format, startOfMonth, endOfMonth, subMonths } from 'date-fns'
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

const makeDonutOpts = (formatFn) => ({
  ...CHART_DEFAULTS,
  cutout: '65%',
  plugins: {
    ...CHART_DEFAULTS.plugins,
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const total = ctx.dataset.data.reduce((a, b) => a + b, 0)
          const pct = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : '0.0'
          return ` ${formatFn(ctx.raw)} (${pct}%)`
        },
      },
    },
  },
})

const COLORS = [
  '#6c8fff','#3ecf8e','#f5633a','#f5a623','#a78bfa',
  '#38bdf8','#fb7185','#34d399','#fbbf24','#60a5fa',
]

export default function ReportsPage() {
  const { lang, t } = useI18n()
  const timezone = useTimezone()
  const prev = prevMonthRange(timezone)
  const [dateFrom, setDateFrom] = useState(prev.date_from.slice(0,10))
  const [dateTo, setDateTo]     = useState(prev.date_to.slice(0,10))
  const [report, setReport]     = useState(null)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)
  const [drilldown, setDrilldown] = useState(null)
  // drilldown = { title, filter: { category_id } | { user_id } | { payment_type } }

  const load = async () => {
    setLoading(true); setError(null)
    try {
      const r = await reportsApi.get({
        date_from: fromZonedTime(new Date(`${dateFrom}T00:00:00`), timezone).toISOString(),
        date_to:   fromZonedTime(new Date(`${dateTo}T23:59:59`), timezone).toISOString(),
      })
      setReport(r)
    } catch (e) { setError(apiError(e)) }
    finally { setLoading(false) }
  }

  useEffect(() => { load() }, []) // eslint-disable-line

  const setPreset = (months) => {
    const nowZoned = toZonedTime(new Date(), timezone)
    const to   = endOfMonth(subMonths(nowZoned, 1))
    const from = startOfMonth(subMonths(nowZoned, months))
    setDateFrom(format(from, 'yyyy-MM-dd'))
    setDateTo(format(to, 'yyyy-MM-dd'))
  }

  // Chart data
  const expenseByCategory = (report?.by_category || []).filter(c => Number(c.total_expense) > 0)
  const totalExpense = expenseByCategory.reduce((sum, c) => sum + Number(c.total_expense), 0)
  const donutData = {
    labels: expenseByCategory.map(c => {
      const pct = totalExpense > 0 ? ((Number(c.total_expense) / totalExpense) * 100).toFixed(1) : '0.0'
      return `${c.category_name} · ${pct}%`
    }),
    datasets: [{
      data: expenseByCategory.map(c => Number(c.total_expense)),
      backgroundColor: expenseByCategory.map((c, i) => c.category_color || COLORS[i % COLORS.length]),
      borderWidth: 0,
      hoverOffset: 6,
    }],
  }
  const donutOpts = makeDonutOpts(formatCurrency)

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
                ? <div className={styles.donutWrap}><Doughnut data={donutData} options={donutOpts} /></div>
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
              onRowClick={r => setDrilldown({ title: r.category_name, filter: { category_id: r.category_id } })}
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
              onRowClick={r => setDrilldown({ title: r.user_name, filter: { user_id: r.user_id } })}
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
              onRowClick={r => setDrilldown({ title: r.payment_method_name || r.payment_type.replace('_', ' '), filter: { payment_type: r.payment_type } })}
              renderRow={r => [
                <span key="p" className={styles.ptLabel}>{r.payment_method_name || r.payment_type.replace('_',' ')}</span>,
                <span key="i" className="amount-income">{formatCurrency(r.total_income)}</span>,
                <span key="e" className="amount-expense">{formatCurrency(r.total_expense)}</span>,
                r.count,
              ]}
            />
          </div>

        </>
      ) : null}

      {drilldown && (
        <DrilldownModal
          open={!!drilldown}
          onClose={() => setDrilldown(null)}
          title={drilldown.title}
          filter={drilldown.filter}
          dateFrom={dateFrom}
          dateTo={dateTo}
          timezone={timezone}
        />
      )}
    </div>
  )
}

function BreakdownTable({ title, rows, columns, renderRow, onRowClick }) {
  const { t } = useI18n()
  const clickable = !!onRowClick
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
              <tr
                key={i}
                onClick={clickable ? () => onRowClick(r) : undefined}
                style={{
                  borderBottom:'1px solid var(--color-border)',
                  cursor: clickable ? 'pointer' : undefined,
                  transition: 'background 0.12s',
                }}
                onMouseEnter={e => { if (clickable) e.currentTarget.style.background = 'var(--color-surface-2)' }}
                onMouseLeave={e => { if (clickable) e.currentTarget.style.background = '' }}
              >
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

const thStyle = {
  textAlign: 'left', padding: '6px 8px',
  color: 'var(--color-text-muted)', fontSize: '11px',
  textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.5px',
  borderBottom: '1px solid var(--color-border)',
}
const tdStyle = { padding: '8px 8px', borderBottom: '1px solid var(--color-border)' }

function DrilldownModal({ open, onClose, title, filter, dateFrom, dateTo, timezone }) {
  const { t } = useI18n()
  const [ops, setOps] = useState({ items: [], total: 0, page: 1, pages: 1 })
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)

  useEffect(() => { setPage(1) }, [filter])

  useEffect(() => {
    if (!open) return
    let cancelled = false
    setLoading(true)
    operationsApi.list({
      ...filter,
      date_from: fromZonedTime(new Date(`${dateFrom}T00:00:00`), timezone).toISOString(),
      date_to:   fromZonedTime(new Date(`${dateTo}T23:59:59`), timezone).toISOString(),
      page,
      size: 15,
    }).then(r => { if (!cancelled) setOps(r) })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [open, filter, dateFrom, dateTo, timezone, page])

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`${title} — ${ops.total} ${t('operationsFor')}`}
      size="lg"
    >
      {loading ? (
        <div style={{display:'flex',justifyContent:'center',padding:32}}><Spinner /></div>
      ) : ops.items.length === 0 ? (
        <EmptyState icon="💸" title={t('noOperations')} />
      ) : (
        <>
          <div style={{overflowX:'auto'}}>
            <table style={{width:'100%',borderCollapse:'collapse',fontSize:'13px'}}>
              <thead>
                <tr>
                  <th style={thStyle}>{t('tableDate')}</th>
                  <th style={thStyle}>{t('tableAmount')}</th>
                  <th style={thStyle}>{t('tableCategory')}</th>
                  <th style={thStyle}>{t('tableUser')}</th>
                  <th style={thStyle}>{t('tablePayment')}</th>
                  <th style={thStyle}>{t('tableDescription')}</th>
                </tr>
              </thead>
              <tbody>
                {ops.items.map(op => (
                  <tr key={op.id}>
                    <td style={tdStyle}>{formatDateTime(op.operation_date, timezone)}</td>
                    <td style={{...tdStyle, fontFamily:'var(--font-mono)',
                      color: op.type === 'income' ? 'var(--color-income)' : 'var(--color-expense)'}}>
                      {op.type === 'income' ? '+' : '-'}{formatCurrency(op.amount)}
                    </td>
                    <td style={tdStyle}>
                      {op.category && (
                        <span style={{display:'flex',alignItems:'center',gap:6}}>
                          <span style={{width:8,height:8,borderRadius:'50%',flexShrink:0,display:'inline-block',
                            background: op.category.color || '#9E9E9E'}} />
                          {op.category.name}
                        </span>
                      )}
                    </td>
                    <td style={tdStyle}>{op.user?.name}</td>
                    <td style={{...tdStyle,color:'var(--color-text-muted)'}}>
                      {op.payment_method?.name || op.payment_type?.replace('_', ' ')}
                    </td>
                    <td style={{...tdStyle,color:'var(--color-text-muted)'}}>{op.description || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {ops.pages > 1 && (
            <div style={{display:'flex',justifyContent:'center',alignItems:'center',gap:12,paddingTop:16}}>
              <Button size="sm" variant="secondary" disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}>{`← ${t('prev')}`}</Button>
              <span style={{fontSize:13,color:'var(--color-text-muted)'}}>
                {t('pageOf', { page, pages: ops.pages })}
              </span>
              <Button size="sm" variant="secondary" disabled={page >= ops.pages}
                onClick={() => setPage(p => p + 1)}>{`${t('next')} →`}</Button>
            </div>
          )}
        </>
      )}
    </Modal>
  )
}
