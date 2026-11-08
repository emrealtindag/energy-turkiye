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
    os.makedirs("data", exist_ok=True)
    csv_path = os.path.join("data", "temiz_epias_uretim.csv")
    profil_path = os.path.join("data", "saatlik_profil.csv")

    if not os.path.exists(csv_path) and os.path.exists("temiz_epias_uretim.csv"):
        csv_path = "temiz_epias_uretim.csv"
        profil_path = "saatlik_profil.csv"

    epias_eposta = os.getenv("EPIAS_USERNAME", "kaanbolek07@gmail.com")
    epias_sifre = os.getenv("EPIAS_PASSWORD", "9pADh+qn.UWk8M")

    if not os.path.exists(csv_path):
        print(f"Hata: {csv_path} bulunamadi!")
        return

    simdi = datetime.datetime.now()

    df = pd.read_csv(csv_path)
    if "Ruzgar" in df.columns and "Rüzgar" in df.columns:
        df["Rüzgar"] = df["Rüzgar"].combine_first(df["Ruzgar"])
        df = df.drop(columns=["Ruzgar"])
    if "Gunes" in df.columns and "Güneş" in df.columns:
        df["Güneş"] = df["Güneş"].combine_first(df["Gunes"])
        df = df.drop(columns=["Gunes"])

    df["dt_temp"] = df.apply(
        lambda r: parse_custom_date(r["Tarih"], r["Saat"]), axis=1
    )
    df = df[df["dt_temp"] <= simdi].drop(columns=["dt_temp"])
    df.to_csv(csv_path, index=False)
    print(
        f"Gelecek saatler temizlendi. Verideki son gecerli saat: {df.iloc[-1]['Tarih']} {df.iloc[-1]['Saat']}"
    )

    son_satir = df.iloc[-1]
    son_tarih = parse_custom_date(son_satir["Tarih"], son_satir["Saat"])

    baslangic = (son_tarih + datetime.timedelta(hours=1)).strftime("%Y-%m-%d")
    bitis = simdi.strftime("%Y-%m-%d")

    if son_tarih < simdi - datetime.timedelta(hours=1):
        try:
            print("EPIAS'tan eksik saatler kontrol ediliyor...")
            eptr = EPTR2(username=epias_eposta, password=epias_sifre)
            res = eptr.call("kgup", start_date=baslangic, end_date=bitis)

            records = (
                res.to_dict("records") if isinstance(res, pd.DataFrame) else []
            )
            yeni_satirlar = []

            col_w = "Rüzgar" if "Rüzgar" in df.columns else "Ruzgar"
            col_s = "Güneş" if "Güneş" in df.columns else "Gunes"

            for row in records:
                dt_raw = row.get("date") or row.get("tarih") or row.get("time")
                if not dt_raw:
                    continue
                dt = pd.to_datetime(dt_raw).tz_localize(None)

                if dt <= son_tarih or dt > simdi:
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
                        col_w: round(ruzgar, 2),
                        col_s: round(gunes, 2),
                        "Toplam_Yenilenebilir": round(toplam_yenilenebilir, 2),
                        "Yenilenebilir_Oran": oran,
                    }
                )

            if yeni_satirlar:
                yeni_df = pd.DataFrame(yeni_satirlar)
                df = pd.concat([df, yeni_df], ignore_index=True)
                df.to_csv(csv_path, index=False)
                print(f"{len(yeni_df)} yeni saat eklendi.")
        except Exception as e:
            print(f"Veri cekme uyarisi: {e}")

    if os.path.exists(profil_path):
        col_w = "Rüzgar" if "Rüzgar" in df.columns else "Ruzgar"
        col_s = "Güneş" if "Güneş" in df.columns else "Gunes"
        profil = (
            df.groupby("Saat")[[col_w, col_s]].mean().reset_index()
        )
        profil.to_csv(profil_path, index=False)
        print("saatlik_profil.csv guncellendi.")

    print("Islem tamam! Veriler su anki saate kadar temizlendi.")

if __name__ == "__main__":
    update_data()
