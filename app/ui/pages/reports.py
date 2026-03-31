"""Reports page with date-range filters and multiple chart views."""
import streamlit as st
from datetime import datetime, date
import calendar

from app.db.connection import run_async
from app.services.report_service import ReportService
from app.services.balance_service import BalanceService
from app.ui.components.forms import date_range_selector
from app.ui.components.charts import (
    category_pie,
    income_expense_bar,
    payment_type_bar,
    balance_trend,
)
from app.ui.components.tables import report_table, balance_table
from app.utils.formatters import format_currency, format_month_year


def render():
    st.title("Reports")

    report_svc = ReportService()
    balance_svc = BalanceService()

    # Default: previous month
    now = datetime.now()
    if now.month == 1:
        prev_year, prev_month = now.year - 1, 12
    else:
        prev_year, prev_month = now.year, now.month - 1

    st.subheader("Date Range")
    date_from, date_to = date_range_selector("reports", prev_year, prev_month)
    st.caption(f"Showing: {date_from.strftime('%d %b %Y')} → {date_to.strftime('%d %b %Y')}")

    st.markdown("---")

    tab_summary, tab_category, tab_user, tab_payment, tab_monthly, tab_balance, tab_forecast = st.tabs([
        "Summary", "By Category", "By User", "By Payment",
        "Monthly Trend", "Balances", "Forecast",
    ])

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    with tab_summary:
        try:
            ive = run_async(report_svc.income_vs_expense(date_from, date_to))
        except Exception as e:
            st.error(f"Error: {e}")
            return

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Income", format_currency(ive["income"]))
        with col2:
            st.metric("Total Expenses", format_currency(ive["expense"]))
        with col3:
            net = ive["net"]
            st.metric("Net", format_currency(net),
                      delta_color="normal" if net >= 0 else "inverse")
        with col4:
            st.metric("Savings Rate", f"{ive['savings_rate']:.1f}%")

    # ── BY CATEGORY ───────────────────────────────────────────────────────────
    with tab_category:
        try:
            cat_data = run_async(report_svc.by_category(date_from, date_to))
        except Exception as e:
            st.error(f"Error: {e}")
            return

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(category_pie(cat_data, "expense"), use_container_width=True)
        with col2:
            st.plotly_chart(category_pie(cat_data, "income"), use_container_width=True)

        st.subheader("Category Breakdown")
        report_table(cat_data, value_col="total", label_col="category_name")

    # ── BY USER ───────────────────────────────────────────────────────────────
    with tab_user:
        try:
            user_data = run_async(report_svc.by_user(date_from, date_to))
        except Exception as e:
            st.error(f"Error: {e}")
            return

        report_table(user_data, value_col="total", label_col="user_name")

    # ── BY PAYMENT TYPE ───────────────────────────────────────────────────────
    with tab_payment:
        try:
            pay_data = run_async(report_svc.by_payment_type(date_from, date_to))
        except Exception as e:
            st.error(f"Error: {e}")
            return

        st.plotly_chart(payment_type_bar(pay_data), use_container_width=True)
        report_table(pay_data, value_col="total", label_col="payment_type")

    # ── MONTHLY TREND ─────────────────────────────────────────────────────────
    with tab_monthly:
        year_filter = st.selectbox("Year", list(range(now.year, now.year - 5, -1)),
                                   key="monthly_year")
        try:
            monthly_data = run_async(report_svc.by_month(year=year_filter))
        except Exception as e:
            st.error(f"Error: {e}")
            return

        st.plotly_chart(income_expense_bar(monthly_data), use_container_width=True)

    # ── BALANCES ──────────────────────────────────────────────────────────────
    with tab_balance:
        try:
            history = run_async(balance_svc.get_history(24))
        except Exception as e:
            st.error(f"Error: {e}")
            return

        history_dicts = [b.to_dict() for b in history]
        st.plotly_chart(balance_trend(history_dicts), use_container_width=True)
        balance_table(history)

        st.markdown("---")
        st.subheader("Manually Set Opening Balance")
        with st.form("manual_balance_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                bal_year = st.number_input("Year", min_value=2000, max_value=2100,
                                           value=now.year, step=1, key="bal_year")
            with col2:
                bal_month = st.number_input("Month", min_value=1, max_value=12,
                                            value=now.month, step=1, key="bal_month")
            with col3:
                pass
            debit = st.number_input("Debit Balance", min_value=0.0, step=0.01, format="%.2f",
                                    key="bal_debit")
            credit = st.number_input("Credit Balance", min_value=0.0, step=0.01, format="%.2f",
                                     key="bal_credit")
            if st.form_submit_button("Set Balance", type="primary"):
                from decimal import Decimal
                try:
                    run_async(balance_svc.set_manual(
                        int(bal_year), int(bal_month),
                        Decimal(str(debit)), Decimal(str(credit)),
                    ))
                    st.success(f"Balance set for {format_month_year(int(bal_year), int(bal_month))}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ── FORECAST ──────────────────────────────────────────────────────────────
    with tab_forecast:
        base_year = st.number_input("Base Year", value=now.year, min_value=2000,
                                    max_value=2100, key="fc_year")
        base_month = st.number_input("Base Month", value=now.month, min_value=1,
                                     max_value=12, key="fc_month")

        try:
            forecast = run_async(report_svc.forecast_next_month(int(base_year), int(base_month)))
        except Exception as e:
            st.error(f"Error: {e}")
            return

        st.subheader(f"Forecast for {format_month_year(forecast['year'], forecast['month'])}")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Forecast Income", format_currency(forecast["forecast_income"]))
        with c2:
            st.metric("Forecast Expenses", format_currency(forecast["forecast_expense"]))
        with c3:
            st.metric("Forecast Net", format_currency(forecast["forecast_net"]))

        if forecast["recurring_details"]:
            st.subheader("Recurring Items")
            import pandas as pd
            df = pd.DataFrame(forecast["recurring_details"])
            st.dataframe(df, use_container_width=True, hide_index=True)
