"""Dashboard page — main landing page with KPIs and charts."""
import streamlit as st
from datetime import datetime

from app.db.connection import run_async
from app.services.balance_service import BalanceService
from app.services.operation_service import OperationService
from app.services.report_service import ReportService
from app.ui.components.charts import income_expense_bar, balance_trend
from app.utils.formatters import format_currency, format_month_year


def render():
    st.title("Family Budget — Dashboard")
    st.markdown("---")

    now = datetime.now()
    year, month = now.year, now.month

    # Load data
    balance_svc = BalanceService()
    op_svc = OperationService()
    report_svc = ReportService()

    try:
        balance = run_async(balance_svc.get_or_create(year, month))
        summary = run_async(op_svc.get_monthly_summary(year, month))
        history = run_async(balance_svc.get_history(12))
        monthly = run_async(report_svc.by_month())
        forecast = run_async(report_svc.forecast_next_month(year, month))
    except Exception as e:
        st.error(f"Failed to load dashboard data: {e}")
        return

    # KPI cards
    st.subheader(f"Current Month: {format_month_year(year, month)}")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Debit Balance",
            value=format_currency(balance.debit_balance),
            delta=None,
        )
    with col2:
        st.metric(
            label="Credit Balance",
            value=format_currency(balance.credit_balance),
        )
    with col3:
        st.metric(
            label="Monthly Income",
            value=format_currency(summary["total_income"]),
            delta=f"{summary['net']:+.2f}",
            delta_color="normal",
        )
    with col4:
        st.metric(
            label="Monthly Expenses",
            value=format_currency(summary["total_expense"]),
        )

    st.markdown("---")

    # Forecast
    st.subheader(f"Forecast — {format_month_year(forecast['year'], forecast['month'])}")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        st.metric("Forecast Income", format_currency(forecast["forecast_income"]))
    with fc2:
        st.metric("Forecast Expenses", format_currency(forecast["forecast_expense"]))
    with fc3:
        net = forecast["forecast_net"]
        st.metric("Forecast Net", format_currency(net),
                  delta_color="normal" if net >= 0 else "inverse")

    st.markdown("---")

    # Charts
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(income_expense_bar(monthly), use_container_width=True)
    with col_right:
        history_dicts = [b.to_dict() for b in history]
        st.plotly_chart(balance_trend(history_dicts), use_container_width=True)

    # Navigation
    st.markdown("---")
    st.subheader("Quick Navigation")
    n1, n2, n3, n4 = st.columns(4)
    with n1:
        if st.button("📋 Operations", use_container_width=True):
            st.session_state["page"] = "operations"
            st.rerun()
    with n2:
        if st.button("📊 Reports", use_container_width=True):
            st.session_state["page"] = "reports"
            st.rerun()
    with n3:
        if st.button("🏷️ Categories", use_container_width=True):
            st.session_state["page"] = "categories"
            st.rerun()
    with n4:
        if st.button("📎 Attachments", use_container_width=True):
            st.session_state["page"] = "attachments"
            st.rerun()
