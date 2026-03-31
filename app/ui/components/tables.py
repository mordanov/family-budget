"""Reusable table rendering helpers for Streamlit."""
import streamlit as st
import pandas as pd
from typing import Optional

from app.utils.formatters import (
    format_currency,
    format_datetime,
    truncate_text,
    operation_type_badge,
    payment_type_label,
)


def operations_table(operations: list, currency: str = "USD") -> Optional[pd.DataFrame]:
    if not operations:
        st.info("No operations found.")
        return None

    rows = []
    for op in operations:
        rows.append({
            "ID": op.id,
            "Date": format_datetime(op.operation_date, "%d %b %Y"),
            "Type": operation_type_badge(op.operation_type.value),
            "Amount": format_currency(op.amount, currency),
            "Payment": payment_type_label(op.payment_type.value),
            "Category": op.category_name or "—",
            "User": op.user_name or "—",
            "Description": truncate_text(op.description, 40),
            "Recurring": "✓" if op.is_recurring else "",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    return df


def categories_table(categories: list) -> Optional[pd.DataFrame]:
    if not categories:
        st.info("No categories found.")
        return None

    rows = []
    for cat in categories:
        rows.append({
            "ID": cat.id,
            "Icon": cat.icon or "",
            "Name": cat.name,
            "Description": truncate_text(cat.description, 50),
            "Color": cat.color or "",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    return df


def users_table(users: list) -> Optional[pd.DataFrame]:
    if not users:
        st.info("No users found.")
        return None

    rows = [{"ID": u.id, "Name": u.name, "Email": u.email} for u in users]
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
    return df


def report_table(data: list[dict], value_col: str = "total", label_col: str = "category_name") -> None:
    if not data:
        st.info("No data for this period.")
        return

    df = pd.DataFrame(data)
    if value_col in df.columns:
        df[value_col] = df[value_col].apply(lambda x: f"{float(x):,.2f}")
    if "count" in df.columns:
        df["count"] = df["count"].astype(int)

    st.dataframe(df, use_container_width=True, hide_index=True)


def balance_table(balances: list) -> None:
    if not balances:
        st.info("No balance history.")
        return

    rows = []
    for b in balances:
        rows.append({
            "Period": b.period_label,
            "Debit Balance": f"{float(b.debit_balance):,.2f}",
            "Credit Balance": f"{float(b.credit_balance):,.2f}",
            "Net": f"{float(b.net_balance):,.2f}",
            "Manual": "✓" if b.is_manual else "auto",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def attachments_table(attachments: list) -> None:
    if not attachments:
        st.info("No attachments.")
        return

    from app.utils.formatters import format_file_size, format_datetime
    rows = []
    for a in attachments:
        rows.append({
            "ID": a.id,
            "File": a.file_name,
            "Type": a.mime_type,
            "Size": format_file_size(a.file_size),
            "Uploaded": format_datetime(a.upload_date, "%d %b %Y"),
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
