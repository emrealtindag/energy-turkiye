# Antigravity görev talimatı: yalnızca Streamlit arayüzü

Bu projede iş bölümü nettir: **Kaan veri katmanını hazırlıyor. Sen yalnızca Streamlit arayüzünü (`app.py`) ve gerekirse arayüz belgelerini geliştir.** Önce README'yi ve mevcut dosyaları oku.

## Kaan'ın sorumluluğu — değiştirme

Kaan `src/data_helper.py` içinde EPİAŞ API ve gerçek CSV yedeğini uygulayacak. Bu dosyaya dokunma, yeniden yazma veya EPİAŞ endpoint'i/temizleme mantığı ekleme. Fonksiyon imzası ve sütun adları Kaan'la henüz teyit edilecek; şimdilik README'deki taslak sözleşmeyi kullan ve entegrasyonun bu sözleşmeye bağlı olduğunu açıkça belirt.

## Senin sorumluluğun

1. `app.py` içinde tarih aralığı filtresi ve Türkçe, erişilebilir bir panel hazırla.
2. `src.data_helper.load_generation_data(start_date, end_date)` fonksiyonunu çağır. Gerçek fonksiyonun sağlayacağı alanlar: `timestamp`, `wind_mwh`, `solar_mwh`, `total_mwh` (Kaan'la teyit bekleyen taslak sözleşme).
3. Sayaç kartlarında rüzgâr üretimi, güneş üretimi, rüzgâr+güneş toplamı, toplam üretimdeki pay ve seçili dönemin saatlik rüzgâr+güneş zirvesini göster. Payı `(rüzgâr + güneş) / toplam üretim` ile hesapla; paydada toplam sıfır veya NaN ise bölme hatası verme, payı “Hesaplanamadı” göster.
4. Saatlik rüzgâr ve güneş üretimini Plotly zaman serisinde göster. Tarih ve saatleri `Europe/Istanbul` (UTC+3) zaman diliminde sun; UTC gelen zaman damgalarını Türkiye saatine dönüştür.
5. API/veri her widget etkileşiminde tekrar yüklenmesin diye veri çağrısında `st.cache_data(ttl=...)` kullan. Makul bir TTL seç ve README'de belirt.
6. Veri yükleniyor, veri yok ve veri kaynağı hatası durumlarını kullanıcıya Türkçe ve anlaşılır biçimde göster. Hata oluştuğunda uygulama çökmesin.
7. Metinlerde “canlı” yerine “güncel veri” kullan. Göstergeyi “rüzgâr + güneş payı” diye adlandır; “temiz enerji payı” deme. Açıklamada güneş üretiminin lisanssız üretim verileri nedeniyle eksik temsil edilebileceğini belirt.
8. README'ye Streamlit Cloud kurulumunu ekle/güncelle: GitHub deposunu bağlama, `app.py` seçme ve varsa secret'ları Streamlit Cloud **Settings → Secrets** alanına girme adımları. Gizli değerleri README'ye veya repoya koyma.

## Veri davranışı ve sınırlar

- Sıfır geçerli üretim değeridir; özellikle güneş için gece sıfırları silme veya doldurma.
- NaN ve eksik saatler için uydurma değer üretme, interpolasyon yapma. Varsa veri eksikliğini görünür biçimde belirt.
- Uydurma/sentetik üretim verisi ekleme. Gerçek CSV yedeğini Kaan `data/` altından okuyacak şekilde hazırlayacak; sen CSV okuma veya veri temizleme kodu yazma.
- Endpoint, veri alanı veya credential anahtarı tahmin etme.
- Sadece arayüz için gerekli dosyaları değiştir; `src/data_helper.py` değişikliklerini teslimde açıkça raporla ve geri al.

## Teslim ve doğrulama

Arayüzü yerel olarak açıp veri yok, veri hatası ve normal veri durumlarını ayrı ayrı doğrula. Normal görünümü yalnızca gerçek EPİAŞ verisi veya Kaan'ın sağladığı gerçek CSV ile doğrula; sentetik üretim kullanma. Sonunda değişen dosyaları ve doğrulama sonucunu kısa bir özetle bildir. Gizli bilgileri çıktıda gösterme.
