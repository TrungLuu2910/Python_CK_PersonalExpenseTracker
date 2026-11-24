from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


OUTPUT = Path(__file__).resolve().parent / "raw_transactions.csv"
random.seed(42)
np.random.seed(42)

expense_categories = {
    "Ăn uống": (45000, 250000),
    "Di chuyển": (30000, 180000),
    "Nhà ở": (1500000, 3500000),
    "Mua sắm": (80000, 1200000),
    "Giải trí": (50000, 500000),
    "Sức khỏe": (40000, 700000),
    "Giáo dục": (100000, 900000),
    "Hóa đơn": (200000, 1500000),
    "Khác": (30000, 400000),
}
income_categories = {
    "Lương": (12000000, 18000000),
    "Thưởng": (800000, 3500000),
    "Đầu tư": (300000, 2500000),
}
descriptions = {
    "Ăn uống": ["Cơm trưa", "Cafe", "Ăn tối", "Đặt đồ ăn"],
    "Di chuyển": ["Grab", "Xăng xe", "Xe buýt", "Gửi xe"],
    "Nhà ở": ["Tiền thuê phòng", "Sửa chữa nhà", "Internet"],
    "Mua sắm": ["Mua quần áo", "Siêu thị", "Đồ dùng"],
    "Giải trí": ["Xem phim", "Game", "Du lịch cuối tuần"],
    "Sức khỏe": ["Thuốc", "Khám bệnh", "Gym"],
    "Giáo dục": ["Sách", "Khóa học", "Nạp học phí"],
    "Hóa đơn": ["Tiền điện", "Tiền nước", "Điện thoại"],
    "Khác": ["Chi tiêu linh tinh", "Quà"],
    "Lương": ["Lương tháng"],
    "Thưởng": ["Thưởng hiệu suất"],
    "Đầu tư": ["Cổ tức", "Lãi tiết kiệm"],
}


def make_row(tx_date: date) -> dict:
    if random.random() < 0.18:
        category = random.choice(list(income_categories))
        tx_type = "thu"
        low, high = income_categories[category]
        amount = random.randint(low, high)
    else:
        category = random.choice(list(expense_categories))
        tx_type = "chi"
        low, high = expense_categories[category]
        amount = random.randint(low, high)
    return {
        "date": tx_date.strftime("%Y-%m-%d"),
        "description": random.choice(descriptions[category]),
        "amount": amount,
        "type": tx_type,
        "category": category,
        "payment_method": random.choice(["Tiền mặt", "Thẻ", "Ví điện tử", "Bank"]),
        "note": random.choice(["", "", "Giao dịch thường xuyên", ""]),
    }


end = date.today()
start = end - timedelta(days=181)
rows = []
for i in range(180):
    tx_date = start + timedelta(days=random.randint(0, 181))
    rows.append(make_row(tx_date))

# Cố ý thêm dữ liệu bẩn để demo làm sạch
rows.extend([
    {"date": "2026/06/15", "description": "  ca phe  ", "amount": "55000",
     "type": "CHI", "category": " an uống ", "payment_method": "Ví điện tử", "note": ""},
    {"date": None, "description": "Giao dịch thiếu ngày", "amount": "100000",
     "type": "chi", "category": "Khác", "payment_method": "Thẻ", "note": "cần xem lại"},
    {"date": "2026-06-20", "description": None, "amount": "200000",
     "type": "chi", "category": "Ăn uống", "payment_method": "Tiền mặt", "note": ""},
])
rows.append(rows[10].copy())

df = pd.DataFrame(rows)
df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
print(f"Da tao {len(df)} dong tai {OUTPUT}")
