import datetime
import os
import pandas as pd
import requests


def parse_custom_date(tarih_val, saat_val):
    """1112025 veya 5112026 ve 23:00 formatındaki veriyi datetime objesine çevirir."""
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

    # Mevcut veriyi oku
    df = pd.read_csv(csv_path)

    # Son satırdan tam tarihi al
    son_satir = df.iloc[-1]
    son_tarih = parse_custom_date(son_satir["Tarih"], son_satir["Saat"])
    print(f"Mevcut verideki son saat: {son_tarih}")

    simdi = datetime.datetime.now()
    if son_tarih >= simdi - datetime.timedelta(hours=2):
        print("Veri zaten güncel, yeni kayıt bulunmuyor.")
        return

    # Sadece eksik olan 1-2 günlük aralığı iste
    baslangic = (son_tarih + datetime.timedelta(hours=1)).strftime(
        "%Y-%m-%dT%H:00:00+03:00"
    )
    bitis = simdi.strftime("%Y-%m-%dT%H:00:00+03:00")
    print(f"EPİAŞ'tan istenen aralık: {baslangic} -> {bitis}")

    url = "https://seffaflik.epias.com.tr/transparency/service/production/real-time-generation"
    params = {"startDate": baslangic, "endDate": bitis}

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    try:
        res = requests.get(url, params=params, headers=headers, timeout=60)
        print(f"EPİAŞ bağlantı yanıt kodu: {res.status_code}")

        if res.status_code != 200:
            print(f"EPİAŞ yanıt içeriği: {res.text[:200]}")
            return

        data = res.json().get("body", {}).get("hourlyGenerations", [])
        if not data:
            print("Çekilecek yeni saatlik veri dönmedi.")
            return

        yeni_satirlar = []
        for row in data:
            tarih_str = row.get("date")
            dt = pd.to_datetime(tarih_str)

            # Orijinal CSV formatı: Tarih (g+aa+yyyy -> 5112026), Saat (23:00)
            tarih_formati = f"{dt.day}{dt.month:02d}{dt.year}"
            saat_formati = f"{dt.hour:02d}:00"

            ruzgar = float(row.get("wind", row.get("ruzgar", 0.0)))
            gunes = float(
                row.get("sun", row.get("solar", row.get("gunes", 0.0)))
            )
            toplam = float(row.get("total", row.get("toplam", 0.0)))

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

        yeni_df = pd.DataFrame(yeni_satirlar)

        # Mevcut verinin altına ekle
        df_guncel = pd.concat([df, yeni_df], ignore_index=True)
        df_guncel.to_csv(csv_path, index=False)
        print(f"Başarılı: {len(yeni_df)} yeni saatlik kayıt CSV'ye eklendi.")

        # 24 Saatlik ortalama profil tablosunu güncelle
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
