import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Optional


COLORS_INCOME = "#2ecc71"
COLORS_EXPENSE = "#e74c3c"
PALETTE = px.colors.qualitative.Set3


def income_expense_bar(monthly_data: list[dict]) -> go.Figure:
    """Bar chart: income vs expense per month."""
    if not monthly_data:
        return _empty_figure("No data available")

    df = pd.DataFrame(monthly_data)
    income_df = df[df["operation_type"] == "income"]
    expense_df = df[df["operation_type"] == "expense"]

    months = sorted(df[["year", "month"]].drop_duplicates().values.tolist())
    labels = [f"{m[0]}-{m[1]:02d}" for m in months]

    income_vals = []
    expense_vals = []
    for y, m in months:
        inc_row = income_df[(income_df["year"] == y) & (income_df["month"] == m)]
        exp_row = expense_df[(expense_df["year"] == y) & (expense_df["month"] == m)]
        income_vals.append(float(inc_row["total"].iloc[0]) if not inc_row.empty else 0)
        expense_vals.append(float(exp_row["total"].iloc[0]) if not exp_row.empty else 0)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Income", x=labels, y=income_vals,
        marker_color=COLORS_INCOME, opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        name="Expense", x=labels, y=expense_vals,
        marker_color=COLORS_EXPENSE, opacity=0.85,
    ))
    fig.update_layout(
        barmode="group",
        title="Income vs Expense by Month",
        xaxis_title="Month",
        yaxis_title="Amount",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def category_pie(category_data: list[dict], op_type: str = "expense") -> go.Figure:
    """Pie chart: breakdown by category."""
    filtered = [r for r in category_data if r["operation_type"] == op_type]
    if not filtered:
        return _empty_figure(f"No {op_type} data")

    labels = [r["category_name"] or "Uncategorized" for r in filtered]
    values = [float(r["total"]) for r in filtered]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=PALETTE),
        textinfo="label+percent",
        hovertemplate="%{label}: %{value:,.2f}<extra></extra>",
    ))
    fig.update_layout(
        title=f"{'Expenses' if op_type == 'expense' else 'Income'} by Category",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
    )
    return fig


def balance_trend(history: list[dict]) -> go.Figure:
    """Line chart: debit/credit balance trend."""
    if not history:
        return _empty_figure("No balance history")

    df = pd.DataFrame(history)
    df = df.sort_values(["year", "month"])
    df["label"] = df.apply(lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["label"],
        y=df["debit_balance"].astype(float),
        name="Debit Balance",
        mode="lines+markers",
        line=dict(color="#3498db", width=2),
        marker=dict(size=6),
    ))
    fig.add_trace(go.Scatter(
        x=df["label"],
        y=df["credit_balance"].astype(float),
        name="Credit Balance",
        mode="lines+markers",
        line=dict(color="#e67e22", width=2, dash="dot"),
        marker=dict(size=6),
    ))
    fig.update_layout(
        title="Balance Trend",
        xaxis_title="Month",
        yaxis_title="Balance",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def payment_type_bar(payment_data: list[dict]) -> go.Figure:
    """Horizontal bar: breakdown by payment type."""
    if not payment_data:
        return _empty_figure("No data")

    labels = [r["payment_type"].replace("_", " ").title() for r in payment_data]
    values = [float(r["total"]) for r in payment_data]
    colors = [COLORS_EXPENSE if r["operation_type"] == "expense" else COLORS_INCOME
              for r in payment_data]

    fig = go.Figure(go.Bar(
        x=values, y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{v:,.2f}" for v in values],
        textposition="auto",
    ))
    fig.update_layout(
        title="By Payment Type",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def _empty_figure(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=msg, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="gray"),
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
    )
    return fig
