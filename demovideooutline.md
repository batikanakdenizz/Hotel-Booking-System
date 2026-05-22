# 🎬 Demo Video Taslağı — Hotel Booking System

> **Süre:** ≤ 5:00 dakika (guideline şartı)
> **Format:** Ekran kaydı + voiceover, Türkçe anlatım
> **Hedef:** Hocaya **5 dakikada** tüm önemli özellikleri kanıtlamak
>
> Bu doku okumak için optimize edildi. Her sahnede **mavi italik metni** sesli oku,
> **kalın aksiyonları** ekranda yap. Süre tahminleri rehber, ±5 sn esneklik var.

---

## 🔧 KAYIT ÖNCESİ HAZIRLIK (5 dk)

- [ ] Warmup pingleri çalıştır: `gh workflow run warmup.yml -R batikanakdenizz/Hotel-Booking-System`
- [ ] 7 servisin Live olduğunu Render dashboard'da doğrula
- [ ] Tarayıcıda **2 sekme** aç:
  - **Sekme 1:** https://hotel-booking-system-psi-beryl.vercel.app (gizli pencere, hard refresh yapılmış)
  - **Sekme 2:** https://github.com/batikanakdenizz/Hotel-Booking-System (README görünür)
- [ ] Demo için bir test hesabı hazır (örn. `demo+video@test.com` / `Test1234!`)
- [ ] Mikrofon test edildi, gürültü filtresi açık (varsa)
- [ ] OBS / Loom kayıt çözünürlüğü **1920×1080**, frame rate **30 fps**
- [ ] Masaüstü dağınıklığı kapatıldı (yalnızca tarayıcı görünsün)

---

## 🎬 SAHNE 1 — Açılış [00:00 → 00:25]

**Ekran:** GitHub repo ana sayfası açık (README görünür).

**Aksiyon:** Hiçbir tıklama yapma, README'nin başlığında dur.

**Sen oku (25 sn):**

> Merhaba, ben Batikan Akdeniz. SE 4458 Software Architecture dersi
> Group 1 final projesi olarak geliştirdiğim **Hotel Booking System**'i
> sunuyorum. Hotels.com benzeri, mikroservis mimarisinde çalışan,
> gerçek bulut altyapısında deploy edilmiş bir otel rezervasyon
> platformu. Bugün size hem teknolojik temellerinden hem de canlı
> ortamdan kısa bir tur atacağım.

---

## 🎬 SAHNE 2 — Teknoloji yığını ve mimari [00:25 → 01:10]

**Ekran:** README'de "Tech stack" tablosuna scroll et. Sonra "Architecture"
diagramına in.

**Aksiyon:** Tech stack tablosunda 3 sn dur, mimari diagram'a kaydır.

**Sen oku (45 sn):**

> Backend tarafında **Python 3.12 ve FastAPI**, async SQLAlchemy 2 ile
> Postgres'e, Motor ile MongoDB'ye bağlanan **7 ayrı mikroservis**
> var: gateway, admin, search, booking, comments, notification ve AI
> agent.
>
> Veritabanları tamamen bulut tabanlı: **Supabase Postgres**,
> **MongoDB Atlas**, ve dağıtık cache için **Upstash Redis**.
> Rezervasyon eventlerini taşımak için **CloudAMQP RabbitMQ** kuyruğunu
> kullanıyoruz. Authentication, guideline'ın istediği gibi harici bir
> IAM servisi olan **Firebase Authentication** ile yapılıyor.
>
> Frontend tarafında **React 19, TypeScript ve Vite**; harita için
> Leaflet, grafikler için Recharts, AI chat için Framer Motion var.
>
> Tüm backend Docker container'ları **Render'da**, frontend **Vercel'in
> CDN'inde**, gece çalışan cron görevi de **Google Cloud Scheduler**'da
> deploy edilmiş durumda.

---

## 🎬 SAHNE 3 — Anasayfa ve search akışı [01:10 → 01:45]

**Ekran:** Vercel sekmesine geç → anasayfa.

**Aksiyon:**
1. Hero alanını ve "Popular destinations" kartlarını göster
2. Arama çubuğuna **Istanbul** yaz (autocomplete dropdown'unu göster)
3. Dropdown'dan "Istanbul"u seç
4. Check-in ve check-out tarihlerini birkaç gün ileriye ayarla
5. **Search** butonuna bas

**Sen oku (35 sn):**

> Anasayfada hero alanının altında React Hook Form ve Zod ile valide
> edilen bir search bar var. Şehir isimlerinde **İstanbul-Istanbul**
> karışıklığını önlemek için autocomplete dropdown ekledim — Türkçe
> noktalı I farketmeden, dropdown'dan kanonik ismi seçiyor.
>
> Şimdi Istanbul'a, ileri tarihli iki gece için 2 misafirle bir arama
> yapıyorum.

---

## 🎬 SAHNE 4 — Search results + harita + cache [01:45 → 02:25]

**Ekran:** Search results sayfası açık (sonuçlar yüklendi).

**Aksiyon:**
1. Solda 2 otel kartını göster (Bosphorus Bay + Sultanahmet Palace)
2. Fiyat etiketini (örn. `$140/night`) **işaret et** — bu anonim kullanıcı için
3. Sağdaki Leaflet haritasını göster, marker'lara hover yap
4. F12 ile Network panelini kısa süre aç → search isteğinin yaklaşık 300 ms cevap verdiğini göster, sonra kapat

**Sen oku (40 sn):**

> Sonuç sayfasında iki otel listelendi: Bosphorus Bay Hotel ve
> Sultanahmet Palace. Sağda guideline'ın istediği **"Haritada göster"**
> özelliği — react-leaflet ile CartoDB Voyager tile'larını kullanıyor.
> Her marker bir hotel ve hover ile bilgi gösteriyor.
>
> Network panelinde gördüğünüz gibi, bu sorgu yaklaşık 300 milisaniyede
> tamamlandı. Çünkü search-service otel-detayını Upstash Redis'te
> `hotel:{uuid}` anahtarıyla **24 saatlik TTL** ile cache'liyor. Oda
> müsaitliği ise **asla cache'lenmiyor** — her sorguda Postgres'ten
> taze okunuyor, çünkü dolu odayı asla satmamak istiyoruz.

---

## 🎬 SAHNE 5 — Otel detayı + 15% indirim [02:25 → 03:00]

**Ekran:** Bir otele tıkla — örneğin **Bosphorus Bay Hotel**.

**Aksiyon:**
1. Otel detay sayfasını yükle
2. "Available rooms" bölümünde Double odasını işaret et — fiyat **$140**
3. Recharts'lı 5 boyutlu rating chart'ı göster (cleanliness/staff/amenities/comfort/eco)
4. Yorum kartlarını birkaç saniye göster
5. **Header'dan Sign in** → daha önce açtığın test hesabıyla giriş yap
6. Sayfa yenilendiğinde — fiyat artık üstü çizili **$140** + coral **$119** ve "Member 15% off" rozeti
7. Bu fiyat değişikliğini **belirgin şekilde göster**

**Sen oku (35 sn):**

> Otel detayında sağda sticky bir booking widget, ortada odalar ve
> guideline'ın istediği **5 boyutlu rating distribution**: Cleanliness,
> Staff, Amenities, Comfort, Eco-friendliness. Bu grafik MongoDB'de
> tek bir aggregation pipeline ile, `$group` ve `$bucket` operatörleri
> kullanılarak hesaplanıyor.
>
> Şu an **anonim kullanıcıyım**, Double oda 140 dolar.
> Şimdi giriş yapıyorum...
> **[login sonrası]**
> Görüldüğü gibi aynı oda artık 119 dolara düştü — guideline'ın istediği
> **%15 üye indirimi** runtime'da uygulanıyor, search-service kullanıcının
> kimliğini gateway'in forward ettiği token'dan algılıyor.

---

## 🎬 SAHNE 6 — Rezervasyon + RabbitMQ akışı [03:00 → 03:40]

**Ekran:** Aynı otel detayı, login durumdayız.

**Aksiyon:**
1. Double odayı seç (mavi border alır)
2. Sağ widget'taki **"Book now"** butonuna bas
3. Toast'u göster: "Booking confirmed"
4. `/my-bookings` sayfasına otomatik yönlendirme olunca yeni booking'i göster (yeşil "Confirmed" rozeti)
5. Toplam fiyatı işaret et

**Sen oku (40 sn):**

> "Book now" butonuna bastığımda, booking-service tek bir Postgres
> transaction'ında üç iş birden yapıyor: önce `room_availability`
> satırlarını `SELECT FOR UPDATE` ile kilitleyip oda sayısını
> azaltıyor, sonra booking kaydını oluşturuyor, ve commit'ten sonra
> RabbitMQ'ya `reservation.created` event'i yayınlıyor — durable
> exchange, persistent message ve `tenacity` ile 3 retry'lı
> exponential backoff.
>
> Bu event'i notification-service consumer olarak dinliyor ve Resend
> üzerinden onay maili gönderiyor. My Bookings sayfasında booking
> hemen göründü, Confirmed rozeti yeşil, toplam fiyat doğru
> hesaplanmış.

---

## 🎬 SAHNE 7 — AI Agent canlı demo [03:40 → 04:30]

**Ekran:** Herhangi bir sayfa. Sağ altta floating coral buton.

**Aksiyon:**
1. AI chat butonuna tıkla → panel açılır, "Hi! I'm Stayfinder's AI concierge..." görünür
2. Chat input'una **yaz** (ya da yapıştır):
   ```
   Find me a hotel in Rome from July 15 to July 18 for 2 guests
   ```
3. Send'e bas → 2-3 sn bekle
4. AI cevabı çıkar — iki Rome oteli listeler, yıldız ve fiyat ile birlikte
5. Cevabı 3-5 sn göster

**Sen oku (50 sn):**

> Sıradaki en önemli özellik **AI agent**. Sağ alttaki butonla chat
> widget'ı açtım. Bu kısım guideline'da istenen "AI agent that uses
> your APIs" özelliği — sadece bir LLM wrapper'ı değil, **gerçek bir
> tool-calling loop**.
>
> Şimdi doğal dilde soruyorum: "Find me a hotel in Rome from July 15
> to July 18 for 2 guests."
>
> Arka planda şu oluyor: bu mesaj ai-agent-service'e gidiyor, oradan
> **Groq'un Llama 3.3 70B** modeline OpenAI-uyumlu function-calling
> protokolüyle yollanıyor. LLM `search_hotels` tool'unu çağırıyor,
> ai-agent bu çağrıyı kendi platformumuzdaki gateway'in REST API'sine
> dönüştürüyor, sonuçları LLM'e geri veriyor, ve LLM doğal dilde
> formatlıyor.
>
> İşte cevap geldi: Trastevere Boutique ve Hotel Roma Plaza, yıldız
> ve fiyat bilgisiyle birlikte. Kullanıcı isterse aynı widget'tan
> "Book the first one" diyerek rezervasyon da yapabilir.

---

## 🎬 SAHNE 8 — Admin paneli + nightly cron [04:30 → 04:50]

**Ekran:** Header'dan **Admin** linkine tıkla.

**Aksiyon:**
1. `/admin/hotels` sayfası — 10 otelin listesi
2. "New hotel" butonunu **işaret et ama tıklama**
3. Hızla GCP Cloud Scheduler sekmesini aç (alttabd) → `hbs-nightly-occupancy` job'unu göster

**Sen oku (20 sn):**

> Admin paneline geçtim. Hotel admin'leri buradan otel ve odaları
> yönetiyor, guideline'ın "authenticated admin service" şartına uygun
> olarak Firebase JWT ve Postgres'teki `users.role = hotel_admin` ile
> çift katmanlı korunuyor.
>
> Son olarak, Google Cloud Scheduler dashboard'unda gece 02:00'da
> `notification-service`'in `/trigger/nightly` endpoint'ini çağıracak
> cron job'u kurulu — bu da guideline'ın istediği nightly scheduled
> task.

---

## 🎬 SAHNE 9 — Kapanış + deliverables [04:50 → 05:00]

**Ekran:** GitHub repo sayfası (README görünür).

**Sen oku (10 sn):**

> Tüm kaynak kod GitHub'da public olarak erişilebilir, README'de
> mimari diyagramı, ER, deploy talimatları ve doğrulama scriptleri
> mevcut. Vakit ayırdığınız için teşekkürler.

---

## 📋 KAYIT SONRASI

- [ ] Videoyu **YouTube'a unlisted** olarak yükle (özel istemiyorsan)
- [ ] Linki kopyala
- [ ] README'de **"Demo video"** satırındaki `_link to be added after recording_`
      kısmını YouTube linkiyle değiştir
- [ ] Aynı linki **TestScenerio.md**'nin de altına ekleyebilirsin (referans için)
- [ ] Commit + push:
  ```bash
  git add README.md
  git commit -m "docs: add demo video link"
  git push
  ```
- [ ] Hocaya gönderdiğin teslim mailine link ekle

---

## 🚨 KAYDA BAŞLAMADAN SON KONTROL

- [ ] Mikrofon ses seviyesi iyi
- [ ] Ekran kaydı 1920×1080, 30 fps
- [ ] Tarayıcı tam ekran, sekmeler temiz
- [ ] Vercel sayfası açık, oturumum kapalı (Sign in akışını gösterebilmek için)
- [ ] Render dashboard 7 servis "Live"
- [ ] Bu doku ikinci ekranda veya yazıcıdan basılmış halde önünde
- [ ] Su iç, bir kere boğazını temizle, kayıt tuşuna bas

---

## ⏱️ Toplam süre öngörüsü

| Sahne | Süre | Birikimli |
|---|---|---|
| 1 — Açılış | 0:25 | 0:25 |
| 2 — Tech stack + mimari | 0:45 | 1:10 |
| 3 — Anasayfa + search | 0:35 | 1:45 |
| 4 — Sonuçlar + harita + cache | 0:40 | 2:25 |
| 5 — Otel detayı + 15% indirim | 0:35 | 3:00 |
| 6 — Booking + RabbitMQ | 0:40 | 3:40 |
| 7 — AI Agent | 0:50 | 4:30 |
| 8 — Admin + nightly cron | 0:20 | 4:50 |
| 9 — Kapanış | 0:10 | **5:00** ✅ |

Eğer ilk denemede 5 dakikayı geçersen:
- **Sahne 2** (tech stack) — README'yi göstermek yerine sadece sözlü hızlıca geç
- **Sahne 4** — Network panelini açma, sadece sonuçları ve haritayı göster
- **Sahne 8** — Admin panelinin sadece listesini göster, GCP'yi atla

Eğer 4 dakikanın altında biterse:
- **Sahne 5** — bir comment yaz ve chart'ın anında güncellenmesini göster (+20 sn)
- **Sahne 7** — AI'a follow-up soru sor: "Show me comments for the first hotel" (+30 sn)

**Bol şanslar!** 🎬
