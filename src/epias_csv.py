"""Readers for the cleaned EPİAŞ CSV files."""

from datetime import date
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _find_file(preferred_names: list[str]) -> Path:
    for name in preferred_names:
        p = ROOT / name
        if p.exists():
            return p
    return ROOT / preferred_names[0]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {}
    for col in df.columns:
        c_low = col.lower()
        if "toplam" in c_low and "yenilenebilir" not in c_low:
            col_map[col] = "total_mwh"
        elif "rüzgar" in c_low or "ruzgar" in c_low:
            col_map[col] = "wind_mwh"
        elif "güneş" in c_low or "gunes" in c_low:
            col_map[col] = "solar_mwh"
        elif "tarih" in c_low:
            col_map[col] = "Tarih"
        elif "saat" in c_low:
            col_map[col] = "Saat"
    return df.rename(columns=col_map)


def load_generation_data(start_date: date, end_date: date) -> pd.DataFrame:
    """Read the hourly file and return the dashboard's normalized schema."""
    gen_file = _find_file(["temiz_epias_uretim (1).csv", "temiz_epias_uretim.csv"])
    raw = pd.read_csv(gen_file, encoding="utf-8-sig", dtype={"Tarih": "string"})
    raw = _normalize_columns(raw)

    required = {"Tarih", "Saat", "total_mwh", "wind_mwh", "solar_mwh"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"EPİAŞ üretim CSV'sinde sütun eksik: {', '.join(sorted(missing))}")

    date_text = raw["Tarih"].str.replace(r"\.0$", "", regex=True).str.zfill(8)
    local_time = pd.to_datetime(
        date_text + " " + raw["Saat"].astype("string"),
        format="%d%m%Y %H:%M",
        errors="coerce",
    )
    raw["timestamp"] = local_time.dt.tz_localize("Europe/Istanbul")
    clean = raw[["timestamp", "wind_mwh", "solar_mwh", "total_mwh"]].copy()
    for column in ("wind_mwh", "solar_mwh", "total_mwh"):
        clean[column] = pd.to_numeric(clean[column], errors="coerce")

    start = pd.Timestamp(start_date, tz="Europe/Istanbul")
    end = pd.Timestamp(end_date + pd.Timedelta(days=1), tz="Europe/Istanbul")
    clean = clean.loc[(clean["timestamp"] >= start) & (clean["timestamp"] < end)]
    clean = clean.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    if clean.empty:
        return pd.DataFrame(columns=["timestamp", "wind_mwh", "solar_mwh", "total_mwh"])
    return clean


def get_dataset_bounds() -> Tuple[date, date]:
    """Return the absolute earliest and latest complete date in the CSV."""
    gen_file = _find_file(["temiz_epias_uretim (1).csv", "temiz_epias_uretim.csv"])
    raw = pd.read_csv(gen_file, encoding="utf-8-sig", dtype={"Tarih": "string"})
    raw = _normalize_columns(raw)

    date_text = raw["Tarih"].str.replace(r"\.0$", "", regex=True).str.zfill(8)
    timestamps = pd.to_datetime(
        date_text + " " + raw["Saat"].astype("string"),
        format="%d%m%Y %H:%M",
        errors="coerce",
    )
    local_dates = timestamps.dt.date
    valid_values = raw[["total_mwh", "wind_mwh", "solar_mwh"]].apply(pd.to_numeric, errors="coerce").notna().all(axis=1)
    available = pd.DataFrame({"local_date": local_dates, "hour": timestamps.dt.hour, "valid": valid_values})
    available = available.dropna(subset=["local_date", "hour"])
    daily = available.groupby("local_date").agg(
        unique_hours=("hour", "nunique"),
        valid_hours=("valid", "sum"),
    )
    complete_days = daily.index[(daily["unique_hours"] == 24) & (daily["valid_hours"] == 24)].sort_values()
    if len(complete_days) == 0:
        raise ValueError("CSV dosyasında 24 saatlik eksiksiz bir gün bulunamadı.")
    return complete_days[0], complete_days[-1]


def get_latest_complete_window(days: int = 30) -> tuple[date, date]:
    """Return the latest window ending on the last complete day in the CSV."""
    earliest, end = get_dataset_bounds()
    start = max(earliest, end - pd.Timedelta(days=days - 1))
    return start, end


def load_hourly_profile() -> pd.DataFrame:
    """Read the prepared 24-hour average profile."""
    prof_file = _find_file(["saatlik_profil (1).csv", "saatlik_profil.csv"])
    raw = pd.read_csv(prof_file, encoding="utf-8-sig")
    raw = _normalize_columns(raw)

    required = {"Saat", "wind_mwh", "solar_mwh"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Saatlik profil CSV'sinde sütun eksik: {', '.join(sorted(missing))}")

    profile = raw.rename(columns={"Saat": "hour"})[["hour", "wind_mwh", "solar_mwh"]].copy()
    profile["hour"] = profile["hour"].astype(str).str.slice(0, 2).astype(int)
    for column in ("wind_mwh", "solar_mwh"):
        profile[column] = pd.to_numeric(profile[column], errors="coerce")
    return profile.dropna(subset=["wind_mwh", "solar_mwh"]).sort_values("hour").reset_index(drop=True)
