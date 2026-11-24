from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import db_manager
from src.analytics import (
    budget_progress,
    calculate_kpis,
    category_summary,
    monthly_summary,
)
from src.api_service import get_exchange_rates
from src.data_cleaner import clean_transactions, collect_csv
from src.visualizer import budget_chart, category_donut, daily_spending, monthly_trend


st.set_page_config(
    page_title="Quản lý Chi tiêu Cá nhân",
    page_icon="💰",
    layout="wide",
)

db_manager.initialize_database()

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💰 Quản lý và Phân tích Chi tiêu Cá nhân")
st.caption("Dữ liệu → làm sạch → SQLite → phân tích → trực quan hóa")

tab_dashboard, tab_transactions, tab_clean, tab_budget = st.tabs([
    "📊 Dashboard",
    "🧾 Giao dịch",
    "🧹 Làm sạch dữ liệu",
    "🎯 Ngân sách",
])

transactions = db_manager.get_transactions()

with tab_dashboard:
    if transactions.empty:
        st.info("Chưa có giao dịch. Hãy thêm giao dịch hoặc nhập dữ liệu mẫu.")
    else:
        kpis = calculate_kpis(transactions)
        rates = get_exchange_rates()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng thu", f"{kpis['income']:,.0f} VND")
        c2.metric("Tổng chi", f"{kpis['expense']:,.0f} VND")
        c3.metric("Số dư", f"{kpis['balance']:,.0f} VND")
        c4.metric("Số giao dịch", f"{kpis['transaction_count']:,}")

        m1, m2 = st.columns(2)
        m1.metric("Tổng thu (USD)", f"${kpis['income'] * rates['USD']:,.2f}")
        m2.metric("Tổng chi (EUR)", f"€{kpis['expense'] * rates['EUR']:,.2f}")
        st.caption(f"Nguồn tỷ giá: {rates['source']} • cache 1 giờ")

        left, right = st.columns([1, 1])
        expense_summary = category_summary(transactions, "expense")
        with left:
            if expense_summary.empty:
                st.info("Chưa có dữ liệu chi tiêu.")
            else:
                st.plotly_chart(category_donut(expense_summary), use_container_width=True)
        with right:
            monthly = monthly_summary(transactions)
            if monthly.empty:
                st.info("Chưa đủ dữ liệu theo tháng.")
            else:
                st.plotly_chart(monthly_trend(monthly), use_container_width=True)

        st.plotly_chart(daily_spending(transactions), use_container_width=True)

        st.subheader("Thống kê theo danh mục")
        col_expense, col_income = st.columns(2)
        col_expense.dataframe(
            category_summary(transactions, "expense"),
            use_container_width=True,
            hide_index=True,
        )
        col_income.dataframe(
            category_summary(transactions, "income"),
            use_container_width=True,
            hide_index=True,
        )

with tab_transactions:
    st.subheader("Tìm kiếm và lọc")
    f1, f2, f3, f4 = st.columns([1, 1, 1, 2])
    start = f1.date_input("Từ ngày", value=None)
    end = f2.date_input("Đến ngày", value=None)
    tx_type = f3.selectbox("Loại", ["Tất cả", "Thu", "Chi"])
    search = f4.text_input("Tìm mô tả hoặc ghi chú")

    categories = db_manager.get_categories()
    category_options = dict(zip(categories["name"], categories["id"]))
    selected_category_names = st.multiselect(
        "Danh mục",
        options=list(category_options.keys()),
    )
    category_ids = [category_options[name] for name in selected_category_names]

    filtered = db_manager.get_transactions(
        start_date=start.isoformat() if start else None,
        end_date=end.isoformat() if end else None,
        category_ids=category_ids or None,
        tx_type={"Thu": "income", "Chi": "expense"}.get(tx_type),
        search_text=search or None,
    )
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Thêm giao dịch")
    with st.form("add_transaction", clear_on_submit=True):
        a1, a2, a3 = st.columns(3)
        tx_date = a1.date_input("Ngày", value=pd.Timestamp.today())
        tx_kind_label = a2.selectbox("Loại", ["Chi", "Thu"])
        tx_kind = "expense" if tx_kind_label == "Chi" else "income"
        available_categories = categories[categories["type"] == tx_kind]
        category_id = a3.selectbox(
            "Danh mục",
            options=available_categories["id"].tolist(),
            format_func=lambda cid: available_categories.loc[
                available_categories["id"] == cid, "name"
            ].iloc[0],
        )
        d1, d2 = st.columns(2)
        description = d1.text_input("Mô tả")
        amount = d2.number_input("Số tiền (VND)", min_value=0.0, step=10000.0)
        p1, p2 = st.columns(2)
        payment_method = p1.selectbox(
            "Phương thức",
            ["Tiền mặt", "Thẻ", "Ví điện tử", "Chuyển khoản"],
        )
        note = p2.text_input("Ghi chú")
        submitted = st.form_submit_button("Thêm giao dịch", use_container_width=True)
        if submitted:
            if not description.strip():
                st.error("Mô tả không được để trống.")
            elif amount <= 0:
                st.error("Số tiền phải lớn hơn 0.")
            else:
                db_manager.add_transaction(
                    tx_date.isoformat(), description, amount, tx_kind,
                    int(category_id), payment_method, note,
                )
                st.success("Đã thêm giao dịch.")
                st.rerun()

    st.subheader("Sửa / xóa giao dịch")
    if not filtered.empty:
        selected_id = st.selectbox(
            "Chọn giao dịch",
            filtered["id"].tolist(),
            format_func=lambda tid: (
                f"{tid} - "
                f"{filtered.loc[filtered['id'] == tid, 'date'].iloc[0]} - "
                f"{filtered.loc[filtered['id'] == tid, 'description'].iloc[0]}"
            ),
        )
        row = filtered[filtered["id"] == selected_id].iloc[0]
        with st.form("edit_transaction"):
            e1, e2, e3 = st.columns(3)
            edit_date = e1.date_input(
                "Ngày sửa",
                value=pd.to_datetime(row["date"]).date(),
            )
            edit_kind = e2.selectbox(
                "Loại sửa",
                ["expense", "income"],
                index=0 if row["type"] == "expense" else 1,
                format_func=lambda value: "Chi" if value == "expense" else "Thu",
            )
            edit_categories = categories[categories["type"] == edit_kind]
            edit_category_id = e3.selectbox(
                "Danh mục sửa",
                options=edit_categories["id"].tolist(),
                index=max(
                    0,
                    edit_categories["id"].tolist().index(int(row["category_id"]))
                    if int(row["category_id"]) in edit_categories["id"].tolist()
                    else 0,
                ),
                format_func=lambda cid: edit_categories.loc[
                    edit_categories["id"] == cid, "name"
                ].iloc[0],
            )
            e4, e5 = st.columns(2)
            edit_description = e4.text_input("Mô tả sửa", value=row["description"])
            edit_amount = e5.number_input(
                "Số tiền sửa",
                min_value=0.0,
                value=float(row["amount"]),
                step=10000.0,
            )
            e6, e7 = st.columns(2)
            edit_payment = e6.text_input(
                "Phương thức sửa",
                value=row["payment_method"] if pd.notna(row["payment_method"]) else "",
            )
            edit_note = e7.text_input(
                "Ghi chú sửa",
                value=row["note"] if pd.notna(row["note"]) else "",
            )
            edit_submit = st.form_submit_button("Lưu thay đổi")
            if edit_submit:
                db_manager.update_transaction(
                    int(selected_id),
                    edit_date.isoformat(),
                    edit_description,
                    edit_amount,
                    edit_kind,
                    int(edit_category_id),
                    edit_payment,
                    edit_note,
                )
                st.success("Đã cập nhật.")
                st.rerun()

        if st.button("Xóa giao dịch đã chọn", type="secondary"):
            db_manager.delete_transaction(int(selected_id))
            st.success("Đã xóa.")
            st.rerun()

with tab_clean:
    st.subheader("Nguồn dữ liệu thô")
    raw_path = PROJECT_ROOT / "data" / "raw_transactions.csv"
    if not raw_path.exists():
        st.warning("Chưa có raw_transactions.csv. Chạy script sinh dữ liệu.")
    else:
        raw_df = collect_csv(raw_path)
        clean_df, report = clean_transactions(raw_df)

        c1, c2 = st.columns([1, 2])
        with c1:
            st.caption("Báo cáo chất lượng")
            st.dataframe(report, use_container_width=True, hide_index=True)
        with c2:
            st.caption("Xem trước dữ liệu sau làm sạch")
            st.dataframe(clean_df.head(30), use_container_width=True, hide_index=True)

        st.caption(f"Kết quả: {len(clean_df)} dòng hợp lệ từ {len(raw_df)} dòng nguồn.")
        if st.button("Nhập dữ liệu sạch vào SQLite", type="primary"):
            categories_df = db_manager.get_categories()
            category_lookup = dict(zip(categories_df["name"], categories_df["id"]))
            import_df = clean_df.copy()
            category_ids = []
            for _, row in import_df.iterrows():
                name = str(row["category"])
                if name not in category_lookup:
                    try:
                        cid = db_manager.add_category(name, str(row["type"]))
                        category_lookup[name] = cid
                    except Exception:
                        cid = category_lookup.get("Khác")
                else:
                    cid = category_lookup[name]
                category_ids.append(cid)
            import_df["category_id"] = category_ids
            inserted = db_manager.replace_transactions(import_df)
            st.success(f"Đã thay dữ liệu hiện tại bằng {inserted} giao dịch đã làm sạch.")
            st.rerun()

with tab_budget:
    st.subheader("Thiết lập ngân sách")
    expense_categories = db_manager.get_categories("expense")
    budget_month = st.text_input(
        "Tháng (YYYY-MM)",
        value=pd.Timestamp.today().strftime("%Y-%m"),
    )

    if expense_categories.empty:
        st.info("Chưa có danh mục chi tiêu.")
    else:
        with st.form("set_budget"):
            b1, b2 = st.columns(2)
            budget_category_id = b1.selectbox(
                "Danh mục",
                expense_categories["id"].tolist(),
                format_func=lambda cid: expense_categories.loc[
                    expense_categories["id"] == cid, "name"
                ].iloc[0],
            )
            budget_amount = b2.number_input(
                "Ngân sách (VND)",
                min_value=0.0,
                step=100000.0,
            )
            if st.form_submit_button("Lưu ngân sách"):
                if not pd.Period(budget_month, freq="M"):
                    st.error("Định dạng tháng không hợp lệ.")
                else:
                    db_manager.set_budget(
                        int(budget_category_id),
                        budget_month,
                        budget_amount,
                    )
                    st.success("Đã lưu ngân sách.")

    all_budgets = db_manager.get_budgets()
    st.dataframe(all_budgets, use_container_width=True, hide_index=True)

    st.subheader("Tiến độ ngân sách")
    try:
        pd.Period(budget_month, freq="M")
        progress = budget_progress(
            db_manager.get_transactions(),
            all_budgets,
            budget_month,
        )
        if progress.empty:
            st.info("Chưa có ngân sách cho tháng này.")
        else:
            st.plotly_chart(budget_chart(progress), use_container_width=True)
            st.dataframe(progress, use_container_width=True, hide_index=True)
    except ValueError:
        st.error("Vui lòng nhập tháng đúng định dạng YYYY-MM.")
