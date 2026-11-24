from __future__ import annotations

import requests
import streamlit as st


API_URL = "https://open.er-api.com/v6/latest/VND"
FALLBACK_RATES = {"USD": 0.000039, "EUR": 0.000037}


@st.cache_data(ttl=3600, show_spinner=False)
def get_exchange_rates() -> dict:
    try:
        response = requests.get(API_URL, timeout=8)
        response.raise_for_status()
        data = response.json()
        if data.get("result") != "success":
            raise ValueError("API không trả về kết quả thành công")
        return {
            "USD": float(data["rates"]["USD"]),
            "EUR": float(data["rates"]["EUR"]),
            "source": "Trực tuyến",
        }
    except Exception:
        return {
            "USD": FALLBACK_RATES["USD"],
            "EUR": FALLBACK_RATES["EUR"],
            "source": "Tỷ giá dự phòng",
        }
