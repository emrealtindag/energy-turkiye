# Türkiye Rüzgâr ve Güneş Panosu

COP31 haftası için EPİAŞ Şeffaflık Platformu verileriyle Türkiye'nin rüzgâr ve güneş elektrik üretimini inceleyen modern Streamlit paneli.

---

## Proje Durumu ve Veri Mimarisi

- **Arayüz Katmanı (`app.py`):** 
  - İki sütunlu modern SaaS dashboard düzeni.
  - Hızlı dönem butonları (`Gün`, `Hafta`, `Ay`, `Özel`).
  - 5 adet özel ikonlu KPI gösterge kartı (Rüzgâr, Güneş, Rüzgâr + Güneş Toplamı, Rüzgâr + Güneş Payı, Saatlik Zirve).
  - Saatlik rüzgâr ve güneş üretim zaman serisi (`connectgaps=False` ile eksik saat bağlantı korumalı).
  - 24 saatlik ortalama üretim profili eğrisi.
  - Günlük ve saatlik 2D üretim yoğunluk haritası (Heatmap).
  - Filtrelenen dönemi inceleme ve Türkçe CSV/Excel formatında indirme butonu.
  - 15 dakikalık (900 sn) `st.cache_data` önbellekleme.

- **Veri Katmanı (Kaan):**
  - `temiz_epias_uretim.csv`: 1 yıllık (8.760 saatlik) temizlenmiş EPİAŞ saatlik üretim veri seti (01.11.2026 — 31.10.2026).
  - `saatlik_profil.csv`: 24 saatlik ortalama üretim profil tablosu.
  - `src/epias_csv.py`: CSV dosyalarını okuyan, `timestamp` damgasını `Europe/Istanbul` (UTC+3) formatına normalize eden ve `load_generation_data`, `get_latest_complete_window`, `load_hourly_profile` fonksiyonlarını sağlayan veri katmanı.

---

## Başlatma

Uygulamayı yerel ortamda çalıştırmak için:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Uygulama varsayılan olarak **http://localhost:8501** adresinde açılır.

---

## Dağıtım (Streamlit Community Cloud)

1. **GitHub Deposu:** Projeyi GitHub deposuna yükleyin (`git push`).
2. **Streamlit Community Cloud:** [share.streamlit.io](https://share.streamlit.io) adresine giderek GitHub hesabınızla giriş yapın.
3. **Yeni Dağıtım:** Deponuzu seçin, ana dosya yolunu `app.py` olarak belirleyin ve **Deploy** butonuna basın.
