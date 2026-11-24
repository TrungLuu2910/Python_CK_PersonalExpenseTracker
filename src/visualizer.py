from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


TEMPLATE = "plotly_white"


def category_donut(df: pd.DataFrame) -> go.Figure:
    fig = px.pie(
        df,
        names="category",
        values="amount",
        hole=0.55,
        title="Cơ cấu chi tiêu theo danh mục",
        template=TEMPLATE,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(l=20, r=20, t=60, b=20))
    return fig


def monthly_trend(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["month"], y=df["income"], name="Thu",
        marker_color="#22c55e",
    ))
    fig.add_trace(go.Bar(
        x=df["month"], y=df["expense"], name="Chi",
        marker_color="#ef4444",
    ))
    fig.add_trace(go.Scatter(
        x=df["month"], y=df["balance"], name="Số dư",
        mode="lines+markers", line=dict(color="#2563eb", width=3),
    ))
    fig.update_layout(
        title="Xu hướng thu - chi - số dư theo tháng",
        barmode="group",
        template=TEMPLATE,
        yaxis_title="Số tiền (VND)",
        hovermode="x unified",
    )
    return fig


def budget_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["category"], y=df["budget"], name="Ngân sách",
        marker_color="#93c5fd",
    ))
    fig.add_trace(go.Bar(
        x=df["category"], y=df["actual"], name="Thực chi",
        marker_color="#fb7185",
    ))
    fig.update_layout(
        barmode="group",
        title="Ngân sách so với thực chi",
        template=TEMPLATE,
        yaxis_title="Số tiền (VND)",
    )
    return fig


def daily_spending(df: pd.DataFrame) -> go.Figure:
    data = df[df["type"] == "expense"].copy()
    if data.empty:
        return go.Figure()
    data["date"] = pd.to_datetime(data["date"])
    daily = data.groupby("date", as_index=False)["amount"].sum()
    fig = px.area(
        daily,
        x="date",
        y="amount",
        title="Xu hướng chi tiêu theo ngày",
        template=TEMPLATE,
        labels={"date": "Ngày", "amount": "Chi tiêu (VND)"},
    )
    fig.update_traces(line_color="#f97316")
    return fig
