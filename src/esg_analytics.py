from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
import streamlit as st

ENTERPRISE_PROFILES: Dict[str, Dict[str, Any]] = {
    "Organize Sanayi Fabrikası (OSB)": {
        "desc": "Orta ölçekli üretim tesisi (Gündüz yoğun, gece asgari vardiya)",
        "base_mwh": 14.0,
        "day_factor": 1.5,
    },
    "Veri Merkezi (Datacenter 7/24)": {
        "desc": "Kesintisiz soğutma ve sunucu yükü (7/24 sabit baz yük tüketimi)",
        "base_mwh": 8.5,
        "day_factor": 1.05,
    },
    "Ticari Plaza ve AVM": {
        "desc": "İş merkezi ve alışveriş kompleksi (10:00 - 22:00 arası tepe tüketim)",
        "base_mwh": 4.2,
        "day_factor": 2.2,
    },
}

def calculate_grid_carbon_intensity(
    df: pd.DataFrame,
    threshold_pct: float = 15.0,
) -> Dict[str, Any]:
    if df.empty:
        return {
            "carbon_intensity": 510,
            "renewable_share": 14.0,
            "threshold_pct": threshold_pct,
            "is_green_window": False,
            "status_title": "Standart Şebeke Yoğunluğu",
            "status_desc": "Termik santraller devrede.",
            "recommendation": "Enerji tüketiminde standart şebeke tarifesi geçerli.",
        }

    last_row = df.iloc[-1]
    total = float(last_row["total_mwh"]) if pd.notna(last_row["total_mwh"]) and last_row["total_mwh"] > 0 else 35000.0
    wind = float(last_row["wind_mwh"]) if pd.notna(last_row["wind_mwh"]) else 0.0
    solar = float(last_row["solar_mwh"]) if pd.notna(last_row["solar_mwh"]) else 0.0
    pair = wind + solar

    share = min(1.0, max(0.0, pair / total))
    share_pct = round(share * 100, 1)

    ci = round(560.0 * (1.0 - share) + 15.0 * share, 0)

    is_green = share_pct >= threshold_pct

    if is_green:
        status_title = "Aktif Yeşil Saat (Düşük Karbon Penceresi)"
        status_desc = f"Şebekede temiz enerji payı %{share_pct} seviyesinde (Yeşil Saat eşiği: ≥%{threshold_pct}). Fosil yakıt ikamesi devrede."
        recommendation = "Fabrikalar, organize sanayi fırınları, batarya şarjı ve elektrikli araç şarjı için en temiz zaman dilimi."
    else:
        status_title = "Standart Şebeke Yoğunluğu"
        status_desc = f"Şebekede temiz enerji payı %{share_pct} (Yeşil Saat eşiği: ≥%{threshold_pct}). Baz yük termik santraller tarafından karşılanıyor."
        recommendation = "Enerji yoğun sanayi yüklerinin rüzgâr ve güneşin arttığı saatlere kaydırılması önerilir."

    return {
        "carbon_intensity": int(ci),
        "renewable_share": share_pct,
        "threshold_pct": threshold_pct,
        "is_green_window": is_green,
        "status_title": status_title,
        "status_desc": status_desc,
        "recommendation": recommendation,
    }

def simulate_enterprise_esg(
    profile_name: str,
    df: pd.DataFrame,
    custom_df: Optional[pd.DataFrame] = None,
) -> Dict[str, Any]:
    if df.empty:
        return {}

    work_df = df.copy()
    if "ts" not in work_df.columns:
        work_df["ts"] = pd.to_datetime(work_df["timestamp"])

    work_df = work_df.sort_values("ts").reset_index(drop=True)
    n_hours = len(work_df)

    if custom_df is not None and not custom_df.empty and "tuketim_mwh" in custom_df.columns:
        consumption = custom_df["tuketim_mwh"].values[:n_hours]
        if len(consumption) < n_hours:
            consumption = np.pad(consumption, (0, n_hours - len(consumption)), mode="edge")
    else:
        prof = ENTERPRISE_PROFILES.get(profile_name, ENTERPRISE_PROFILES["Organize Sanayi Fabrikası (OSB)"])
        base = prof["base_mwh"]
        factor = prof["day_factor"]
        hours = work_df["ts"].dt.hour.values
        shift_mult = np.where((hours >= 8) & (hours <= 19), factor, 1.0)
        rng = np.random.default_rng(42)
        noise = rng.uniform(0.92, 1.08, size=n_hours)
        consumption = base * shift_mult * noise

    clean_series = work_df[["wind_mwh", "solar_mwh"]].sum(axis=1, min_count=1).fillna(0)
    total_series = work_df["total_mwh"].fillna(1)
    grid_share = np.clip(clean_series / total_series, 0.0, 1.0).values

    clean_consumed = consumption * grid_share
    total_consumed = float(np.sum(consumption))
    total_clean = float(np.sum(clean_consumed))
    clean_pct = round((total_clean / total_consumed * 100), 1) if total_consumed > 0 else 0.0

    avoided_co2 = round(total_clean * 0.45, 1)

    scope2_ci = round(560.0 * (1.0 - clean_pct / 100.0) + 15.0 * (clean_pct / 100.0), 0)

    if clean_pct >= 20.0:
        esg_grade = "A+ (Üst Düzey Yeşil Tedarik)"
    elif clean_pct >= 14.0:
        esg_grade = "A (İyi Düzey Yeşil Tedarik)"
    elif clean_pct >= 10.0:
        esg_grade = "B+ (Gelişmekte Olan Tedarik)"
    else:
        esg_grade = "B (Standart Şebeke Tedariği)"

    comp_df = pd.DataFrame({
        "ts": work_df["ts"],
        "factory_mwh": consumption,
        "clean_mwh": clean_consumed,
    })

    return {
        "profile_name": profile_name,
        "total_consumed_mwh": round(total_consumed, 1),
        "clean_consumed_mwh": round(total_clean, 1),
        "clean_share_pct": clean_pct,
        "avoided_co2_tons": avoided_co2,
        "scope2_ci": int(scope2_ci),
        "esg_grade": esg_grade,
        "comp_df": comp_df,
    }
