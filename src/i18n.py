import copy
import re
import textwrap
from typing import Any
import streamlit as st

EXACT_MAP = {
    "Enerji Nabzı · Türkiye Rüzgar ve Güneş Enerjisi İzleme ve Yapay Zeka ile Tahmin Platformu": "Energy Pulse · Türkiye Wind & Solar Energy Monitoring and AI Forecasting Platform",
    "Canlı Şebeke & Hava Durumu": "Live Grid & Weather",
    "Yapay Zeka Tahmini (24 Saat – 2 Ay)": "AI Forecast (24 Hours – 2 Months)",
    "Yapay Zeka Tahmini (24 Saat – 1 Ay)": "AI Forecast (24 Hours – 1 Month)",
    "Kurumsal ESG Simülatörü": "Corporate ESG Simulator",
    "İncelenen Bölge": "Selected Region",
    "Tüm Türkiye (Ortalama)": "All Türkiye (National Average)",
    "Marmara Bölgesi": "Marmara Region",
    "Ege Bölgesi": "Aegean Region",
    "İç Anadolu Bölgesi": "Central Anatolia Region",
    "Akdeniz Bölgesi": "Mediterranean Region",
    "Güneydoğu Anadolu": "Southeastern Anatolia",
    "Karadeniz Bölgesi": "Black Sea Region",
    "Doğu Anadolu": "Eastern Anatolia",
    "Ulusal Ağırlıklı Ortalama": "National Weighted Average",
    "Dönem Seçimi": "Period Selection",
    "Günlük (24 Saat)": "Daily (24 Hours)",
    "Haftalık (7 Gün)": "Weekly (7 Days)",
    "Aylık (30 Gün)": "Monthly (30 Days)",
    "Yıllık (365 Gün)": "Annual (365 Days)",
    "Özel Aralık": "Custom Range",
    "Başlangıç": "Start Date",
    "Bitiş": "End Date",
    "Piyasa verileri yükleniyor...": "Loading market telemetry...",
    "Başlangıç tarihi bitiş tarihinden sonra olamaz. Lütfen tarih seçimini kontrol edin.": "Start date cannot be after end date. Please check your date selection.",
    "Veri kaynağına erişilirken bir sorun oluştu. Lütfen veri bağlantısını kontrol edin.": "An error occurred while accessing the data source. Please check the data connection.",
    "Veri Uyuşmazlığı: Beklenen sütunlar eksik. Veri fonksiyonunun timestamp, wind_mwh, solar_mwh, total_mwh alanlarını sağlaması gerekir.": "Data Mismatch: Expected columns are missing. The data loader must provide timestamp, wind_mwh, solar_mwh, and total_mwh fields.",
    "Seçilen tarih aralığında gösterilecek veri bulunamadı. Lütfen geçerli bir tarih aralığı seçin.": "No data found for the selected date range. Please select a valid date range.",
    "Saat Dilimi Teyit Bekliyor: Zaman damgalarında saat dilimi bilgisi bulunamadı. Veriler olduğu gibi sunulmuştur.": "Timezone Unconfirmed: No timezone metadata found in timestamps. Data is presented as-is.",
    "Kaynak": "Source",
    "Rüzgar": "Wind",
    "Güneş": "Solar",
    "Rüzgar Ort.": "Wind Avg.",
    "Güneş Ort.": "Solar Avg.",
    "Üretim (MWh)": "Generation (MWh)",
    "Ort. MWh": "Avg. MWh",
    "Tahmin Vadesi": "Forecast Horizon",
    "24 Saatlik (Günlük GÖP)": "24 Hours (Day-Ahead)",
    "7 Günlük (Haftalık)": "7 Days (Weekly)",
    "30 Günlük (Aylık)": "30 Days (Monthly)",
    "60 Günlük (2 Aylık)": "60 Days (2 Months)",
    "Tahmini Rüzgar (Yeşil)": "Forecasted Wind (Green)",
    "Tahmini Güneş (Turuncu)": "Forecasted Solar (Amber)",
    "Tahmini Toplam Yenilenebilir": "Forecasted Total Renewable",
    "Tahmini Üretim (MWh)": "Forecasted Generation (MWh)",
    "Gelecek 24 Saat (GÖP Saatlik Tahmini)": "Next 24 Hours (Day-Ahead Hourly Forecast)",
    "Gelecek 7 Gün (Saatlik Tahmin)": "Next 7 Days (Hourly Forecast)",
    "Tesis / Tüketim Profili Seçimi": "Facility / Consumption Profile Selection",
    "Organize Sanayi Fabrikası (OSB)": "Organized Industrial Zone Factory (OIZ)",
    "Veri Merkezi (Datacenter 7/24)": "Data Center (24/7 Baseload)",
    "Ticari Plaza ve AVM": "Commercial Plaza & Shopping Mall",
    "Özel CSV Dosyası Yükle": "Upload Custom CSV File",
    "Fabrika Saatlik Tüketim CSV'si Yükleyin (Sütun: 'tuketim_mwh')": "Upload Facility Hourly Consumption CSV (Column: 'tuketim_mwh')",
    "CSV dosyası okunamadı. Lütfen biçimi kontrol edin.": "Could not read CSV file. Please check the file format.",
    "Tesis Toplam Tüketimi (MWh)": "Total Facility Consumption (MWh)",
    "Şebekeden Karşılanan Rüzgar + Güneş (MWh)": "Grid-Matched Wind + Solar Supply (MWh)",
    "Kapsam 2 Karbon Hesabını İndir (Simülasyon CSV)": "Download Scope 2 Carbon Audit (Simulation CSV)",
    "İndirilen dosya karar destek ve simülasyon amaçlı tahmini hesaplamadır; resmi denetim belgesi niteliği taşımaz.": "The downloaded file is an estimated simulation for decision support and does not constitute an official accredited audit certificate.",
}

SUBSTRING_REPLACEMENTS = [
    ("YENİLENEBİLİR ENERJİ İZLEME PLATFORMU · ENERJİ NABZI", "RENEWABLE ENERGY MONITORING PLATFORM · ENERGY PULSE"),
    ("EPİAŞ Gerçek Verisi · Canlı API", "EPİAŞ Real-Time Data · Live API"),
    ("Türkiye Rüzgar ve Güneş Enerjisi İzleme ve Yapay Zeka ile Tahmin Platformu", "Türkiye Wind & Solar Energy Monitoring and AI Forecasting Platform"),
    ("Saatlik üretimi, bölgesel hava durumunu, rüzgar + güneş payını, yapay zeka üretim tahminlerini ve tepe üretim saatlerini tek bir ekranda inceleyin.", "Monitor hourly generation, regional weather patterns, wind + solar grid share, AI production forecasts, and peak generation hours on a single screen."),
    ("Aktif Yeşil Saat (Düşük Karbon Penceresi)", "Active Green Hour (Low Carbon Window)"),
    ("Standart Şebeke Yoğunluğu", "Standard Grid Intensity"),
    ("Fabrikalar, organize sanayi fırınları, batarya şarjı ve elektrikli araç şarjı için en temiz zaman dilimi.", "Optimal low-carbon window for industrial plants, furnaces, battery storage, and EV charging."),
    ("Enerji yoğun sanayi yüklerinin rüzgar ve güneşin arttığı saatlere kaydırılması önerilir.", "Shifting energy-intensive industrial loads to peak wind and solar hours is recommended."),
    ("Enerji tüketiminde standart şebeke tarifesi geçerli.", "Standard grid tariff applies for current energy consumption."),
    ("Şebeke Durumu", "Grid Status"),
    ("Anlık Karbon Yoğunluğu", "Live Carbon Intensity"),
    ("Temiz Enerji Payı", "Clean Energy Share"),
    ("Karar Destek / Akıllı Yönlendirme", "Decision Support / Smart Dispatch"),
    ("Canlı Hava Durumu & Bölge Seçimi", "Live Weather & Region Selection"),
    ("İncelemek istediğiniz coğrafi bölgeyi seçin", "Select the geographic region you want to inspect"),
    ("Türkiye Canlı Potansiyel Haritası", "Türkiye Live Renewable Potential Map"),
    ("7 coğrafi bölgenin anlık rüzgar hızı ve meteorolojik dağılımı (Detaylar için bölgelerin üzerine gelin)", "Real-time wind speed and meteorological distribution across 7 geographic regions (Hover over regions for details)"),
    ("Kuvvetli Rüzgar / Yüksek Üretim", "Strong Wind / High Generation"),
    ("Orta Şiddette / Normal Akış", "Moderate Wind / Normal Flow"),
    ("Sakin Rüzgar / Düşük Akış", "Calm Wind / Low Flow"),
    ("Açık ve Güneşli", "Clear & Sunny"),
    ("Parçalı Bulutlu", "Partly Cloudy"),
    ("Çok Bulutlu / Kapalı", "Mostly Cloudy / Overcast"),
    ("Gece / Üretim Yok", "Night / No Solar Generation"),
    ("Rüzgar Durumu", "Wind Status"),
    ("Güneş Işınımı", "Solar Irradiance"),
    ("Havza Detayı", "Basin Details"),
    ("Ulusal Ağırlıklı Ortalama", "National Weighted Average"),
    ("Tüm Türkiye (Ortalama)", "All Türkiye (National Average)"),
    ("Marmara Bölgesi", "Marmara Region"),
    ("Ege Bölgesi", "Aegean Region"),
    ("İç Anadolu Bölgesi", "Central Anatolia Region"),
    ("Akdeniz Bölgesi", "Mediterranean Region"),
    ("Güneydoğu Anadolu", "Southeastern Anatolia"),
    ("Karadeniz Bölgesi", "Black Sea Region"),
    ("Doğu Anadolu", "Eastern Anatolia"),
    ("Bulut:", "Cloud Cover:"),
    ("İnceleme Dönemi", "Analysis Period"),
    ("Seçili Aralık:", "Selected Range:"),
    ("Kaynak: <b>EPİAŞ Şeffaflık</b>", "Source: <b>EPİAŞ Transparency</b>"),
    ("Veri Kapsamı:", "Data Coverage:"),
    ("(1 Yıl / 8.760+ Saat)", "(1 Year / 8,760+ Hours)"),
    ("Çözünürlük: <b>Saatlik (MWh)</b>", "Resolution: <b>Hourly (MWh)</b>"),
    ("Saat Dilimi: <b>İstanbul (UTC+3)</b>", "Timezone: <b>Istanbul (UTC+3)</b>"),
    ("Önbellek: <b>15 Dk (TTL: 900s)</b>", "Cache: <b>15 Min (TTL: 900s)</b>"),
    ("<b>Güneş verisi hakkında:</b> EPİAŞ üretim serisi lisanssız (çatı ve öz tüketim) güneş üretimini tam yansıtmayabilir. Gerçek güneş üretimi ve rüzgar + güneş payı gösterilen değerlerden daha yüksek olabilir.", "<b>Note on Solar Data:</b> The EPİAŞ generation series may not fully capture unlicensed (rooftop and self-consumption) solar installations. Actual solar output and the combined wind + solar share may be higher than reported."),
    ("Tahmini Rüzgar Üretimi", "Forecasted Wind Generation"),
    ("Tahmini Güneş Üretimi", "Forecasted Solar Generation"),
    ("Tahmini Toplam Üretim", "Forecasted Total Generation"),
    ("Beklenen Zirve Üretim", "Expected Peak Generation"),
    ("Tepe Saati", "Peak Hour"),
    ("En yüksek saat:", "Peak timestamp:"),
    ("Rüzgar + Güneş Payı", "Wind + Solar Share"),
    ("Rüzgar + Güneş", "Wind + Solar"),
    ("Rüzgar Üretimi", "Wind Generation"),
    ("Güneş Üretimi", "Solar Generation"),
    ("Saatlik Zirve", "Hourly Peak"),
    ("Önlenen CO₂ Salımı", "Avoided CO₂ Emissions"),
    ("Dönem toplamı", "Period total"),
    ("İki kaynağın toplamı", "Combined renewable total"),
    ("Toplam üretimdeki oran", "Share in total generation"),
    ("~0,45 tCO₂ / MWh ikamesi", "~0.45 tCO₂ / MWh grid displacement"),
    ("Geçerli zirve ölçümü yok", "No valid peak record"),
    ("Hesaplanamadı", "N/A"),
    ("Veri Yok", "No Data"),
    ("Saatlik Üretim Dağılımı", "Hourly Generation Distribution"),
    ("Dönem boyunca rüzgar ve güneş santrallerinin saatlik üretim profili", "Hourly power generation profile of wind and solar plants throughout the selected period"),
    ("<span><i style=\"background:#059669\"></i> Rüzgar</span>", "<span><i style=\"background:#059669\"></i> Wind</span>"),
    ("<span><i style=\"background:#EAB308\"></i> Güneş</span>", "<span><i style=\"background:#EAB308\"></i> Solar</span>"),
    ("Verideki Son Kayıt:", "Latest Record in Dataset:"),
    ("(TSİ)", "(TRT)"),
    ("Zaman Dilimi: Europe/Istanbul (UTC+3)", "Timezone: Europe/Istanbul (UTC+3)"),
    ("24 Saatlik Üretim Profili", "24-Hour Generation Profile"),
    ("Günün saatlerine göre ortalama rüzgar ve güneş dağılımı", "Average diurnal distribution of wind and solar generation by hour of day"),
    ("Saatlik Üretim Yoğunluk Haritası", "Hourly Generation Intensity Heatmap"),
    ("Günler ve saatler arasındaki üretim yoğunluğu", "Generation intensity matrix across days and hours"),
    ("Yoğunluk haritası için en az 2 günlük aralık seçiniz.", "Please select a range of at least 2 days to display the intensity heatmap."),
    ("<b>Açıklama ve Metodoloji:</b> Bu panelde sunulan elektrik üretim verileri <b>EPİAŞ Şeffaflık Platformu</b>", "<b>Methodology & Data Note:</b> Electricity generation figures presented in this dashboard are official national grid data sourced from the <b>EPİAŞ Transparency Platform</b>"),
    ("kaynaklı ulusal şebeke verileridir (TEİAŞ iletim şebekesine bağlı tüm Türkiye toplamıdır).", "(representing the aggregate Türkiye transmission grid operated by TEİAŞ)."),
    ("Bölgesel hava durumu değerleri Türkiye geneli ve 7 coğrafi bölgenin anlık atmosferik modellerinden derlenmiştir.", "Regional weather metrics are compiled from real-time atmospheric models across all 7 geographic regions of Türkiye."),
    ("Önlenen karbon emisyonu, Türkiye şebekesi ortalama termik ikame faktörü (~0,45 ton CO₂ / MWh) referans alınarak hesaplanmıştır.", "Avoided carbon emissions are calculated using the national thermal grid displacement factor (~0.45 tons CO₂ / MWh)."),
    ("Yapay Zeka Yenilenebilir Üretim Projeksiyonu", "AI Renewable Generation Projection"),
    ("EPİAŞ saatlik verisi ve astronomik güneş fiziğiyle eğitilen makine öğrenmesi projeksiyonu", "Machine learning projection trained on hourly EPİAŞ telemetry and astronomical solar physics"),
    ("<b>Projeksiyon Metodolojisi & Karar Destek:</b> Model, tarihsel EPİAŞ verisi ve astronomik güneş fiziği kullanarak seçilen vade", "<b>Projection Methodology & Decision Support:</b> The model computes generation projections using historical EPİAŞ telemetry and astronomical solar physics over the selected"),
    ("boyunca üretim projeksiyonunu hesaplar. Uzun vadelerde grafik akıcılığı için günlük ortalamalar gösterilir; CSV çıktısında ise tüm saatlik detaylar yer alır.", "horizon. For longer horizons, daily averages are plotted for visual clarity, while the CSV export contains the full hourly breakdown."),
    ("COP31 Kurumsal Sürdürülebilirlik (ESG) & Fabrika Karbon Raporu", "COP31 Corporate Sustainability (ESG) & Industrial Carbon Report"),
    ("Şirketinizin veya fabrikanızın elektrik tüketimini ulusal rüzgar ve güneş payı ile eşleştirerek Kapsam 2 (Scope 2) karbon raporunu hesaplayın", "Match your facility's hourly electricity consumption with the national wind and solar grid share to calculate your Scope 2 carbon footprint report"),
    ("Toplam Fabrika Tüketimi", "Total Facility Consumption"),
    ("Organize Sanayi Fabrikası (OSB) profil tüketimi", "Organized Industrial Zone Factory (OIZ) profile consumption"),
    ("Veri Merkezi (Datacenter 7/24) profil tüketimi", "Data Center (24/7 Baseload) profile consumption"),
    ("Ticari Plaza ve AVM profil tüketimi", "Commercial Plaza & Shopping Mall profile consumption"),
    ("Özel CSV Dosyası Yükle profil tüketimi", "Custom CSV File profile consumption"),
    ("Temiz Enerji Tedariği", "Clean Energy Supply"),
    ("Şebeke Payı", "Grid Share"),
    ("MWh rüzgar ve güneşten karşılandı", "MWh supplied from wind and solar"),
    ("Önlenen Karbon Emisyonu", "Avoided Carbon Emissions"),
    ("Tasarruf", "Savings"),
    ("Termik ikamesi (~0,45 tCO₂/MWh)", "Thermal displacement (~0.45 tCO₂/MWh)"),
    ("COP31 Yeşil Enerji Skoru", "COP31 Green Energy Rating"),
    ("Kapsam 2 Yoğunluğu:", "Scope 2 Intensity:"),
    ("Kapsam 2", "Scope 2"),
    ("A+ (Üst Düzey Yeşil Tedarik)", "A+ (Premier Green Supply)"),
    ("A (İyi Düzey Yeşil Tedarik)", "A (High Green Supply)"),
    ("B+ (Gelişmekte Olan Tedarik)", "B+ (Developing Green Supply)"),
    ("B (Standart Şebeke Tedariği)", "B (Standard Grid Supply)"),
    ("<b>Metodoloji & Yasal Sorumluluk Reddi (Disclaimer):</b> Şirket veya fabrikanın saatlik elektrik tüketimi,", "<b>Methodology & Legal Disclaimer:</b> The facility's hourly electricity consumption is"),
    ("EPİAŞ ulusal iletim şebekesindeki o saatin rüzgar ve güneş payı ile GHG Protocol Scope 2 pazar bazlı yaklaşımına göre eşleştirilerek simüle edilmiştir.", "simulated by matching the hourly wind and solar share on the EPİAŞ national transmission grid in accordance with the GHG Protocol Scope 2 framework."),
    ("Bu sonuçlar kurumsal iç sürdürülebilirlik planlaması ve enerji optimizasyonu için karar destek amaçlı olup,", "These results are intended for internal corporate sustainability planning and energy optimization decision support, and"),
    ("bağımsız denetimden geçmiş resmi ISO 14064 doğrulama belgesi yerine geçmez.", "do not substitute for an independently verified ISO 14064 audit certificate."),
    ("<b>Lisanssız Güneş Notu:</b> EPİAŞ üretim serisi lisanssız (çatı ve öz tüketim) güneş üretimini tam yansıtmayabilir.", "<b>Unlicensed Solar Note:</b> The EPİAŞ generation series may not fully capture unlicensed (rooftop and self-consumption) solar installations."),
    ("Bu durum gerçek temiz enerji payının gösterilenden bir miktar daha yüksek, şebeke karbon yoğunluğunun ise daha düşük olmasına yol açabilir.", "Consequently, the actual clean energy share may be slightly higher and the grid carbon intensity lower than displayed."),
    ("ENERJİ NABZI", "ENERGY PULSE"),
    ("Veri Kaynağı: <b>EPİAŞ Şeffaflık Platformu (Canlı API & Saatlik Otomasyon)</b> · TEİAŞ Ulusal İletim Şebekesi", "Data Source: <b>EPİAŞ Transparency Platform (Live API & Hourly Automation)</b> · TEİAŞ National Transmission Grid"),
    ("Yapay zeka modelleri ve Scope 2 ESG simülasyonları açık veri analitiği karar destek amaçlıdır.", "AI forecasting models and Scope 2 ESG simulations are designed for open-data decision support analytics."),
    ("© 2026 Enerji Nabzı Platformu · Tüm Hakları Saklıdır", "© 2026 Energy Pulse Platform · All Rights Reserved"),
    ("Tahmin hesaplanırken durum oluştu:", "An error occurred while computing forecast:"),
    ("Ortalama: ~", "Average: ~"),
    (">Canlı<", ">Live<"),
    (">Dönem<", ">Period<"),
    ("km/s", "km/h"),
    ("MWh/saat", "MWh/h"),
    ("Günlük Ort.", "Daily Avg."),
    ("ton CO₂", "tons CO₂"),
    ('<span class="u">ton</span>', '<span class="u">tons</span>'),
    ("24 Saatlik", "24-Hour"),
    ("7 Günlük", "7-Day"),
    ("30 Günlük", "30-Day"),
    ("60 Günlük", "60-Day"),
    ("24 saatlik", "24-hour"),
    ("7 günlük", "7-day"),
    ("30 günlük", "30-day"),
    ("60 günlük", "60-day"),
]

MONTH_REPLACEMENTS = [
    (r"\bOca\b", "Jan"),
    (r"\bŞub\b", "Feb"),
    (r"\bMar\b", "Mar"),
    (r"\bNis\b", "Apr"),
    (r"\bMay\b", "May"),
    (r"\bHaz\b", "Jun"),
    (r"\bTem\b", "Jul"),
    (r"\bAğu\b", "Aug"),
    (r"\bEyl\b", "Sep"),
    (r"\bEki\b", "Oct"),
    (r"\bKas\b", "Nov"),
    (r"\bAra\b", "Dec"),
]

REGEX_REPLACEMENTS = [
    (r"(\d+)\s+Gün\s+·\s+(\d+)\s+Saat", r"\1 Days · \2 Hours"),
    (r"Toplam\s+(\d+)\s+saatlik\s+kayıt", r"Total \1 hourly records"),
    (r"%(\d+[.,]?\d*)\s+Pay", r"\1% Share"),
    (r">%\s*(\d+[.,]?\d*)<", r">\1%<"),
    (r"Bulut:\s*%(\d+[.,]?\d*)", r"Cloud Cover: \1%"),
    (r"Cloud Cover:\s*%(\d+[.,]?\d*)", r"Cloud Cover: \1%"),
    (r"(.+?)\s+projeksiyon hesaplanıyor\.\.\.", r"Calculating \1 projection..."),
    (r"(.+?)\s+Saatlik Tahmin Tablosunu İndir \(CSV\)", r"Download \1 Hourly Forecast Table (CSV)"),
    (r"Gelecek\s+(.+?)\s+boyunca tüm saatlik rüzgar, güneş ve toplam üretim projeksiyon dökümü\.", r"Complete hourly wind, solar, and total generation projection breakdown for the next \1."),
    (r"Gelecek\s+(.+?)\s+Projeksiyon\s+\(Günlük Ortalama\)", r"Next \1 Projection (Daily Average)"),
    (r"<b>Eksik Ölçüm Uyarısı:</b>\s*Seçili dönemde\s*Rüzgar:\s*(\d+)\s*saat,\s*Güneş:\s*(\d+)\s*saat,\s*Toplam:\s*(\d+)\s*saat eksik \(NaN\) ölçüm tespit edildi\.\s*Veri bütünlüğü için doldurma veya interpolasyon yapılmamıştır\.", r"<b>Missing Measurement Notice:</b> In the selected period, Wind: \1 hrs, Solar: \2 hrs, Total: \3 hrs of missing (NaN) records were detected. No imputation or interpolation was applied to preserve data integrity."),
]


def get_lang() -> str:
    val = st.session_state.get("app_lang_selector", "TR · Türkçe")
    if val and str(val).startswith("EN"):
        return "EN"
    return "TR"


def tr_text(text: Any) -> Any:
    if not isinstance(text, str) or not text:
        return text
    if get_lang() != "EN":
        return text

    stripped = text.strip()
    if stripped in EXACT_MAP:
        return text.replace(stripped, EXACT_MAP[stripped])

    out = text
    for src, dst in SUBSTRING_REPLACEMENTS:
        if src in out:
            out = out.replace(src, dst)

    for pattern, repl in REGEX_REPLACEMENTS:
        out = re.sub(pattern, repl, out)

    for m_pat, m_rep in MONTH_REPLACEMENTS:
        out = re.sub(m_pat, m_rep, out)

    return out


def translate_plotly_figure(fig: Any) -> Any:
    if get_lang() != "EN" or fig is None:
        return fig

    try:
        fig = copy.deepcopy(fig)
        for trace in fig.data:
            if getattr(trace, "name", None):
                trace.name = tr_text(trace.name)
            if getattr(trace, "hovertemplate", None):
                ht = trace.hovertemplate
                ht = ht.replace("Havza:", "Basin:")
                ht = ht.replace("Rüzgar Hızı:", "Wind Speed:")
                ht = ht.replace("Sıcaklık:", "Temperature:")
                ht = ht.replace("Güneş Işınımı:", "Solar Irradiance:")
                ht = ht.replace("Tahmini Rüzgar:", "Forecasted Wind:")
                ht = ht.replace("Tahmini Güneş:", "Forecasted Solar:")
                ht = ht.replace("Tahmini Toplam:", "Forecasted Total:")
                ht = ht.replace("Rüzgar:", "Wind:")
                ht = ht.replace("Güneş:", "Solar:")
                ht = ht.replace("Tüketim:", "Consumption:")
                ht = ht.replace("Temiz Enerji Payı:", "Clean Energy Supply:")
                ht = tr_text(ht)
                trace.hovertemplate = ht
            if getattr(trace, "text", None) is not None:
                if isinstance(trace.text, (list, tuple)):
                    trace.text = [tr_text(str(x)) for x in trace.text]
                else:
                    try:
                        trace.text = [tr_text(str(x)) for x in trace.text]
                    except Exception:
                        pass
            if getattr(trace, "customdata", None) is not None:
                try:
                    new_cd = []
                    for row in trace.customdata:
                        new_cd.append([tr_text(str(cell)) if isinstance(cell, str) else cell for cell in row])
                    trace.customdata = new_cd
                except Exception:
                    pass
            if getattr(trace, "x", None) is not None:
                try:
                    if len(trace.x) > 0 and isinstance(trace.x[0], str):
                        trace.x = [tr_text(x) for x in trace.x]
                except Exception:
                    pass
            if getattr(trace, "y", None) is not None:
                try:
                    if len(trace.y) > 0 and isinstance(trace.y[0], str):
                        trace.y = [tr_text(y) for y in trace.y]
                except Exception:
                    pass
            if hasattr(trace, "marker") and getattr(trace.marker, "colorbar", None):
                cb = trace.marker.colorbar
                if getattr(cb, "title", None) and getattr(cb.title, "text", None):
                    cb.title.text = tr_text(cb.title.text)

        if getattr(fig, "layout", None):
            if getattr(fig.layout, "xaxis", None) and getattr(fig.layout.xaxis, "title", None):
                if getattr(fig.layout.xaxis.title, "text", None):
                    fig.layout.xaxis.title.text = tr_text(fig.layout.xaxis.title.text)
            if getattr(fig.layout, "yaxis", None) and getattr(fig.layout.yaxis, "title", None):
                if getattr(fig.layout.yaxis.title, "text", None):
                    fig.layout.yaxis.title.text = tr_text(fig.layout.yaxis.title.text)
    except Exception:
        pass
    return fig


def translate_csv_bytes(data: Any) -> Any:
    if get_lang() != "EN" or not isinstance(data, bytes):
        return data
    try:
        text = data.decode("utf-8-sig")
        csv_replacements = [
            ("COP31 KURUMSAL KAPSAM 2 (SCOPE 2) TAHMİNİ KARBON HESABI", "COP31 CORPORATE SCOPE 2 ESTIMATED CARBON AUDIT REPORT"),
            ("YASAL UYARI: Bu rapor simülasyon ve karar destek amaçlıdır;", "LEGAL DISCLAIMER: This report is for simulation and decision support purposes;"),
            ("bağımsız akredite denetim belgesi veya resmi beyan yerine geçmez.", "it does not substitute for an accredited independent audit certificate or official declaration."),
            ("Tesis / Tüketim Profili:", "Facility / Consumption Profile:"),
            ("Toplam Tüketim:", "Total Consumption:"),
            ("Temiz Enerjiden Karşılanan:", "Supplied from Clean Energy:"),
            ("Önlenen Karbon Emisyonu:", "Avoided Carbon Emissions:"),
            ("ton CO2", "tons CO2"),
            ("Kapsam 2 Karbon Yoğunluğu:", "Scope 2 Carbon Intensity:"),
            ("COP31 ESG Derecesi:", "COP31 ESG Rating:"),
            ("Kaynak: EPİAŞ Şeffaflık Platformu & GHG Protocol Scope 2", "Source: EPİAŞ Transparency Platform & GHG Protocol Scope 2"),
            ("Tarih_Saat,Tesis_Tuketimi_MWh,Yenilenebilir_Karsilanan_MWh,Fosil_Sebeke_Tuketimi_MWh,Temiz_Enerji_Payi_Yuzde", "Timestamp,Facility_Consumption_MWh,Renewable_Matched_MWh,Fossil_Grid_Consumption_MWh,Clean_Energy_Share_Pct"),
        ]
        for s, d in csv_replacements:
            text = text.replace(s, d)
        text = tr_text(text)
        return text.encode("utf-8-sig")
    except Exception:
        return data


def install_streamlit_i18n() -> None:
    if getattr(st, "_i18n_installed", False):
        return

    orig_markdown = st.markdown
    orig_tabs = st.tabs
    orig_selectbox = st.selectbox
    orig_segmented = st.segmented_control
    orig_plotly = st.plotly_chart
    orig_download = st.download_button
    orig_caption = st.caption
    orig_date_input = st.date_input
    orig_file_uploader = st.file_uploader
    orig_spinner = st.spinner
    orig_error = st.error
    orig_warning = st.warning
    orig_info = st.info

    def i18n_markdown(body, *args, **kwargs):
        if isinstance(body, str):
            if kwargs.get("unsafe_allow_html"):
                body = textwrap.dedent(body).strip()
            if not body.startswith("<style>"):
                body = tr_text(body)
        return orig_markdown(body, *args, **kwargs)

    def i18n_tabs(tabs, *args, **kwargs):
        translated_tabs = [tr_text(t) for t in tabs]
        return orig_tabs(translated_tabs, *args, **kwargs)

    def i18n_selectbox(label, options, *args, **kwargs):
        label = tr_text(label)
        if "format_func" not in kwargs:
            kwargs["format_func"] = tr_text
        return orig_selectbox(label, options, *args, **kwargs)

    def i18n_segmented(label, options, *args, **kwargs):
        if kwargs.get("key") == "app_lang_selector":
            return orig_segmented(label, options, *args, **kwargs)
        label = tr_text(label)
        if "format_func" not in kwargs:
            kwargs["format_func"] = tr_text
        return orig_segmented(label, options, *args, **kwargs)

    def i18n_plotly(figure_or_data, *args, **kwargs):
        figure_or_data = translate_plotly_figure(figure_or_data)
        return orig_plotly(figure_or_data, *args, **kwargs)

    def i18n_download(label, data, file_name=None, *args, **kwargs):
        label = tr_text(label)
        data = translate_csv_bytes(data)
        if isinstance(file_name, str) and get_lang() == "EN":
            file_name = file_name.replace("saatlik_projeksiyon", "hourly_projection")
            file_name = file_name.replace("COP31_Kapsam2_Karbon_Karnesi", "COP31_Scope2_Carbon_Report")
            file_name = tr_text(file_name).replace(" ", "_")
        return orig_download(label, data, file_name=file_name, *args, **kwargs)

    def i18n_caption(body, *args, **kwargs):
        return orig_caption(tr_text(body), *args, **kwargs)

    def i18n_date_input(label, *args, **kwargs):
        return orig_date_input(tr_text(label), *args, **kwargs)

    def i18n_file_uploader(label, *args, **kwargs):
        return orig_file_uploader(tr_text(label), *args, **kwargs)

    def i18n_spinner(text="In progress...", *args, **kwargs):
        return orig_spinner(tr_text(text), *args, **kwargs)

    def i18n_error(body, *args, **kwargs):
        return orig_error(tr_text(body), *args, **kwargs)

    def i18n_warning(body, *args, **kwargs):
        return orig_warning(tr_text(body), *args, **kwargs)

    def i18n_info(body, *args, **kwargs):
        return orig_info(tr_text(body), *args, **kwargs)

    st.markdown = i18n_markdown
    st.tabs = i18n_tabs
    st.selectbox = i18n_selectbox
    st.segmented_control = i18n_segmented
    st.plotly_chart = i18n_plotly
    st.download_button = i18n_download
    st.caption = i18n_caption
    st.date_input = i18n_date_input
    st.file_uploader = i18n_file_uploader
    st.spinner = i18n_spinner
    st.error = i18n_error
    st.warning = i18n_warning
    st.info = i18n_info
    st._i18n_installed = True
