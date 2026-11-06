from typing import Any, Dict
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
import streamlit as st

def calculate_solar_elevation(dt: pd.Timestamp, lat: float = 39.0) -> float:
    doy = dt.dayofyear
    decl = np.radians(23.45 * np.sin(np.radians(360.0 / 365.0 * (284 + doy))))
    lat_r = np.radians(lat)

    hour_float = dt.hour + dt.minute / 60.0
    hour_angle = np.radians((hour_float - 12.0) * 15.0)

    sin_elev = np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(hour_angle)
    sin_elev = np.clip(sin_elev, -1.0, 1.0)
    elevation = np.degrees(np.arcsin(sin_elev))
    return float(elevation)

def create_feature_matrix(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    d = df.copy()
    if "ts" not in d.columns:
        d["ts"] = pd.to_datetime(d["timestamp"])

    d["hour"] = d["ts"].dt.hour
    d["dayofweek"] = d["ts"].dt.dayofweek
    d["sin_hour"] = np.sin(2 * np.pi * d["hour"] / 24.0)
    d["cos_hour"] = np.cos(2 * np.pi * d["hour"] / 24.0)

    s_elev = [calculate_solar_elevation(t) for t in d["ts"]]
    d["solar_elev"] = s_elev
    d["solar_flux_pot"] = np.maximum(0.0, np.sin(np.radians(s_elev)))

    d["lag_1"] = d[target_col].shift(1)
    d["lag_2"] = d[target_col].shift(2)
    d["lag_24"] = d[target_col].shift(24)
    d["rolling_mean_6"] = d[target_col].shift(1).rolling(6).mean()
    d["rolling_mean_24"] = d[target_col].shift(1).rolling(24).mean()
    return d.dropna().reset_index(drop=True)

def train_and_evaluate_models(
    historical_df: pd.DataFrame,
    horizon_hours: int = 24,
    *args,
    **kwargs,
) -> Dict[str, Any]:
    if historical_df.empty or len(historical_df) < 120:
        return {}

    df = historical_df.copy()
    if "ts" not in df.columns:
        df["ts"] = pd.to_datetime(df["timestamp"])

    feature_cols = [
        "hour",
        "dayofweek",
        "sin_hour",
        "cos_hour",
        "solar_elev",
        "solar_flux_pot",
        "lag_1",
        "lag_2",
        "lag_24",
        "rolling_mean_6",
        "rolling_mean_24",
    ]

    wind_features = create_feature_matrix(df, "wind_mwh")
    X_w = wind_features[feature_cols].values
    y_w = wind_features["wind_mwh"].values
    wind_model = HistGradientBoostingRegressor(max_iter=90, random_state=42)
    wind_model.fit(X_w, y_w)

    solar_features = create_feature_matrix(df, "solar_mwh")
    X_s = solar_features[feature_cols].values
    y_s = solar_features["solar_mwh"].values
    solar_model = HistGradientBoostingRegressor(max_iter=90, random_state=42)
    solar_model.fit(X_s, y_s)

    last_ts = df["ts"].iloc[-1]
    future_times = [last_ts + pd.Timedelta(hours=i + 1) for i in range(horizon_hours)]

    hrs = np.array([t.hour for t in future_times], dtype=np.float64)
    dows = np.array([t.dayofweek for t in future_times], dtype=np.float64)
    sin_hrs = np.sin(2.0 * np.pi * hrs / 24.0)
    cos_hrs = np.cos(2.0 * np.pi * hrs / 24.0)
    s_elevs = np.array([calculate_solar_elevation(t) for t in future_times], dtype=np.float64)
    s_fluxes = np.maximum(0.0, np.sin(np.radians(s_elevs)))

    w_history = list(df["wind_mwh"].values)
    wind_predictions = []
    feat_w = np.empty((1, 11), dtype=np.float64)
    for i in range(horizon_hours):
        feat_w[0, 0] = hrs[i]
        feat_w[0, 1] = dows[i]
        feat_w[0, 2] = sin_hrs[i]
        feat_w[0, 3] = cos_hrs[i]
        feat_w[0, 4] = s_elevs[i]
        feat_w[0, 5] = s_fluxes[i]
        feat_w[0, 6] = w_history[-1]
        feat_w[0, 7] = w_history[-2]
        feat_w[0, 8] = w_history[-24]
        feat_w[0, 9] = np.mean(w_history[-6:])
        feat_w[0, 10] = np.mean(w_history[-24:])

        p_val = float(np.clip(wind_model.predict(feat_w)[0], 400.0, 11000.0))
        wind_predictions.append(p_val)
        w_history.append(p_val)

    s_history = list(df["solar_mwh"].values)
    solar_predictions = []
    feat_s = np.empty((1, 11), dtype=np.float64)
    for i in range(horizon_hours):
        s_elev = s_elevs[i]
        if s_elev <= 0:
            p_val = 0.0
        else:
            feat_s[0, 0] = hrs[i]
            feat_s[0, 1] = dows[i]
            feat_s[0, 2] = sin_hrs[i]
            feat_s[0, 3] = cos_hrs[i]
            feat_s[0, 4] = s_elev
            feat_s[0, 5] = s_fluxes[i]
            feat_s[0, 6] = s_history[-1]
            feat_s[0, 7] = s_history[-2]
            feat_s[0, 8] = s_history[-24]
            feat_s[0, 9] = np.mean(s_history[-6:])
            feat_s[0, 10] = np.mean(s_history[-24:])

            raw_p = float(solar_model.predict(feat_s)[0])
            p_val = float(np.clip(raw_p, 0.0, 4200.0))

        solar_predictions.append(p_val)
        s_history.append(p_val)

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
