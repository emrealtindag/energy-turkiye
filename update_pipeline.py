import datetime
import os
from eptr2 import EPTR2
import pandas as pd


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

    epias_eposta = "kaanbolek07@gmail.com"
    epias_sifre = os.getenv("EPIAS_PASSWORD")

    if not epias_sifre:
        print("Hata: EPIAS_PASSWORD ortam değişkeni bulunamadı!")
        return

    if not os.path.exists(csv_path):
        print(f"Hata: {csv_path} bulunamadı!")
        return

    df = pd.read_csv(csv_path)
    son_satir = df.iloc[-1]
    son_tarih = parse_custom_date(son_satir["Tarih"], son_satir["Saat"])
    print(f"Mevcut verideki son saat: {son_tarih}")

    simdi = datetime.datetime.now()
    if son_tarih >= simdi - datetime.timedelta(hours=2):
        print("Veri zaten güncel.")
        return

    baslangic = (son_tarih + datetime.timedelta(hours=1)).strftime("%Y-%m-%d")
    bitis = simdi.strftime("%Y-%m-%d")
    print(f"EPİAŞ'tan çekilen tarih aralığı: {baslangic} -> {bitis}")

    try:
        eptr = EPTR2(username=epias_eposta, password=epias_sifre)

        # eptr2 içinde çağrı adını belirle (öncelik 'rtg')
        cagri_adi = "rtg"
        try:
            available = eptr.get_available_calls()
            avail_list = (
                list(available.keys())
                if isinstance(available, dict)
                else list(available)
            )
            if "rtg" not in avail_list:
                for c in avail_list:
                    if any(
                        k in str(c).lower()
                        for k in ["rtg", "real_time", "generation"]
                    ):
                        cagri_adi = c
                        break
        except Exception:
            cagri_adi = "rtg"

        print(f"Kullanılan eptr2 çağrısı: {cagri_adi}")
        res = eptr.call(cagri_adi, start_date=baslangic, end_date=bitis)

        # Dönen sonuç DataFrame veya sözlük olabilir, ikisini de yönetelim
        yeni_satirlar = []

        if isinstance(res, pd.DataFrame):
            raw_records = res.to_dict("records")
        elif isinstance(res, dict):
            raw_records = (
                res.get("items")
                or res.get("body", {}).get("hourlyGenerations")
                or []
            )
        else:
            raw_records = []

        if not raw_records:
            print("EPİAŞ'tan yeni saatlik kayıt dönmedi.")
            return

        for row in raw_records:
            dt_raw = row.get("date") or row.get("tarih") or row.get("time")
            dt = pd.to_datetime(dt_raw).tz_localize(None)
            if dt <= son_tarih:
                continue

            tarih_formati = f"{dt.day}{dt.month:02d}{dt.year}"
            saat_formati = f"{dt.hour:02d}:00"

            ruzgar = float(row.get("wind") or row.get("ruzgar") or 0.0)
            gunes = float(
                row.get("sun") or row.get("solar") or row.get("gunes") or 0.0
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
            print("İncelenen aralıktaki veriler zaten mevcut.")
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
        print(f"Hata oluştu: {e}")


if __name__ == "__main__":
    update_data()
