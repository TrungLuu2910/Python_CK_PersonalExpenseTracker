from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


CATEGORY_ALIASES = {
    "an uong": "Ăn uống", "ăn uống": "Ăn uống", "food": "Ăn uống",
    "di chuyển": "Di chuyển", "di chuyen": "Di chuyển", "transport": "Di chuyển",
    "nhà ở": "Nhà ở", "nha o": "Nhà ở", "housing": "Nhà ở",
    "mua sắm": "Mua sắm", "mua sam": "Mua sắm", "shopping": "Mua sắm",
    "giải trí": "Giải trí", "giai tri": "Giải trí", "giải tiện": "Giải trí",
    "sức khỏe": "Sức khỏe", "suc khoe": "Sức khỏe",
    "giáo dục": "Giáo dục", "giao duc": "Giáo dục",
    "hóa đơn": "Hóa đơn", "hoa don": "Hóa đơn",
    "khác": "Khác", "khac": "Khác", "other": "Khác",
    "lương": "Lương", "luong": "Lương", "salary": "Lương",
    "thưởng": "Thưởng", "thuong": "Thưởng", "bonus": "Thưởng",
    "đầu tư": "Đầu tư", "dau tu": "Đầu tư", "investment": "Đầu tư",
}


def _fold(text: str) -> str:
    return " ".join(text.strip().lower().split())


def normalize_category(value) -> str:
    if pd.isna(value):
        return "Khác"
    text = str(value).strip()
    key = _fold(text)
    return CATEGORY_ALIASES.get(key, text)


def clean_transactions(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Trả về (dữ liệu sạch, báo cáo chất lượng)."""
    report = pd.DataFrame({
        "metric": ["Dòng đầu vào", "Dòng trùng lặp", "Dòng thiếu bắt buộc",
                   "Ngày không hợp lệ", "Số tiền không hợp lệ"],
        "count": [0, 0, 0, 0, 0],
    })
    original_count = len(df)

    clean = df.copy()
    required = {"date", "description", "amount", "type", "category"}
    missing_columns = required - set(clean.columns)
    if missing_columns:
        raise ValueError(f"Thiếu cột bắt buộc: {', '.join(sorted(missing_columns))}")

    duplicate_count = int(clean.duplicated().sum())
    clean = clean.drop_duplicates()

    clean["date"] = pd.to_datetime(clean["date"], format="mixed", errors="coerce")
    invalid_date_count = int(clean["date"].isna().sum())

    clean["description"] = clean["description"].fillna("").astype(str).str.strip()
    clean["description"] = clean["description"].replace("", np.nan)
    clean["amount"] = pd.to_numeric(clean["amount"], errors="coerce")

    clean["type"] = (clean["type"].fillna("").astype(str).str.strip().str.lower()
                     .replace({"thu nhập": "income", "income": "income", "thu": "income",
                               "chi tiêu": "expense", "expense": "expense", "chi": "expense"}))
    clean["category"] = clean["category"].apply(normalize_category)
    clean["payment_method"] = clean.get("payment_method", "Tiền mặt").fillna("Tiền mặt").astype(str).str.strip()
    clean["note"] = clean.get("note", "").fillna("").astype(str).str.strip()

    missing_count = int(clean[["date", "description", "amount", "type", "category"]].isna().sum().sum())
    invalid_amount_count = int((clean["amount"].isna() | (clean["amount"] < 0)).sum())
    clean = clean.dropna(subset=["date", "description", "amount", "type"])
    clean = clean[clean["type"].isin(["income", "expense"])]
    clean = clean[clean["amount"] >= 0]
    clean["date"] = clean["date"].dt.strftime("%Y-%m-%d")

    clean["category"] = clean["category"].replace("", "Khác").fillna("Khác")
    clean = clean.reset_index(drop=True)

    report["count"] = [
        original_count, duplicate_count, missing_count, invalid_date_count, invalid_amount_count
    ]
    return clean, report


def collect_csv(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy dữ liệu: {path}")
    return pd.read_csv(path, encoding="utf-8-sig")
