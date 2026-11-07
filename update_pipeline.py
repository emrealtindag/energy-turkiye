import datetime
import os
import pandas as pd
import requests


def update_data():
    csv_path = "temiz_epias_uretim.csv"
    profil_path = "saatlik_profil.csv"

    if not os.path.exists(csv_path):
        print(f"Hata: {csv_path} bulunamadı!")
        return

    # Mevcut veriyi formatı belirterek oku
    df = pd.read_csv(csv_path)

    # Tarih sütununu esnek şekilde parse et
    df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Tarih"])

    son_tarih = df["Tarih"].max()
    print(f"Mevcut verideki son saat: {son_tarih}")

    simdi = datetime.datetime.now()
    if son_tarih >= simdi - datetime.timedelta(hours=2):
        print("Veri zaten güncel, yeni kayıt bulunmuyor.")
        return

    # Eksik aralığı belirle (ISO formatı)
    baslangic = (son_tarih + datetime.timedelta(hours=1)).strftime(
        "%Y-%m-%dT%H:00:00+03:00"
    )
    bitis = simdi.strftime("%Y-%m-%dT%H:00:00+03:00")

    url = "https://seffaflik.epias.com.tr/transparency/service/production/real-time-generation"
    params = {"startDate": baslangic, "endDate": bitis}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=30)
        print(f"EPİAŞ bağlantı yanıt kodu: {res.status_code}")

        if res.status_code != 200:
            print(f"EPİAŞ yanıt içeriği: {res.text[:200]}")
            return

        data = res.json().get("body", {}).get("hourlyGenerations", [])
        if not data:
            print("Çekilecek yeni saatlik veri dönmedi.")
            return

        yeni_kayitlar = []
        for row in data:
            tarih_str = row.get("date")
            dt = pd.to_datetime(tarih_str).tz_localize(None)
            ruzgar = row.get("wind", 0.0)
            gunes = row.get("sun", 0.0)
            toplam = row.get("total", 0.0)

            yeni_kayitlar.append(
                {
                    "Tarih": dt,
                    "Rüzgar": ruzgar,
                    "Güneş": gunes,
                    "Toplam_Uretim": toplam,
                }
            )

        yeni_df = pd.DataFrame(yeni_kayitlar)

        # Yeni veriyi ekle ve tarihe göre sırala
        df_guncel = pd.concat([df, yeni_df]).drop_duplicates(
            subset=["Tarih"], keep="last"
        )
        df_guncel = df_guncel.sort_values(by="Tarih").reset_index(drop=True)

        # Temiz CSV'yi kaydet
        df_guncel.to_csv(csv_path, index=False)
        print(f"Başarılı: {len(yeni_df)} yeni saat eklendi.")

        # 24 Saatlik ortalama profil tablosunu güncelle
        df_guncel["Saat"] = df_guncel["Tarih"].dt.hour
        profil = (
            df_guncel.groupby("Saat")[["Rüzgar", "Güneş"]].mean().reset_index()
        )
        profil.to_csv(profil_path, index=False)
        print("saatlik_profil.csv güncellendi.")

    except Exception as e:
        print(f"Güncelleme sırasında hata oluştu: {e}")


if __name__ == "__main__":
    update_data()
