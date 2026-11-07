import datetime
import json
import os
import pandas as pd
import requests


def parse_custom_date(tarih_val, saat_val):
    t_str = str(tarih_val).split(".")[0].strip()
    s_str = str(saat_val).strip()

    yil = int(t_str[-4:])
    ay = int(t_str[-6:-4])
    gun = int(t_str[:-6])
    saat = int(s_str.split(":")[0])

    return datetime.datetime(yil, ay, gun, saat, 0)


def update_data():
    csv_path = "temiz_epias_uretim.csv"
    profil_path = "saatlik_profil.csv"

    if not os.path.exists(csv_path):
        print(f"Hata: {csv_path} bulunamadı!")
        return

    df = pd.read_csv(csv_path)

    son_satir = df.iloc[-1]
    son_tarih = parse_custom_date(son_satir["Tarih"], son_satir["Saat"])
    print(f"Mevcut verideki son saat: {son_tarih}")

    simdi = datetime.datetime.now()
    if son_tarih >= simdi - datetime.timedelta(hours=2):
        print("Veri zaten güncel, yeni kayıt bulunmuyor.")
        return

    # EPİAŞ 2.0 ISO formatı
    baslangic = (son_tarih + datetime.timedelta(hours=1)).strftime(
        "%Y-%m-%dT00:00:00+03:00"
    )
    bitis = simdi.strftime("%Y-%m-%dT23:00:00+03:00")
    print(f"EPİAŞ'tan çekilen tarih aralığı: {baslangic} -> {bitis}")

    url = "https://seffaflik.epias.com.tr/electricity-service/v1/generation/data/real-time-generation"

    payload = {"startDate": baslangic, "endDate": bitis}

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Origin": "https://seffaflik.epias.com.tr",
        "Referer": "https://seffaflik.epias.com.tr/electricity/generation/real-time-generation",
    }

    try:
        # POST isteği gönderiyoruz
        res = requests.post(
            url, data=json.dumps(payload), headers=headers, timeout=30
        )
        print(f"EPİAŞ bağlantı yanıt kodu: {res.status_code}")

        if res.status_code != 200:
            print(f"EPİAŞ Hata Yanıtı: {res.text[:300]}")
            return

        json_data = res.json()
        items = []
        if isinstance(json_data, dict):
            items = (
                json_data.get("items")
                or json_data.get("body", {}).get("hourlyGenerations")
                or []
            )
        elif isinstance(json_data, list):
            items = json_data

        if not items:
            print("Gelen yanıtta saatlik veri listesi boş.")
            return

        yeni_satirlar = []
        for row in items:
            tarih_str = row.get("date")
            dt = pd.to_datetime(tarih_str).tz_localize(None)

            # Sadece mevcut CSV'de olmayan yeni saatleri al
            if dt <= son_tarih:
                continue

            tarih_formati = f"{dt.day}{dt.month:02d}{dt.year}"
            saat_formati = f"{dt.hour:02d}:00"

            ruzgar = float(row.get("wind") or row.get("ruzgar") or 0.0)
            gunes = float(
                row.get("solar")
                or row.get("sun")
                or row.get("gunes")
                or row.get("diger")
                or 0.0
            )
            toplam = float(row.get("total") or row.get("toplam") or 0.0)

            toplam_yenilenebilir = ruzgar + gunes
            oran = (
                (toplam_yenilenebilir / toplam * 100) if toplam > 0 else 0.0
            )

            yeni_satirlar.append(
                {
                    "Tarih": tarih_formati,
                    "Saat": saat_formati,
                    "Toplam": round(toplam, 2),
                    "Rüzgar": round(ruzgar, 2),
                    "Güneş": round(gunes, 2),
                    "Toplam_Yenilenebilir": round(toplam_yenilenebilir, 2),
                    "Yenilenebilir_Oran": oran,
                }
            )

        if not yeni_satirlar:
            print(
                "İncelenen aralıktaki tüm saatler zaten dosyada mevcut, eklenecek kayıt yok."
            )
            return

        yeni_df = pd.DataFrame(yeni_satirlar)
        df_guncel = pd.concat([df, yeni_df], ignore_index=True)
        df_guncel.to_csv(csv_path, index=False)
        print(f"Başarılı: {len(yeni_df)} yeni saatlik kayıt CSV'ye eklendi.")

        if os.path.exists(profil_path):
            profil = (
                df_guncel.groupby("Saat")[["Rüzgar", "Güneş"]]
                .mean()
                .reset_index()
            )
            profil.to_csv(profil_path, index=False)
            print("saatlik_profil.csv güncellendi.")

    except Exception as e:
        print(f"Güncelleme sırasında hata oluştu: {e}")


if __name__ == "__main__":
    update_data()
