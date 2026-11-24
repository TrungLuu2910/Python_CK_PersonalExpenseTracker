from __future__ import annotations

import pandas as pd


def prepare_transactions(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce").fillna(0)
    data["month"] = data["date"].dt.to_period("M").astype(str)
    return data


def calculate_kpis(df: pd.DataFrame) -> dict:
    data = prepare_transactions(df)
    income = float(data.loc[data["type"] == "income", "amount"].sum())
    expense = float(data.loc[data["type"] == "expense", "amount"].sum())
    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "transaction_count": int(len(data)),
    }


def category_summary(df: pd.DataFrame, tx_type: str = "expense") -> pd.DataFrame:
    data = prepare_transactions(df)
    result = (
        data[data["type"] == tx_type]
        .groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )
    if not result.empty:
        result["percent"] = result["amount"] / result["amount"].sum() * 100
    return result


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    data = prepare_transactions(df)
    result = (
        data.groupby(["month", "type"], as_index=False)["amount"].sum()
        .pivot(index="month", columns="type", values="amount")
        .fillna(0)
        .reset_index()
    )
    if "income" not in result:
        result["income"] = 0
    if "expense" not in result:
        result["expense"] = 0
    result["balance"] = result["income"] - result["expense"]
    return result.sort_values("month")


def budget_progress(transactions: pd.DataFrame, budgets: pd.DataFrame,
                    month: str) -> pd.DataFrame:
    tx = prepare_transactions(transactions)
    actual = (
        tx[(tx["type"] == "expense") & (tx["month"] == month)]
        .groupby("category_id", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "actual"})
    )
    current = budgets[budgets["month"] == month].copy()
    if current.empty:
        return pd.DataFrame(columns=["category", "budget", "actual", "remaining", "progress"])
    result = current.merge(actual, on="category_id", how="left")
    result["actual"] = result["actual"].fillna(0)
    result["remaining"] = result["amount"] - result["actual"]
    result["progress"] = result["actual"] / result["amount"].clip(lower=0.0001) * 100
    return result.rename(columns={"amount": "budget"})[
        ["category", "budget", "actual", "remaining", "progress"]
    ]
