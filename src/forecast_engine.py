"""Weather and Environmental Intelligence Service.

Türkiye geneli ve 7 coğrafi bölge için anlık rüzgâr ve güneş hava verileri.
"""

from typing import Any, Dict
import pandas as pd
import requests
import streamlit as st

# Türkiye Geneli ve 7 Coğrafi Bölge Referans Koordinatları
REGIONS: Dict[str, Dict[str, Any]] = {
    "Tüm Türkiye (Ortalama)": {"lat": 39.0, "lon": 35.0, "desc": "Ulusal Ağırlıklı Ortalama"},
    "Marmara Bölgesi": {"lat": 40.5, "lon": 28.5, "desc": "Çanakkale, Balıkesir, İstanbul, Bursa"},
    "Ege Bölgesi": {"lat": 38.4, "lon": 27.8, "desc": "İzmir, Manisa, Aydın, Muğla"},
    "İç Anadolu Bölgesi": {"lat": 39.0, "lon": 33.0, "desc": "Konya, Ankara, Kayseri, Eskişehir"},
    "Akdeniz Bölgesi": {"lat": 36.9, "lon": 32.5, "desc": "Antalya, Adana, Mersin, Hatay"},
    "Güneydoğu Anadolu": {"lat": 37.5, "lon": 39.0, "desc": "Gaziantep, Şanlıurfa, Diyarbakır"},
    "Karadeniz Bölgesi": {"lat": 41.3, "lon": 36.3, "desc": "Samsun, Trabzon, Sinop"},
    "Doğu Anadolu": {"lat": 39.5, "lon": 41.5, "desc": "Erzurum, Malatya, Van, Elazığ"},
}

CO2_AVOIDED_FACTOR = 0.45


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_all_regions_weather() -> Dict[str, Dict[str, Any]]:
    """Tüm Türkiye ve 7 bölge için hava durumu verilerini tek bir batch çağrıda çeker."""
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

    results: Dict[str, Dict[str, Any]] = {}
    region_keys = list(REGIONS.keys())

    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                now_hour = min(max(pd.Timestamp.now(tz="Europe/Istanbul").hour, 0), 23)
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

                    # Durum metni
                    if w_speed > 30:
                        w_status = "Kuvvetli Rüzgâr / Yüksek Üretim"
                    elif w_speed > 15:
                        w_status = "Orta Şiddette / Normal Akış"
                    else:
                        w_status = "Sakin Rüzgâr / Düşük Akış"

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
    except Exception:
        pass

    # Yedek veri
    for key in region_keys:
        results[key] = {
            "name": key,
            "desc": REGIONS[key]["desc"],
            "wind_speed_kmh": 22.5,
            "wind_speed_ms": 6.3,
            "temp_c": 13.0,
            "wind_status": "Normal Akış",
            "solar_rad_wm2": 180.0,
            "cloud_cover": 40.0,
            "solar_status": "Parçalı Bulutlu",
        }
    return results


def calculate_esg_savings(mwh_amount: float) -> Dict[str, Any]:
    """Üretilen temiz enerji ile önlenen CO2 miktarını hesaplar."""
    if mwh_amount is None or mwh_amount <= 0:
        return {"co2_formatted": "0"}

    co2_tons = mwh_amount * CO2_AVOIDED_FACTOR
    return {
        "co2_formatted": f"{co2_tons:,.0f}".replace(",", "X").replace(".", ",").replace("X", "."),
    }
