# Turkiye Temiz Enerji Zekasi ve Canli Sebeke Platformu

EPİAS Seffaflik Platformu ve TEIAS verileriyle Turkiye'nin ruzgar ve gunes elektrik uretimini, 7 cografi bolgenin anlik meteorolojik potansiyelini, cok ufuklu yapay zeka projeksiyonlarini ve kurumsal ESG Scope-2 karbon emisyon tasarruflarini inceleyen uretim duzeyi analitik platformu.

---

## Sistem Mimarisi ve Moduller

### 1. Canli Sebeke & Bolgesel Potansiyel Haritasi
- **EPİAS Entegrasyonu:** Ulusal sebekedeki ruzgar, gunes ve toplam elektrik uretiminin saatlik takibi.
- **Canli Meteoroloji Servisi:** 7 cografi bolgenin (Marmara, Ege, Ic Anadolu, Akdeniz, Karadeniz, Guneydogu, Dogu Anadolu) anlik ruzgar hizi (100m turbin irtifasi), sicaklik, bulutluluk ve direkt normal gunes isinimi (DNI) verileri.
- **Interaktif Cografi Gorsellestirme:** Bolgelerin meteorolojik gucunu dinamik olcekli harita pinleriyle sunan arayuz.

### 2. Cok Ufuklu Yapay Zeka Tahmin Motoru (Ridge AI)
- **GOP & Sebeke Planlama Ufuklari:**
  - 24 Saatlik (Gunluk Piyasa Projeksiyonu)
  - 7 Gunluk (Haftalik Sebeke Egrisi)
  - 30 Gunluk (Aylik Trend ve Portfoy Planlama)
- **Alt-Saniye Performans:** Astronomik gunes acisi hesaplamalari ve gunduz-gece dongusu donusumleriyle 100 milisaniyenin altinda tahmin uretimi.

### 3. Kurumsal ESG ve SKDM (CBAM) Simulatoru
- **Scope-2 Karbon Salinimi:** EPİAS emisyon faktoru (0.45 tCO2e/MWh) uzerinden isletmelerin temiz enerjiye gecisle sagladiklari karbon tasarrufu modellemesi.
- **Mali Karsilik:** AB Karbon Fiyati (EUA) ve CBAM cercevesinde yillik olasi vergi muafiyeti projeksiyonu.
- **Yesil Finansman Sertifikasyonu:** Denetim ve surdurulebilirlik raporlarina hazir PDF/CSV kurumsal karne ciktisi.

### 4. Otomasyon & Canli Veri Hatti
- **GitHub Actions Pipeline:** EPTR2 kutuphanesi araciligiyla her saat basi ve her gece sebeke verilerini EPİAS uzerinden otomatik cekerek veri tabanini gunceller.
- **Veri Deposu:**
  - `data/temiz_epias_uretim.csv`: 8.760+ saatlik temizlenmis EPİAŞ ulusal uretim veri seti.
  - `data/saatlik_profil.csv`: 24 saatlik ortalama uretim karakteristigi profili.

---

## Yerel Kurulum ve Calistirma

Platformu yerel ortamda baslatmak icin:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Uygulama varsayilan olarak **http://localhost:8501** adresinde calisacaktir.

---

## Canli Dagitim Baglantilari

- **Render (Birincil Uretim Ortami):** https://enerjinabzi.onrender.com
- **Streamlit Community Cloud (Yedek):** https://enerjinabzi.streamlit.app
