from datetime import date, timedelta
import logging
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("enerji_dashboard")

try:
    from src.epias_csv import (
        get_dataset_bounds,
        get_latest_complete_window,
        load_generation_data,
        load_hourly_profile,
    )
except ImportError:
    from src.data_helper import load_generation_data
    get_dataset_bounds = None
    get_latest_complete_window = None
    load_hourly_profile = None

from src.forecast_engine import REGIONS, calculate_esg_savings, fetch_all_regions_weather
from src.ml_forecaster import train_and_evaluate_models
from src.esg_analytics import (
    ENTERPRISE_PROFILES,
    calculate_grid_carbon_intensity,
    simulate_enterprise_esg,
)

WIND_COLOR = "#059669"
SUN_COLOR = "#EAB308"
MONTHS = ["", "Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
COLS = ["wind_mwh", "solar_mwh", "total_mwh"]

st.set_page_config(
    page_title="Enerji Nabzı · Türkiye Rüzgar ve Güneş Enerjisi İzleme ve Yapay Zeka ile Tahmin Platformu",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400..800;1,9..40,400..800&family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --ink: #0F2417;
    --mute: #526E5C;
    --line: #DCE7DE;
    --bg-app: #F0F5F1;
    --card-bg: #FFFFFF;
}

*, html, body, .stApp, [class*="css"], [class*="st-"], [data-testid="stAppViewContainer"] {
    font-family: 'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
    text-rendering: optimizeLegibility !important;
}

.stMarkdown, .stText, p, span, label, div {
    font-family: 'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

h1, h2, h3, h4, h5, h6, .chart-title, .hero-title {
    font-family: 'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    color: var(--ink) !important;
}

.stApp, [data-testid="stAppViewContainer"] {
    background: var(--bg-app) !important;
    color: var(--ink);
}

#MainMenu, footer, header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none !important;
}

.block-container {
    max-width: 98% !important;
    width: 98% !important;
    padding: 1.2rem 1.8rem 3rem !important;
    margin: 0 auto !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: #FFFFFF !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    padding: 20px 24px !important;
    box-shadow: 0 1px 3px rgba(15, 36, 23, 0.04) !important;
}

.hero {
    background: linear-gradient(135deg, #092015 0%, #113624 100%);
    color: #FFFFFF;
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 18px;
    box-shadow: 0 4px 20px -2px rgba(9, 32, 21, 0.2);
    border: 1px solid rgba(52, 211, 153, 0.15);
}
.hero-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.eyebrow {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: #34D399;
    text-transform: uppercase;
}
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid rgba(52, 211, 153, 0.4);
    color: #A7F3D0;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
}
.status-pill i {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #34D399;
    box-shadow: 0 0 8px #34D399;
}
.hero h1 {
    color: #FFFFFF !important;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
    margin: 0 0 8px 0 !important;
    letter-spacing: -0.03em !important;
}
.hero p {
    color: #A7F3D0 !important;
    font-size: 0.95rem !important;
    max-width: 820px;
    margin: 0 !important;
    line-height: 1.5;
}

.live-status-ribbon {
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 14px 22px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 16px;
    box-shadow: 0 1px 3px rgba(15, 36, 23, 0.04);
}
.lsr-item {
    display: flex;
    align-items: center;
    gap: 12px;
}
.lsr-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
}
.lsr-dot.green {
    background: #10B981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}
.lsr-dot.neutral {
    background: #94A3B8;
}
.lsr-lbl {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--mute);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.lsr-val {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--ink);
}
.lsr-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.74rem;
    font-weight: 600;
}
.lsr-badge.green {
    background: #DCFCE7;
    color: #15803D;
    border: 1px solid #86EFAC;
}
.lsr-badge.neutral {
    background: #F1F5F9;
    color: #475569;
    border: 1px solid #CBD5E1;
}

/* Modern Segmented Pill Tabs */
div[data-testid="stTabs"] > div:first-child {
    background-color: #E2ECE4 !important;
    padding: 4px !important;
    border-radius: 12px !important;
    gap: 6px !important;
    border: 1px solid #CBDDD0 !important;
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.04) !important;
    margin-bottom: 20px !important;
    display: flex !important;
    width: 100% !important;
}

div[data-testid="stTabs"] button[role="tab"] {
    background-color: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    color: #4A6352 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 9px 16px !important;
    transition: all 0.15s ease-in-out !important;
    box-shadow: none !important;
    flex: 1 1 0px !important;
    text-align: center !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    white-space: nowrap !important;
}

div[data-testid="stTabs"] button[role="tab"]:hover {
    background-color: rgba(255, 255, 255, 0.45) !important;
    color: #0F2417 !important;
}

div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background-color: #FFFFFF !important;
    color: #0F2417 !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08), 0 1px 1px rgba(0, 0, 0, 0.04) !important;
}

div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
div[data-testid="stTabs"] [data-baseweb="tab-border"] {
    display: none !important;
}

.weather-section-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #0F2417;
    margin-bottom: 2px;
    letter-spacing: -0.01em;
    display: flex;
    align-items: center;
    gap: 8px;
}
.weather-section-desc {
    font-size: 0.82rem;
    color: #526E5C;
    margin-bottom: 12px;
}
.w-card {
    background: #F8FAF9;
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
}
.w-card-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--mute);
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.w-card-val {
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--ink);
    letter-spacing: -0.02em;
    line-height: 1.2;
}
.w-card-val .unit {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--mute);
}
.w-card-sub {
    font-size: 0.75rem;
    color: var(--mute);
    margin-top: 4px;
}

.control-bar-title {
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: var(--mute);
    text-transform: uppercase;
    margin-bottom: 6px;
}
.active-range-badge {
    background: #EAF2EC;
    border: 1px solid #CDE0D2;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.8rem;
    color: #1F3826;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin-top: 10px;
}
.range-indicator {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #059669;
}
.range-hours-pill {
    background: #FFFFFF;
    border: 1px solid #CDE0D2;
    border-radius: 999px;
    padding: 2px 8px;
    font-size: 0.72rem;
    font-weight: 600;
    color: #059669;
}
.meta-pills {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: flex-end;
    align-items: center;
    height: 100%;
}
.meta-pill {
    background: #F8FAF9;
    border: 1px solid var(--line);
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.74rem;
    color: var(--mute);
}
.meta-pill b {
    color: var(--ink);
}

.grid-6 {
    display: grid !important;
    grid-template-columns: repeat(6, 1fr) !important;
    gap: 12px !important;
    margin: 14px 0 18px 0 !important;
}

@media (max-width: 1400px) {
    .grid-6 {
        grid-template-columns: repeat(3, 1fr) !important;
    }
}

@media (max-width: 768px) {
    .grid-6 {
        grid-template-columns: repeat(2, 1fr) !important;
    }
}

.grid-4 {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 12px !important;
    margin: 12px 0 16px 0 !important;
}

@media (max-width: 1024px) {
    .grid-4 {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 10px !important;
    }
}

@media (max-width: 600px) {
    .grid-4 {
        grid-template-columns: 1fr !important;
        gap: 10px !important;
    }
}

.card {
    background: var(--card-bg);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px -4px rgba(0,0,0,0.06);
}
.card-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
}
.card-dot.wind { background: #059669; }
.card-dot.sun { background: #EAB308; }
.card-dot.total { background: #4F46E5; }
.card-dot.pct { background: #7C3AED; }
.card-dot.peak { background: #DC2626; }
.card-dot.esg { background: #0D9488; }

.lb {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--mute);
    margin-bottom: 6px;
    letter-spacing: -0.01em;
}
.val {
    font-size: 1.55rem;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: -0.025em;
    line-height: 1.2;
}
.val .u {
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--mute);
    margin-left: 4px;
}
.nt {
    font-size: 0.74rem;
    color: var(--mute);
    margin-top: 8px;
}

.chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 12px;
}
.chart-title {
    font-size: 1.12rem !important;
    font-weight: 700 !important;
    color: var(--ink) !important;
    letter-spacing: -0.02em !important;
    margin: 0 !important;
}
.chart-sub {
    font-size: 0.84rem !important;
    font-weight: 400 !important;
    color: var(--mute) !important;
    letter-spacing: -0.01em !important;
    margin: 3px 0 0 0 !important;
}
.legend-pill {
    display: flex;
    gap: 14px;
    font-size: 0.8rem;
    color: var(--mute);
    align-items: center;
}
.legend-pill span {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: 500;
}
.legend-pill i {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.foot-bar {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 0.76rem;
    color: var(--mute);
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid var(--line);
}
.methodology-note {
    font-size: 0.78rem;
    color: #375240;
    line-height: 1.6;
    margin-top: 16px;
    padding: 14px 18px;
    background: #EAF2EC;
    border: 1px solid var(--line);
    border-radius: 10px;
}
</style>""",
    unsafe_allow_html=True,
)

def tr_format(val: float, d: int = 0) -> str:
    if val is None or pd.isna(val):
        return "–"
    return f"{val:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def date_label(d: date) -> str:
    return f"{d.day} {MONTHS[d.month]} {d.year}"

def ts_label(t: pd.Timestamp) -> str:
    if not isinstance(t, pd.Timestamp):
        return str(t)
    return f"{t.day} {MONTHS[t.month]} · {t:%H:%M}"

def build_card(tone: str, label: str, val_str: str, unit: str = "", note: str = "") -> str:
    unit_html = f'<span class="u">{unit}</span>' if unit else ""
    return (
        f'<div class="card">'
        f'  <div>'
        f'    <div class="lb"><span class="card-dot {tone}"></span>{label}</div>'
        f'    <div class="val">{val_str}{unit_html}</div>'
        f'  </div>'
        f'  <div class="nt">{note}</div>'
        f'</div>'
    )

@st.cache_data(ttl=900, show_spinner=False)
def fetch_generation_data(start: date, end: date) -> pd.DataFrame:
    return load_generation_data(start, end)

@st.cache_data(ttl=900, show_spinner=False)
def get_cached_ml_results(start_d: date, end_d: date, horizon_h: int = 24) -> dict:
    base_data = fetch_generation_data(start_d, end_d)
    return train_and_evaluate_models(base_data, horizon_hours=horizon_h)

full_start, full_end = None, None
if get_dataset_bounds is not None:
    try:
        full_start, full_end = get_dataset_bounds()
    except Exception:
        full_start, full_end = None, None

win_end = full_end if full_end is not None else date.today()
win_start = win_end - timedelta(days=29)

if full_start is None:
    full_start = win_start
if full_end is None:
    full_end = win_end

all_weather = fetch_all_regions_weather()
baseline_df = fetch_generation_data(win_start, win_end)
ci_data = calculate_grid_carbon_intensity(baseline_df) if calculate_grid_carbon_intensity is not None else None
clean_df = baseline_df.copy()

st.markdown(
    """
    <div class="hero">
        <div class="hero-top">
            <span class="eyebrow">YENİLENEBİLİR ENERJİ İZLEME PLATFORMU · ENERJİ NABZI</span>
            <span class="status-pill"><i></i>EPİAŞ Gerçek Verisi</span>
        </div>
        <h1>Türkiye Rüzgar ve Güneş Enerjisi İzleme ve Yapay Zeka ile Tahmin Platformu</h1>
        <p>Saatlik üretimi, bölgesel hava durumunu, rüzgar + güneş payını, yapay zeka üretim tahminlerini ve tepe üretim saatlerini tek bir ekranda inceleyin.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if ci_data:
    gw_dot_cls = "green" if ci_data["is_green_window"] else "neutral"
    st.markdown(
        f"""
        <div class="live-status-ribbon">
            <div class="lsr-item">
                <span class="lsr-dot {gw_dot_cls}"></span>
                <div>
                    <div class="lsr-lbl">Şebeke Durumu</div>
                    <div class="lsr-val">{ci_data['status_title']}</div>
                </div>
            </div>
            <div class="lsr-sep"></div>
            <div class="lsr-item">
                <div>
                    <div class="lsr-lbl">Anlık Karbon Yoğunluğu</div>
                    <div class="lsr-val">{ci_data['carbon_intensity']} <span class="lsr-unit">gCO₂/kWh</span></div>
                </div>
            </div>
            <div class="lsr-sep"></div>
            <div class="lsr-item">
                <div>
                    <div class="lsr-lbl">Temiz Enerji Payı</div>
                    <div class="lsr-val">%{ci_data['renewable_share']}</div>
                </div>
            </div>
            <div class="lsr-sep"></div>
            <div class="lsr-item lsr-rec">
                <div>
                    <div class="lsr-lbl">Karar Destek / Akıllı Yönlendirme</div>
                    <div style="font-size:0.8rem; color:#475569; line-height:1.35; margin-top:2px;">{ci_data['recommendation']}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

tab_grid, tab_ai, tab_esg = st.tabs([
    "Canlı Şebeke & Hava Durumu",
    "Yapay Zeka Tahmini (24s – 3 Ay)",
    "Kurumsal ESG Simülatörü",
])

with tab_grid:
    with st.container(border=True):
        col_w_side, col_w_map = st.columns([1, 1.3], gap="large")
        with col_w_side:
            st.markdown(
                """
                <div>
                    <div class="weather-section-title">Canlı Hava Durumu & Bölge Seçimi</div>
                    <div style="font-size:0.82rem; color:#64748B; margin-top:2px; margin-bottom:10px;">
                        İncelemek istediğiniz coğrafi bölgeyi seçin
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            selected_region = st.selectbox(
                "İncelenen Bölge",
                options=list(REGIONS.keys()),
                index=0,
                key="region_selector",
                label_visibility="collapsed",
            )
            w_info = all_weather.get(selected_region, all_weather["Tüm Türkiye (Ortalama)"])
            st.markdown(
                f"""
                <div style="display:flex; flex-direction:column; gap:10px; margin-top:10px;">
                    <div class="w-card">
                        <div class="w-card-header">
                            <span>Rüzgar Durumu</span>
                            <span style="color:#059669; font-weight:700;">Canlı</span>
                        </div>
                        <div class="w-card-val">{tr_format(w_info['wind_speed_kmh'], 1)} <span class="unit">km/s</span></div>
                        <div class="w-card-sub">{w_info['wind_speed_ms']} m/s · {w_info['temp_c']} °C · <b>{w_info['wind_status']}</b></div>
                    </div>
                    <div class="w-card">
                        <div class="w-card-header">
                            <span>Güneş Işınımı</span>
                            <span style="color:#D97706; font-weight:700;">Canlı</span>
                        </div>
                        <div class="w-card-val">{tr_format(w_info['solar_rad_wm2'], 0)} <span class="unit">W/m²</span></div>
                        <div class="w-card-sub">Bulut: %{tr_format(w_info['cloud_cover'], 0)} · <b>{w_info['solar_status']}</b></div>
                    </div>
                    <div class="w-card">
                        <div class="w-card-header">
                            <span>Havza Detayı</span>
                            <span style="color:#2563EB; font-weight:700;">{selected_region}</span>
                        </div>
                        <div class="w-card-sub" style="font-size:0.83rem;">{w_info['desc']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_w_map:
            st.markdown(
                """
                <div>
                    <div class="weather-section-title">Türkiye Canlı Potansiyel Haritası</div>
                    <div style="font-size:0.82rem; color:#64748B; margin-top:2px; margin-bottom:4px;">
                        7 coğrafi bölgenin anlık rüzgar hızı ve meteorolojik dağılımı (Detaylar için bölgelerin üzerine gelin)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            map_rows = []
            for reg_k, reg_v in REGIONS.items():
                if reg_k == "Tüm Türkiye (Ortalama)":
                    continue
                w_item = all_weather.get(reg_k, {})
                map_rows.append({
                    "region": reg_k,
                    "lat": reg_v["lat"],
                    "lon": reg_v["lon"],
                    "wind_kmh": w_item.get("wind_speed_kmh", 20.0),
                    "temp_c": w_item.get("temp_c", 12.0),
                    "solar_wm2": w_item.get("solar_rad_wm2", 150.0),
                    "cloud": w_item.get("cloud_cover", 30.0),
                    "wind_status": w_item.get("wind_status", ""),
                    "desc": reg_v.get("desc", ""),
                })
            df_map = pd.DataFrame(map_rows)
            fig_tr = go.Figure()
            fig_tr.add_trace(
                go.Scattergeo(
                    lon=df_map["lon"],
                    lat=df_map["lat"],
                    text=df_map["region"],
                    customdata=np.stack([
                        df_map["wind_kmh"],
                        df_map["wind_status"],
                        df_map["temp_c"],
                        df_map["solar_wm2"],
                        df_map["desc"],
                    ], axis=-1),
                    hovertemplate="<b>%{text}</b><br>"
                                  "Havza: %{customdata[4]}<br>"
                                  "Rüzgar Hızı: %{customdata[0]} km/s (%{customdata[1]})<br>"
                                  "Sıcaklık: %{customdata[2]} °C<br>"
                                  "Güneş Işınımı: %{customdata[3]} W/m²<extra></extra>",
                    mode="markers+text",
                    textposition="top center",
                    textfont=dict(size=11, family="Plus Jakarta Sans, sans-serif", color="#1E293B"),
                    marker=dict(
                        size=df_map["wind_kmh"] * 0.75 + 16,
                        color=df_map["wind_kmh"],
                        colorscale=[[0, "#A7F3D0"], [0.5, "#10B981"], [1.0, "#047857"]],
                        colorbar=dict(title=dict(text="km/s", font=dict(size=10)), thickness=10, len=0.7),
                        line=dict(width=1.5, color="#065F46"),
                        opacity=0.9,
                    ),
                )
            )
            fig_tr.update_geos(
                center=dict(lat=39.0, lon=35.2),
                lataxis_range=[35.3, 42.4],
                lonaxis_range=[25.5, 44.8],
                visible=True,
                resolution=50,
                showcountries=True,
                countrycolor="#94A3B8",
                showcoastlines=True,
                coastlinecolor="#CBD5E1",
                showland=True,
                landcolor="#F8FAFC",
                showocean=True,
                oceancolor="#E8F1EB",
                projection_type="mercator",
            )
            fig_tr.update_layout(
                height=320,
                margin=dict(l=0, r=0, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_tr, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        col_filter, col_meta = st.columns([1.6, 2], gap="large")

        with col_filter:
            st.markdown('<div class="control-bar-title">İnceleme Dönemi</div>', unsafe_allow_html=True)
            period = st.segmented_control(
                "Dönem Seçimi",
                options=["Günlük (24 Saat)", "Haftalık (7 Gün)", "Aylık (30 Gün)", "Yıllık (365 Gün)", "Özel Aralık"],
                default="Haftalık (7 Gün)",
                label_visibility="collapsed",
            )

            if not period:
                period = "Haftalık (7 Gün)"

            if period == "Günlük (24 Saat)":
                start_date, end_date = win_end, win_end
                day_count = 1
            elif period == "Haftalık (7 Gün)":
                start_date, end_date = win_end - timedelta(days=6), win_end
                day_count = 7
            elif period == "Aylık (30 Gün)":
                start_date, end_date = win_start, win_end
                day_count = (win_end - win_start).days + 1
            elif period == "Yıllık (365 Gün)":
                start_date, end_date = full_start, full_end
                day_count = (full_end - full_start).days + 1
            else:
                col_s, col_e = st.columns(2)
                with col_s:
                    start_date = st.date_input("Başlangıç", value=win_end - timedelta(days=6), min_value=full_start, max_value=full_end)
                with col_e:
                    end_date = st.date_input("Bitiş", value=win_end, min_value=full_start, max_value=full_end)
                day_count = (end_date - start_date).days + 1 if end_date >= start_date else 0

            hours_count = day_count * 24
            st.markdown(
                f"""
                <div class="active-range-badge">
                    <span class="range-indicator"></span>
                    <span><b>Seçili Aralık:</b> {date_label(start_date)} — {date_label(end_date)}</span>
                    <span class="range-hours-pill">{day_count} Gün · {hours_count} Saat</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_meta:
            st.markdown(
                f"""
                <div class="meta-grid">
                    <div class="meta-pill">Kaynak: <b>EPİAŞ Şeffaflık</b></div>
                    <div class="meta-pill">Veri Kapsamı: <b>{date_label(full_start)} – {date_label(full_end)} (1 Yıl / 8.760+ Saat)</b></div>
                    <div class="meta-pill">Çözünürlük: <b>Saatlik (MWh)</b></div>
                    <div class="meta-pill">Saat Dilimi: <b>İstanbul (UTC+3)</b></div>
                    <div class="meta-pill">Önbellek: <b>15 Dk (TTL: 900s)</b></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    state = "ok"
    df = None

    if start_date > end_date:
        state = "range_error"
    else:
        try:
            with st.spinner("Piyasa verileri yükleniyor..."):
                df = fetch_generation_data(start_date, end_date)
                if df is None or df.empty:
                    state = "empty"
        except Exception:
            state = "error"

    if state == "ok" and df is not None and not df.empty:
        if not {"timestamp", *COLS} <= set(df.columns):
            state = "schema_error"

    if state == "range_error":
        st.error("Başlangıç tarihi bitiş tarihinden sonra olamaz. Lütfen tarih seçimini kontrol edin.")
        st.stop()

    if state == "error":
        st.error("Veri kaynağına erişilirken bir sorun oluştu. Lütfen veri bağlantısını kontrol edin.")
        st.stop()

    if state == "schema_error":
        st.error(
            "Veri Uyuşmazlığı: Beklenen sütunlar eksik. "
            "Veri fonksiyonunun timestamp, wind_mwh, solar_mwh, total_mwh alanlarını sağlaması gerekir."
        )
        st.stop()

    if state == "empty":
        st.info("Seçilen tarih aralığında gösterilecek veri bulunamadı. Lütfen geçerli bir tarih aralığı seçin.")
        st.stop()

    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    tz_aware = ts.dt.tz is not None

    if tz_aware:
        ts = ts.dt.tz_convert("Europe/Istanbul")
        clean_df = df.assign(ts=ts).dropna(subset=["ts"]).drop_duplicates("ts").sort_values("ts")
    else:
        clean_df = df.assign(ts=ts).dropna(subset=["ts"]).drop_duplicates("ts").sort_values("ts")
        st.warning(
            "Saat Dilimi Teyit Bekliyor: Zaman damgalarında saat dilimi bilgisi bulunamadı. "
            "Veriler olduğu gibi sunulmuştur."
        )

    for col in COLS:
        clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    wind_nans = int(clean_df["wind_mwh"].isna().sum())
    solar_nans = int(clean_df["solar_mwh"].isna().sum())
    total_nans = int(clean_df["total_mwh"].isna().sum())
    missing_nans = wind_nans + solar_nans + total_nans

    if missing_nans > 0:
        st.markdown(
            f'<div class="warn-box"><b>Eksik Ölçüm Uyarısı:</b> Seçili dönemde '
            f'Rüzgar: {wind_nans} saat, Güneş: {solar_nans} saat, Toplam: {total_nans} saat eksik (NaN) ölçüm tespit edildi. '
            f'Veri bütünlüğü için doldurma veya interpolasyon yapılmamıştır.</div>',
            unsafe_allow_html=True,
        )

    valid_wind = clean_df["wind_mwh"].dropna()
    valid_solar = clean_df["solar_mwh"].dropna()
    valid_total = clean_df["total_mwh"].dropna()

    wind_sum = valid_wind.sum() if not valid_wind.empty else None
    solar_sum = valid_solar.sum() if not valid_solar.empty else None
    pair_sum = (wind_sum or 0.0) + (solar_sum or 0.0) if (wind_sum is not None or solar_sum is not None) else None
    total_sum = valid_total.sum() if not valid_total.empty else None

    if total_sum is None or total_sum <= 0 or pair_sum is None:
        share_str = "Hesaplanamadı"
    else:
        share_str = f"%{tr_format((pair_sum / total_sum) * 100, 1)}"

    hourly_valid_pair = clean_df["wind_mwh"] + clean_df["solar_mwh"]
    peaks_series = hourly_valid_pair.dropna()

    if not peaks_series.empty and (peaks_series > 0).any():
        peak_idx = peaks_series.idxmax()
        peak_val = peaks_series.loc[peak_idx]
        peak_ts = clean_df.loc[peak_idx, "ts"]
        peak_val_str = tr_format(peak_val)
        peak_time_str = ts_label(peak_ts)
        peak_unit = "MWh"
    else:
        peak_val_str = "Hesaplanamadı"
        peak_time_str = "Geçerli zirve ölçümü yok"
        peak_unit = ""

    esg_data = calculate_esg_savings(pair_sum if pair_sum is not None else 0.0)

    st.markdown(
        f'<div class="grid-6">'
        + build_card("wind", "Rüzgar Üretimi", tr_format(wind_sum) if wind_sum is not None else "Veri Yok", "MWh", "Dönem toplamı")
        + build_card("sun", "Güneş Üretimi", tr_format(solar_sum) if solar_sum is not None else "Veri Yok", "MWh", "Dönem toplamı")
        + build_card("total", "Rüzgar + Güneş", tr_format(pair_sum) if pair_sum is not None else "Veri Yok", "MWh", "İki kaynağın toplamı")
        + build_card("pct", "Rüzgar + Güneş Payı", share_str, "", "Toplam üretimdeki oran")
        + build_card("peak", "Saatlik Zirve", peak_val_str, peak_unit, peak_time_str)
        + build_card("esg", "Önlenen CO₂ Salımı", esg_data["co2_formatted"], "ton", "~0,45 tCO₂ / MWh ikamesi")
        + "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="warn-box"><b>Güneş verisi hakkında:</b> EPİAŞ üretim serisi lisanssız (çatı ve öz tüketim) güneş üretimini '
        'tam yansıtmayabilir. Gerçek güneş üretimi ve rüzgar + güneş payı gösterilen değerlerden daha yüksek olabilir.</div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        col_t_title, col_t_legend = st.columns([1.6, 1], gap="medium")
        with col_t_title:
            st.markdown(
                """
                <div>
                    <h4 class="chart-title">Saatlik Üretim Dağılımı</h4>
                    <p class="chart-sub">Dönem boyunca rüzgar ve güneş santrallerinin saatlik üretim profili</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_t_legend:
            st.markdown(
                """
                <div style="display:flex; justify-content:flex-end; align-items:center; height:100%;">
                    <div class="legend-pill">
                        <span><i style="background:#059669"></i> Rüzgar</span>
                        <span><i style="background:#EAB308"></i> Güneş</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        chart_data = clean_df.set_index("ts")[["wind_mwh", "solar_mwh"]]
        if tz_aware:
            chart_data = chart_data.asfreq("h")

        fig_time = go.Figure()

        fig_time.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data["wind_mwh"],
                name="Rüzgar",
                mode="lines",
                connectgaps=False,
                line=dict(color=WIND_COLOR, width=2.2),
                fill="tozeroy",
                fillcolor="rgba(5, 150, 105, 0.08)",
                hovertemplate="Rüzgar: %{y:,.0f} MWh<extra></extra>",
            )
        )

        fig_time.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data["solar_mwh"],
                name="Güneş",
                mode="lines",
                connectgaps=False,
                line=dict(color=SUN_COLOR, width=2.2),
                fill="tozeroy",
                fillcolor="rgba(234, 179, 8, 0.12)",
                hovertemplate="Güneş: %{y:,.0f} MWh<extra></extra>",
            )
        )

        fig_time.update_layout(
            height=420,
            showlegend=False,
            hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans, sans-serif", color="#64748B", size=12),
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(showgrid=True, gridcolor="#E2E8F0", zeroline=False),
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0", zeroline=False, title="Üretim (MWh)"),
        )

        st.plotly_chart(fig_time, config={"displayModeBar": False})

        latest_ts = clean_df["ts"].max()
        st.markdown(
            f"""
            <div class="foot-bar">
                <span>Toplam {len(clean_df)} saatlik kayıt · <b>Verideki Son Kayıt:</b> {ts_label(latest_ts)} (TSİ)</span>
                <span>Zaman Dilimi: Europe/Istanbul (UTC+3)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    col_chart_left, col_chart_right = st.columns(2, gap="medium")

    with col_chart_left:
        if period == "Aylık (30 Gün)" and load_hourly_profile is not None:
            try:
                prof = load_hourly_profile().set_index("hour")
            except Exception:
                prof = clean_df.groupby(clean_df["ts"].dt.hour)[["wind_mwh", "solar_mwh"]].mean().reindex(range(24))
        else:
            prof = clean_df.groupby(clean_df["ts"].dt.hour)[["wind_mwh", "solar_mwh"]].mean().reindex(range(24))

        hour_labels = [f"{int(h):02d}:00" if str(h).isdigit() else str(h) for h in prof.index]

        fig_prof = go.Figure()
        fig_prof.add_trace(
            go.Scatter(
                x=hour_labels,
                y=prof["wind_mwh"],
                name="Rüzgar Ort.",
                mode="lines",
                line=dict(color=WIND_COLOR, width=2.4),
                fill="tozeroy",
                fillcolor="rgba(5, 150, 105, 0.08)",
                hovertemplate="Rüzgar: %{y:,.0f} MWh<extra></extra>",
            )
        )
        fig_prof.add_trace(
            go.Scatter(
                x=hour_labels,
                y=prof["solar_mwh"],
                name="Güneş Ort.",
                mode="lines",
                line=dict(color=SUN_COLOR, width=2.4),
                fill="tozeroy",
                fillcolor="rgba(234, 179, 8, 0.12)",
                hovertemplate="Güneş: %{y:,.0f} MWh<extra></extra>",
            )
        )
        fig_prof.update_layout(
            height=320,
            showlegend=False,
            hovermode="x unified",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Plus Jakarta Sans, sans-serif", color="#64748B", size=11),
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(tickmode="array", tickvals=hour_labels[::3], showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0", title="Ort. MWh"),
        )

        with st.container(border=True):
            st.markdown(
                """
                <div class="chart-header">
                    <div>
                        <h4 class="chart-title">24 Saatlik Üretim Profili</h4>
                        <p class="chart-sub">Günün saatlerine göre ortalama rüzgar ve güneş dağılımı</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(fig_prof, config={"displayModeBar": False})

    with col_chart_right:
        if clean_df["ts"].dt.date.nunique() > 1:
            with st.container(border=True):
                col_heat_title, col_heat_ctrl = st.columns([1.6, 1], gap="small")
                with col_heat_title:
                    st.markdown(
                        """
                        <div class="chart-header" style="margin-bottom:0;">
                            <div>
                                <h4 class="chart-title">Saatlik Üretim Yoğunluk Haritası</h4>
                                <p class="chart-sub">Günler ve saatler arasındaki üretim yoğunluğu</p>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col_heat_ctrl:
                    heat_src = st.segmented_control(
                        "Kaynak",
                        options=["Rüzgar", "Güneş"],
                        default="Rüzgar",
                        key="heat_src_segmented",
                        label_visibility="collapsed",
                    )
                    if not heat_src:
                        heat_src = "Rüzgar"

                target_col = "wind_mwh" if heat_src == "Rüzgar" else "solar_mwh"

                pivot_m = clean_df.assign(day=clean_df["ts"].dt.date, hr=clean_df["ts"].dt.hour).pivot_table(
                    index="day", columns="hr", values=target_col, aggfunc="mean"
                ).reindex(columns=range(24))

                fig_heat = go.Figure(
                    go.Heatmap(
                        z=pivot_m.to_numpy(),
                        x=[f"{i:02d}:00" for i in range(24)],
                        y=[f"{x.day} {MONTHS[x.month]}" for x in pivot_m.index],
                        colorscale="Greens" if heat_src == "Rüzgar" else "YlOrBr",
                        xgap=2,
                        ygap=2,
                        colorbar=dict(title="MWh", thickness=10),
                        hovertemplate="%{y} · %{x}<br>" + heat_src + ": %{z:,.0f} MWh<extra></extra>",
                    )
                )
                fig_heat.update_layout(
                    height=265,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Plus Jakarta Sans, sans-serif", color="#64748B", size=10),
                    margin=dict(l=0, r=0, t=5, b=0),
                    xaxis=dict(side="top", showgrid=False, tickmode="array", tickvals=[f"{i:02d}:00" for i in range(0, 24, 4)]),
                    yaxis=dict(autorange="reversed", showgrid=False),
                )
                st.plotly_chart(fig_heat, config={"displayModeBar": False})
        else:
            with st.container(border=True):
                st.markdown(
                    """
                    <div style="display:flex; align-items:center; justify-content:center; min-height:300px; text-align:center;">
                        <div style="color:#64748B;">
                            <div style="font-weight:600;">Yoğunluk haritası için en az 2 günlük aralık seçiniz.</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(
        """
        <div class="methodology-note">
            <b>Açıklama ve Metodoloji:</b> Bu panelde sunulan elektrik üretim verileri <b>EPİAŞ Şeffaflık Platformu</b> 
            kaynaklı ulusal şebeke verileridir (TEİAŞ iletim şebekesine bağlı tüm Türkiye toplamıdır). 
            Bölgesel hava durumu değerleri Türkiye geneli ve 7 coğrafi bölgenin anlık atmosferik modellerinden derlenmiştir. 
            Önlenen karbon emisyonu, Türkiye şebekesi ortalama termik ikame faktörü (~0,45 ton CO₂ / MWh) referans alınarak hesaplanmıştır.
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab_ai:
    if train_and_evaluate_models is not None:
        try:
            with st.container(border=True):
                col_pred_title, col_pred_horizon = st.columns([1.4, 1.8], gap="medium")
                with col_pred_title:
                    st.markdown(
                        """
                        <div>
                            <h4 class="chart-title">Yapay Zeka Yenilenebilir Üretim Projeksiyonu</h4>
                            <p class="chart-sub">1 yıllık EPİAŞ saatlik verisi ve astronomik güneş fiziğiyle eğitilen orta ve uzun vadeli üretim projeksiyonu</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with col_pred_horizon:
                    horizon_choice = st.segmented_control(
                        "Tahmin Vadesi",
                        options=[
                            "24 Saatlik (Günlük)",
                            "7 Günlük (Haftalık)",
                            "30 Günlük (Aylık)",
                            "3 Aylık (Çeyreklik)",
                        ],
                        default="24 Saatlik (Günlük)",
                        key="ml_horizon_choice",
                    )

                if not horizon_choice:
                    horizon_choice = "24 Saatlik (Günlük)"

                if horizon_choice == "7 Günlük (Haftalık)":
                    horizon_hours = 168
                    horizon_label = "7 Günlük"
                elif horizon_choice == "30 Günlük (Aylık)":
                    horizon_hours = 720
                    horizon_label = "30 Günlük"
                elif horizon_choice == "3 Aylık (Çeyreklik)":
                    horizon_hours = 2160
                    horizon_label = "3 Aylık"
                else:
                    horizon_hours = 24
                    horizon_label = "24 Saatlik"

                with st.spinner(f"{horizon_label} makine öğrenmesi projeksiyonu hesaplanıyor..."):
                    ml_res = get_cached_ml_results(full_start, full_end, horizon_h=horizon_hours)

                if ml_res and "forecast_df" in ml_res:
                    f_df = ml_res["forecast_df"]
                    p_dt = ml_res.get("peak_hour")
                    if p_dt is not None and hasattr(p_dt, "month"):
                        peak_t_str = f"{p_dt.day:02d} {MONTHS[p_dt.month]} {p_dt.year} - {p_dt.hour:02d}:00"
                    else:
                        peak_t_str = "-"

                    st.markdown(
                        f"""
                        <div class="grid-4">
                            <div class="w-card">
                                <div class="w-card-header"><span>Tahmini Toplam Üretim</span><span style="color:#7C3AED; font-weight:700;">{horizon_label}</span></div>
                                <div class="w-card-val">{tr_format(ml_res['total_all'])} <span class="unit">MWh</span></div>
                                <div class="w-card-sub">Ortalama: ~{tr_format(ml_res.get('avg_total', 0))} MWh/saat</div>
                            </div>
                            <div class="w-card">
                                <div class="w-card-header"><span>Tahmini Rüzgar Üretimi</span><span style="color:#059669; font-weight:700;">%{ml_res.get('wind_pct', 0)} Pay</span></div>
                                <div class="w-card-val">{tr_format(ml_res.get('total_wind', 0))} <span class="unit">MWh</span></div>
                                <div class="w-card-sub">Ortalama: ~{tr_format(ml_res.get('avg_wind', 0))} MWh/saat</div>
                            </div>
                            <div class="w-card">
                                <div class="w-card-header"><span>Tahmini Güneş Üretimi</span><span style="color:#D97706; font-weight:700;">%{ml_res.get('solar_pct', 0)} Pay</span></div>
                                <div class="w-card-val">{tr_format(ml_res.get('total_solar', 0))} <span class="unit">MWh</span></div>
                                <div class="w-card-sub">Ortalama: ~{tr_format(ml_res.get('avg_solar', 0))} MWh/saat</div>
                            </div>
                            <div class="w-card">
                                <div class="w-card-header"><span>Beklenen Zirve Üretim</span><span style="color:#2563EB; font-weight:700;">Tepe Saati</span></div>
                                <div class="w-card-val">{tr_format(ml_res.get('peak_val', 0))} <span class="unit">MWh</span></div>
                                <div class="w-card-sub">En yüksek saat: {peak_t_str}</div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if horizon_hours == 24:
                        plot_df = f_df.copy()
                        plot_x = [t.strftime("%H:00") for t in plot_df["ts"]]
                        hover_unit = "MWh/saat"
                        x_label = "Gelecek 24 Saat (Saatlik)"
                    elif horizon_hours == 168:
                        plot_df = f_df.copy()
                        plot_x = [f"{t.day:02d} {MONTHS[t.month]} {t.hour:02d}:00" for t in plot_df["ts"]]
                        hover_unit = "MWh/saat"
                        x_label = "Gelecek 7 Gün (Saatlik)"
                    elif horizon_hours == 720:
                        plot_df = f_df.resample("1D", on="ts").mean().reset_index()
                        plot_x = [f"{t.day:02d} {MONTHS[t.month]}" for t in plot_df["ts"]]
                        hover_unit = "Günlük Ort. MWh/saat"
                        x_label = "Gelecek 30 Gün (Günlük Ortalama)"
                    elif horizon_hours == 2160:
                        plot_df = f_df.resample("5D", on="ts").mean().reset_index()
                        plot_x = [f"{t.day:02d} {MONTHS[t.month]}" for t in plot_df["ts"]]
                        hover_unit = "5 Günlük Ort. MWh/saat"
                        x_label = "Gelecek 3 Aylık Projeksiyon (5 Günlük Dönemler)"
                    elif horizon_hours == 4320:
                        plot_df = f_df.resample("10D", on="ts").mean().reset_index()
                        plot_x = [f"{t.day:02d} {MONTHS[t.month]}" for t in plot_df["ts"]]
                        hover_unit = "10 Günlük Dekad Ort. MWh/saat"
                        x_label = "Gelecek 6 Aylık Projeksiyon (10 Günlük Dekad Aralıkları)"
                    else:
                        plot_df = f_df.resample("10D", on="ts").mean().reset_index()
                        plot_x = [f"{t.day:02d} {MONTHS[t.month]}" for t in plot_df["ts"]]
                        hover_unit = "10 Günlük Dekad Ort. MWh/saat"
                        x_label = "Gelecek 1 Yıllık Projeksiyon (10 Günlük Dekad Aralıkları)"

                    fig_ml = go.Figure()
                    fig_ml.add_trace(
                        go.Scatter(
                            x=plot_x,
                            y=plot_df["wind_pred"],
                            name="Tahmini Rüzgar (Yeşil)",
                            mode="lines+markers" if horizon_hours > 720 else "lines",
                            line=dict(color=WIND_COLOR, width=2.2),
                            marker=dict(size=5) if horizon_hours > 720 else None,
                            fill="tozeroy",
                            fillcolor="rgba(5, 150, 105, 0.08)",
                            hovertemplate=f"Tahmini Rüzgar: %{{y:,.0f}} {hover_unit}<extra></extra>",
                        )
                    )
                    fig_ml.add_trace(
                        go.Scatter(
                            x=plot_x,
                            y=plot_df["solar_pred"],
                            name="Tahmini Güneş (Turuncu)",
                            mode="lines+markers" if horizon_hours > 720 else "lines",
                            line=dict(color=SUN_COLOR, width=2.2),
                            marker=dict(size=5) if horizon_hours > 720 else None,
                            fill="tozeroy",
                            fillcolor="rgba(234, 179, 8, 0.14)",
                            hovertemplate=f"Tahmini Güneş: %{{y:,.0f}} {hover_unit}<extra></extra>",
                        )
                    )
                    fig_ml.add_trace(
                        go.Scatter(
                            x=plot_x,
                            y=plot_df["total_pred"],
                            name="Tahmini Toplam Yenilenebilir",
                            mode="lines",
                            line=dict(color="#4F46E5", width=2.2, dash="dash"),
                            hovertemplate=f"Tahmini Toplam: %{{y:,.0f}} {hover_unit}<extra></extra>",
                        )
                    )

                    fig_ml.update_layout(
                        height=360,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1,
                            font=dict(family="DM Sans, sans-serif", size=11, color="#0F2417"),
                        ),
                        hovermode="x unified",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="DM Sans, sans-serif", color="#64748B", size=11),
                        margin=dict(l=0, r=0, t=25, b=0),
                        xaxis=dict(showgrid=True, gridcolor="#E2E8F0", title=x_label),
                        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", title="Tahmini Üretim (MWh)"),
                    )

                    st.plotly_chart(fig_ml, config={"displayModeBar": False})

                    col_f_down_left, col_f_down_right = st.columns([1, 1], gap="medium")
                    with col_f_down_left:
                        st.download_button(
                            label=f"{horizon_label} Saatlik Tahmin Tablosunu İndir (CSV)",
                            data=f_df.to_csv(index=False).encode("utf-8-sig"),
                            file_name=f"{horizon_label.lower().replace(' ', '_')}_saatlik_projeksiyon.csv",
                            mime="text/csv",
                            width="stretch",
                        )
                    with col_f_down_right:
                        st.caption(f"Gelecek {horizon_label.lower()} boyunca tüm saatlik rüzgar, güneş ve toplam üretim projeksiyon dökümü.")

                    st.markdown(
                        f"""
                        <div style="font-size:0.78rem; color:#475569; background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:10px 14px; margin-top:8px; line-height:1.5;">
                            <b>Projeksiyon Metodolojisi & Karar Destek:</b> Model, 1 yıllık (8.894 saat) tarihsel EPİAŞ verisi ve astronomik güneş deklinasyon fiziği kullanarak 
                            {horizon_label.lower()} vade boyunca üretim projeksiyonunu hesaplar. Uzun vadelerde (3 Ay, 6 Ay, 1 Yıl) grafik akıcılığı için 
                            10 günlük dekad dönemleri şeklinde gruplanır; CSV çıktısında ise tüm saatlik detaylar yer alır.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        except Exception as err:
            logger.exception("Makine tahmini hatası: %s", err)
            st.error(f"Tahmin hesaplanırken durum oluştu: {err}")

with tab_esg:
    if simulate_enterprise_esg is not None and ENTERPRISE_PROFILES:
        with st.container(border=True):
            col_esg_h, col_esg_sel = st.columns([1.5, 1], gap="medium")
            with col_esg_h:
                st.markdown(
                    """
                    <div>
                        <h4 class="chart-title">COP31 Kurumsal Sürdürülebilirlik (ESG) & Fabrika Karbon Raporu</h4>
                        <p class="chart-sub">Şirketinizin veya fabrikanızın elektrik tüketimini ulusal rüzgar ve güneş payı ile eşleştirerek Kapsam 2 (Scope 2) karbon raporunu hesaplayın</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_esg_sel:
                esg_profile_choice = st.selectbox(
                    "Tesis / Tüketim Profili Seçimi",
                    options=list(ENTERPRISE_PROFILES.keys()) + ["Özel CSV Dosyası Yükle"],
                    index=0,
                    key="esg_profile_selector",
                )

            custom_upload_df = None
            if esg_profile_choice == "Özel CSV Dosyası Yükle":
                uploaded_file = st.file_uploader("Fabrika Saatlik Tüketim CSV'si Yükleyin (Sütun: 'tuketim_mwh')", type=["csv"])
                if uploaded_file is not None:
                    try:
                        custom_upload_df = pd.read_csv(uploaded_file)
                    except Exception:
                        st.error("CSV dosyası okunamadı. Lütfen biçimi kontrol edin.")

            esg_sim = simulate_enterprise_esg(esg_profile_choice, clean_df, custom_upload_df)

            if esg_sim:
                st.markdown(
                    f"""
                    <div class="grid-4">
                        <div class="w-card">
                            <div class="w-card-header"><span>Toplam Fabrika Tüketimi</span><span style="color:#2563EB; font-weight:700;">Dönem</span></div>
                            <div class="w-card-val">{tr_format(esg_sim['total_consumed_mwh'])} <span class="unit">MWh</span></div>
                            <div class="w-card-sub">{esg_profile_choice} profil tüketimi</div>
                        </div>
                        <div class="w-card">
                            <div class="w-card-header"><span>Temiz Enerji Tedariği</span><span style="color:#059669; font-weight:700;">Şebeke Payı</span></div>
                            <div class="w-card-val">%{tr_format(esg_sim['clean_share_pct'], 1)}</div>
                            <div class="w-card-sub">{tr_format(esg_sim['clean_consumed_mwh'])} MWh rüzgar ve güneşten karşılandı</div>
                        </div>
                        <div class="w-card">
                            <div class="w-card-header"><span>Önlenen Karbon Emisyonu</span><span style="color:#0D9488; font-weight:700;">Tasarruf</span></div>
                            <div class="w-card-val">{tr_format(esg_sim['avoided_co2_tons'])} <span class="unit">ton CO₂</span></div>
                            <div class="w-card-sub">Termik ikamesi (~0,45 tCO₂/MWh)</div>
                        </div>
                        <div class="w-card">
                            <div class="w-card-header"><span>COP31 Yeşil Enerji Skoru</span><span style="color:#7C3AED; font-weight:700;">Kapsam 2</span></div>
                            <div class="w-card-val" style="font-size:1.15rem;">{esg_sim['esg_grade']}</div>
                            <div class="w-card-sub">Kapsam 2 Yoğunluğu: {esg_sim['scope2_ci']} gCO₂/kWh</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                comp_data = esg_sim["comp_df"]
                fig_esg = go.Figure()
                fig_esg.add_trace(
                    go.Scatter(
                        x=comp_data["ts"],
                        y=comp_data["factory_mwh"],
                        name="Tesis Toplam Tüketimi (MWh)",
                        mode="lines",
                        line=dict(color="#64748B", width=2),
                        hovertemplate="Tüketim: %{y:,.1f} MWh<extra></extra>",
                    )
                )
                fig_esg.add_trace(
                    go.Scatter(
                        x=comp_data["ts"],
                        y=comp_data["clean_mwh"],
                        name="Şebekeden Karşılanan Rüzgar + Güneş (MWh)",
                        mode="lines",
                        line=dict(color="#059669", width=2.2),
                        fill="tozeroy",
                        fillcolor="rgba(5, 150, 105, 0.15)",
                        hovertemplate="Temiz Enerji Payı: %{y:,.1f} MWh<extra></extra>",
                    )
                )
                fig_esg.update_layout(
                    height=280,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#0F2417"),
                    ),
                    hovermode="x unified",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Plus Jakarta Sans, sans-serif", color="#64748B", size=11),
                    margin=dict(l=0, r=0, t=25, b=0),
                    xaxis=dict(showgrid=True, gridcolor="#E2E8F0"),
                    yaxis=dict(showgrid=True, gridcolor="#E2E8F0", title="MWh"),
                )
                st.plotly_chart(fig_esg, config={"displayModeBar": False})

                export_rows = []
                for _, r in comp_data.iterrows():
                    f_val = float(r["factory_mwh"])
                    c_val = float(r["clean_mwh"])
                    export_rows.append({
                        "Tarih_Saat": r["ts"].strftime("%Y-%m-%d %H:%M"),
                        "Tesis_Tuketimi_MWh": round(f_val, 2),
                        "Yenilenebilir_Karsilanan_MWh": round(c_val, 2),
                        "Fosil_Sebeke_Tuketimi_MWh": round(max(0.0, f_val - c_val), 2),
                        "Temiz_Enerji_Payi_Yuzde": round(c_val / f_val * 100, 1) if f_val > 0 else 0.0,
                    })
                df_audit = pd.DataFrame(export_rows)
                summary_header = (
                    f"# ========================================================\n"
                    f"# COP31 KURUMSAL KAPSAM 2 (SCOPE 2) TAHMİNİ KARBON HESABI\n# YASAL UYARI: Bu rapor simülasyon ve karar destek amaçlıdır;\n# bağımsız akredite denetim belgesi veya resmi beyan yerine geçmez.\n"
                    f"# Tesis / Tüketim Profili: {esg_profile_choice}\n"
                    f"# Toplam Tüketim: {esg_sim['total_consumed_mwh']} MWh\n"
                    f"# Temiz Enerjiden Karşılanan: {esg_sim['clean_consumed_mwh']} MWh (%{esg_sim['clean_share_pct']})\n"
                    f"# Önlenen Karbon Emisyonu: {esg_sim['avoided_co2_tons']} ton CO2\n"
                    f"# Kapsam 2 Karbon Yoğunluğu: {esg_sim['scope2_ci']} gCO2/kWh\n"
                    f"# COP31 ESG Derecesi: {esg_sim['esg_grade']}\n"
                    f"# Kaynak: EPİAŞ Şeffaflık Platformu & GHG Protocol Scope 2\n"
                    f"# ========================================================\n"
                )
                csv_audit_data = summary_header + df_audit.to_csv(index=False)

                col_down_left, col_down_right = st.columns([1, 1], gap="medium")
                with col_down_left:
                    st.download_button(
                        label="Kapsam 2 Karbon Hesabını İndir (Simülasyon CSV)",
                        data=csv_audit_data.encode("utf-8-sig"),
                        file_name=f"COP31_Kapsam2_Karbon_Karnesi_{esg_profile_choice.replace(' ', '_')}.csv",
                        mime="text/csv",
                        width="stretch",
                    )
                with col_down_right:
                    st.caption("İndirilen dosya karar destek ve simülasyon amaçlı tahmini hesaplamadır; resmi denetim belgesi niteliği taşımaz.")

                st.markdown(
                    """
                    <div style="font-size:0.78rem; color:#375240; background:#EAF2EC; border:1px solid #DCE7DE; border-radius:8px; padding:12px 16px; margin-top:8px; line-height:1.6;">
                        <b>Metodoloji & Yasal Sorumluluk Reddi (Disclaimer):</b> Şirket veya fabrikanın saatlik elektrik tüketimi, 
                        EPİAŞ ulusal iletim şebekesindeki o saatin rüzgar ve güneş payı ile GHG Protocol Scope 2 pazar bazlı yaklaşımına göre eşleştirilerek simüle edilmiştir. 
                        Bu sonuçlar kurumsal iç sürdürülebilirlik planlaması ve enerji optimizasyonu için karar destek amaçlı olup, 
                        bağımsız denetimden geçmiş resmi ISO 14064 doğrulama belgesi yerine geçmez.
                        <br><br>
                        <b>Lisanssız Güneş Notu:</b> EPİAŞ üretim serisi lisanssız (çatı ve öz tüketim) güneş üretimini tam yansıtmayabilir. 
                        Bu durum gerçek temiz enerji payının gösterilenden bir miktar daha yüksek, şebeke karbon yoğunluğunun ise daha düşük olmasına yol açabilir.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

st.markdown(
    """
    <div style="margin-top: 50px; margin-bottom: 24px; padding-top: 22px; border-top: 1px solid #DCE7DE; text-align: center;">
        <div style="font-size: 1.05rem; font-weight: 700; color: #172B22; letter-spacing: 0.4px;">
            Emre Altındağ & Kaan Bölek
        </div>
        <div style="font-size: 0.78rem; color: #5A7163; margin-top: 6px;">
            Enerji Nabzı · Türkiye Rüzgar ve Güneş Enerjisi İzleme ve Yapay Zeka ile Tahmin Platformu
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
