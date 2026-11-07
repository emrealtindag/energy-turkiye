from typing import Any, Dict
import numpy as np
import pandas as pd
import requests
import streamlit as st

REGIONS: Dict[str, Dict[str, Any]] = {
    "Tüm Türkiye (Ortalama)": {"lat": 39.0, "lon": 35.0, "desc": "Ulusal Ağırlıklı Ortalama", "base_wind": 23.5, "base_temp": 12.5},
    "Marmara Bölgesi": {"lat": 40.5, "lon": 28.5, "desc": "Çanakkale, Balıkesir, İstanbul, Bursa", "base_wind": 36.0, "base_temp": 13.0},
    "Ege Bölgesi": {"lat": 38.4, "lon": 27.8, "desc": "İzmir, Manisa, Aydın, Muğla", "base_wind": 31.0, "base_temp": 15.0},
    "İç Anadolu Bölgesi": {"lat": 39.0, "lon": 33.0, "desc": "Konya, Ankara, Kayseri, Eskişehir", "base_wind": 23.0, "base_temp": 9.5},
    "Akdeniz Bölgesi": {"lat": 36.9, "lon": 32.5, "desc": "Antalya, Adana, Mersin, Hatay", "base_wind": 26.5, "base_temp": 17.0},
    "Güneydoğu Anadolu": {"lat": 37.5, "lon": 39.0, "desc": "Gaziantep, Şanlıurfa, Diyarbakır", "base_wind": 13.0, "base_temp": 14.5},
    "Karadeniz Bölgesi": {"lat": 41.3, "lon": 36.3, "desc": "Samsun, Trabzon, Sinop", "base_wind": 28.5, "base_temp": 12.0},
    "Doğu Anadolu": {"lat": 39.5, "lon": 41.5, "desc": "Erzurum, Malatya, Van, Elazığ", "base_wind": 14.0, "base_temp": 6.5},
}

CO2_AVOIDED_FACTOR = 0.45

@st.cache_data(ttl=300, show_spinner=False)
def fetch_all_regions_weather() -> Dict[str, Dict[str, Any]]:
    lats = [v["lat"] for v in REGIONS.values()]
    lons = [v["lon"] for v in REGIONS.values()]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lats,
        "longitude": lons,
        "hourly": "wind_speed_100m,direct_normal_irradiance,cloud_cover,temperature_2m",
        "timezone": "Europe/Istanbul",
        "forecast_days": 1,
    }
    headers = {
        "User-Agent": "EnerjiNabzi-Platform/1.0 (+https://enerjinabzi.onrender.com; contact: info@enerjinabzi.org)",
        "Accept": "application/json",
    }

    results: Dict[str, Dict[str, Any]] = {}
    region_keys = list(REGIONS.keys())
    now_hour = min(max(pd.Timestamp.now(tz="Europe/Istanbul").hour, 0), 23)

    data = None
    for attempt in range(2):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=12)
            if resp.status_code == 200:
                raw_data = resp.json()
                if isinstance(raw_data, list) and len(raw_data) == len(region_keys):
                    data = raw_data
                    break
        except Exception:
            continue

    if data is not None:
        for key, d in zip(region_keys, data):
            hourly = d.get("hourly", {})
            w_arr = hourly.get("wind_speed_100m", [20.0])
            w_speed = float(w_arr[now_hour] if now_hour < len(w_arr) else w_arr[0])

            t_arr = hourly.get("temperature_2m", [12.0])
            temp = float(t_arr[now_hour] if now_hour < len(t_arr) else t_arr[0])

            c_arr = hourly.get("cloud_cover", [40.0])
            cloud = float(c_arr[now_hour] if now_hour < len(c_arr) else c_arr[0])

            solar_arr = hourly.get("direct_normal_irradiance", [0.0])
            s_rad = float(solar_arr[now_hour] if now_hour < len(solar_arr) else 0.0)

            if w_speed > 30:
                w_status = "Kuvvetli Rüzgar / Yüksek Üretim"
            elif w_speed > 15:
                w_status = "Orta Şiddette / Normal Akış"
            else:
                w_status = "Sakin Rüzgar / Düşük Akış"

            if cloud < 25:
                s_status = "Açık ve Güneşli"
            elif cloud < 65:
                s_status = "Parçalı Bulutlu"
            else:
                s_status = "Çok Bulutlu / Kapalı"

            results[key] = {
                "name": key,
                "desc": REGIONS[key]["desc"],
                "wind_speed_kmh": round(w_speed, 1),
                "wind_speed_ms": round(w_speed / 3.6, 1),
                "temp_c": round(temp, 1),
                "wind_status": w_status,
                "solar_rad_wm2": round(s_rad, 0),
                "cloud_cover": round(cloud, 0),
                "solar_status": s_status,
            }
        return results

    now_ts = pd.Timestamp.now(tz="Europe/Istanbul")
    doy = now_ts.dayofyear
    decl = np.radians(23.45 * np.sin(np.radians(360.0 / 365.0 * (284 + doy))))
    ha = np.radians((now_hour - 12.0) * 15.0)

    for key, meta in REGIONS.items():
        lat_r = np.radians(meta["lat"])
        sin_elev = np.clip(np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(ha), -1.0, 1.0)
        elev = np.degrees(np.arcsin(sin_elev))

        base_wind = meta.get("base_wind", 22.0)
        diurnal_factor = 1.0 + 0.15 * np.sin(2.0 * np.pi * (now_hour - 6) / 24.0)
        w_speed = round(base_wind * diurnal_factor, 1)

        base_temp = meta.get("base_temp", 12.0)
        temp = round(base_temp + 3.0 * np.sin(2.0 * np.pi * (now_hour - 9) / 24.0), 1)

        if elev <= 0.0:
            s_rad = 0.0
            cloud = 30.0
            s_status = "Gece / Üretim Yok"
        else:
            flux = max(0.0, float(sin_elev))
            s_rad = round(flux * 750.0, 0)
            cloud = 35.0
            s_status = "Açık ve Güneşli" if s_rad > 400 else "Parçalı Bulutlu"

        if w_speed > 30:
            w_status = "Kuvvetli Rüzgar / Yüksek Üretim"
        elif w_speed > 15:
            w_status = "Orta Şiddette / Normal Akış"
        else:
            w_status = "Sakin Rüzgar / Düşük Akış"

        results[key] = {
            "name": key,
            "desc": meta["desc"],
            "wind_speed_kmh": w_speed,
            "wind_speed_ms": round(w_speed / 3.6, 1),
            "temp_c": temp,
            "wind_status": w_status,
            "solar_rad_wm2": s_rad,
            "cloud_cover": cloud,
            "solar_status": s_status,
        }

    return results

def calculate_esg_savings(mwh_amount: float) -> Dict[str, Any]:
    if mwh_amount is None or mwh_amount <= 0:
        return {"co2_formatted": "0"}

    co2_tons = mwh_amount * CO2_AVOIDED_FACTOR
    return {
        "co2_formatted": f"{co2_tons:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."),
    }
