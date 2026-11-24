# Ứng dụng Quản lý và Phân tích Chi tiêu Cá nhân

Ứng dụng web Streamlit quản lý thu chi cá nhân theo quy trình:
**Nguồn dữ liệu -> Thu thập -> Làm sạch -> SQLite -> Phân tích -> Plotly -> Streamlit**.

## Cài đặt

Yêu cầu Python 3.10 trở lên.

```bash
cd personal-expense-tracker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python data\generate_sample_data.py
streamlit run app.py
```

Mở trình duyệt tại địa chỉ Streamlit hiển thị (thường là `http://localhost:8501`).

## Dữ liệu

- `data/raw_transactions.csv`: dữ liệu thô mẫu, khoảng 180 giao dịch trong sáu tháng.
- File cố ý chứa trùng lặp, thiếu ngày/mô tả, tiền không hợp lệ và tên danh mục sai định dạng.
- `src/data_cleaner.py` chuẩn hóa ngày, danh mục, loại thu/chi; loại bỏ trùng lặp và dòng bắt buộc bị thiếu.
- Tỷ giá lấy từ `https://open.er-api.com/v6/latest/VND`. Ứng dụng lưu cache một giờ và dùng tỷ giá dự phòng khi mất mạng.

## Cơ sở dữ liệu

SQLite nằm tại `database/expenses.db`. Cấu trúc được định nghĩa trong `database/schema.sql`:

- `categories(id, name, type)`: danh mục thu/chi.
- `transactions(id, date, description, amount, type, category_id, payment_method, note)`.
- `budgets(id, category_id, month, amount)`: ngân sách theo danh mục và tháng.

Khởi tạo database tự động khi chạy ứng dụng.

## Chức năng

- Dashboard KPI, cơ cấu chi tiêu, xu hướng và quy đổi USD/EUR.
- Thêm, sửa, xóa giao dịch; tìm kiếm, lọc ngày/danh mục/loại.
- Làm sạch dữ liệu và nhập dữ liệu CSV mẫu vào SQLite.
- Thiết lập và theo dõi ngân sách theo tháng.
- Báo cáo thống kê thu/chi theo ngày, tháng và danh mục.

## Deploy Streamlit Cloud

1. Đưa thư mục dự án lên GitHub.
2. Tạo app mới trên Streamlit Community Cloud.
3. Chọn `app.py` làm Main file.
4. Python runtime tối thiểu phải là 3.10.