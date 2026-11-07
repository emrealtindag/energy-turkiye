from typing import Any, Dict
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
import streamlit as st

def calculate_solar_elevation(dt: pd.Timestamp, lat: float = 39.0) -> float:
    doy = dt.dayofyear
    decl = np.radians(23.45 * np.sin(np.radians(360.0 / 365.0 * (284 + doy))))
    lat_r = np.radians(lat)
    hour_float = dt.hour + dt.minute / 60.0
    hour_angle = np.radians((hour_float - 12.0) * 15.0)
    sin_elev = np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(hour_angle)
    sin_elev = np.clip(sin_elev, -1.0, 1.0)
    return float(np.degrees(np.arcsin(sin_elev)))

def train_and_evaluate_models(
    historical_df: pd.DataFrame,
    horizon_hours: int = 24,
    *args,
    **kwargs,
) -> Dict[str, Any]:
    if historical_df.empty or len(historical_df) < 120:
        return {}

    train = historical_df.tail(720).copy()
    if "ts" not in train.columns:
        train["ts"] = pd.to_datetime(train["timestamp"])

    train["hour"] = train["ts"].dt.hour
    train["sin_h"] = np.sin(2.0 * np.pi * train["hour"] / 24.0)
    train["cos_h"] = np.cos(2.0 * np.pi * train["hour"] / 24.0)

    doy = train["ts"].dt.dayofyear.values
    decl = np.radians(23.45 * np.sin(np.radians(360.0 / 365.0 * (284 + doy))))
    lat_r = np.radians(39.0)
    hour_float = train["hour"].values + train["ts"].dt.minute.values / 60.0
    hour_angle = np.radians((hour_float - 12.0) * 15.0)
    sin_elev = np.clip(np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(hour_angle), -1.0, 1.0)
    train["solar_flux"] = np.maximum(0.0, sin_elev)

    train["w_lag24"] = train["wind_mwh"].shift(24)
    train["w_roll6"] = train["wind_mwh"].shift(1).rolling(6).mean()
    train["s_lag24"] = train["solar_mwh"].shift(24)

    clean_train = train.dropna()
    if len(clean_train) < 48:
        return {}

    X_w = clean_train[["sin_h", "cos_h", "w_lag24", "w_roll6"]].values
    y_w = clean_train["wind_mwh"].values
    w_model = Ridge(alpha=1.0)
    w_model.fit(X_w, y_w)

    X_s = clean_train[["solar_flux", "s_lag24"]].values
    y_s = clean_train["solar_mwh"].values
    s_model = Ridge(alpha=1.0)
    s_model.fit(X_s, y_s)

    last_ts = train["ts"].iloc[-1]
    future_times = [last_ts + pd.Timedelta(hours=i + 1) for i in range(horizon_hours)]

    w_history = list(historical_df["wind_mwh"].tail(48).values)
    s_history = list(historical_df["solar_mwh"].tail(48).values)

    wind_predictions = []
    solar_predictions = []

    for i in range(horizon_hours):
        t = future_times[i]
        h = t.hour
        sin_h = np.sin(2.0 * np.pi * h / 24.0)
        cos_h = np.cos(2.0 * np.pi * h / 24.0)

        d = t.dayofyear
        dec = np.radians(23.45 * np.sin(np.radians(360.0 / 365.0 * (284 + d))))
        ha = np.radians((h - 12.0) * 15.0)
        se = np.clip(np.sin(lat_r) * np.sin(dec) + np.cos(lat_r) * np.cos(dec) * np.cos(ha), -1.0, 1.0)
        elev = np.degrees(np.arcsin(se))

        feat_w = np.array([[sin_h, cos_h, w_history[-24], np.mean(w_history[-6:])]])
        p_w = float(np.clip(w_model.predict(feat_w)[0], 400.0, 11000.0))
        wind_predictions.append(p_w)
        w_history.append(p_w)

        if elev <= 0.0:
            p_s = 0.0
        else:
            flux = max(0.0, float(se))
            feat_s = np.array([[flux, s_history[-24]]])
            p_s = float(np.clip(s_model.predict(feat_s)[0], 0.0, 4500.0))
        solar_predictions.append(p_s)
        s_history.append(p_s)

    forecast_df = pd.DataFrame({
        "ts": future_times,
        "wind_pred": wind_predictions,
        "solar_pred": solar_predictions,
        "total_pred": [w + s for w, s in zip(wind_predictions, solar_predictions)],
    })

    total_w = float(sum(wind_predictions))
    total_s = float(sum(solar_predictions))
    total_all = total_w + total_s
    w_pct = round(total_w / total_all * 100, 1) if total_all > 0 else 0.0
    s_pct = round(total_s / total_all * 100, 1) if total_all > 0 else 0.0

    peak_idx = int(np.argmax(forecast_df["total_pred"]))
    peak_hour = future_times[peak_idx]
    peak_val = float(forecast_df["total_pred"].iloc[peak_idx])

    return {
        "horizon_hours": horizon_hours,
        "forecast_df": forecast_df,
        "total_all": round(total_all, 0),
        "total_24h": round(total_all, 0),
        "total_wind": round(total_w, 0),
        "total_solar": round(total_s, 0),
        "wind_pct": w_pct,
        "solar_pct": s_pct,
        "peak_hour": peak_hour,
        "peak_val": round(peak_val, 0),
        "avg_wind": round(total_w / horizon_hours, 0),
        "avg_solar": round(total_s / horizon_hours, 0),
        "avg_total": round(total_all / horizon_hours, 0),
    }
