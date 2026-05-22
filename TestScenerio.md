# Demo Öncesi Tam Test Senaryosu

> Demo video kaydından önce sistemin **uçtan uca** doğru çalıştığını
> kanıtlamak için adım adım test plani. Hiçbir adımı atlama — her
> tikleme video'da sorunsuz akmak için burada test edilmeli.
>
> Toplam tahmini süre: **30-40 dk** (cold start dahil).
>
> **Hedef tarayıcı:** Chrome veya Edge (gizli pencere — extension/cache
> karışmasın).

---

## 🔧 0. Ön hazırlık (kayda başlamadan 10 dk önce yap)

### 0.1 Servisleri uyandır

Render free tier 15 dk idle olunca uyuyor. İlk istekte 30 sn cold start
kaybı yaşamamak için warmup'u manuel tetikle:

```bash
gh workflow run warmup.yml -R batikanakdenizz/Hotel-Booking-System
```

~1 dk içinde 7 servisin hepsi sıcak.

**Doğrulama:**
```bash
curl -fsS https://hbs-gateway.onrender.com/health
# {"status":"ok","service":"gateway"} -- saniyede dönmeli
```

✅ Gateway sıcak.

### 0.2 Demo verilerinin yerinde olduğunu doğrula

```bash
# Postgres -- 7 şehirde 10 otel
curl -sS "https://hbs-gateway.onrender.com/api/v1/search?destination=Istanbul&check_in=2026-07-15&check_out=2026-07-18&guests=2" \
  -H "Accept-Encoding: identity" | head -c 200

# Mongo -- 46 yorum
curl -sS "https://hbs-gateway.onrender.com/api/v1/comments/hotels/439b7445-8ea3-4485-ab41-73d80107891f/distribution" \
  -H "Accept-Encoding: identity"
# total_comments 4 olmalı (Bosphorus Bay için)
```

Yoksa seed scriptlerini çalıştır:
```bash
python scripts/seed_demo_data.py        # Postgres
python scripts/seed_demo_comments.py    # Mongo
```

### 0.3 Tarayıcıyı temizle

- **Gizli pencere** aç (Ctrl+Shift+N veya Cmd+Shift+N)
- F12 → **Network** sekmesini aç, "Disable cache" tıkla
- F12 → **Console** sekmesini aç (hata çıkarsa hemen görmek için)

### 0.4 Demo için bir Firebase test kullanıcısı hazırla

İki kullanıcı kullanacaksın (video boyunca):

| Rol | Email | Niye |
|---|---|---|
| **Normal user** | `demo+user@example.com` | Booking + comment akışı |
| **Admin user** | Senin gerçek hesabın | Admin paneline erişim |

Eğer admin hesabın yoksa, kendi hesabını admin yap:
```bash
python scripts/promote_admin.py akdenizbatikan@hotmail.com
```

### 0.5 Hazır mıyım kontrol listesi

- [ ] `gh workflow run warmup.yml` çalıştırıldı, 7 servis sıcak
- [ ] Gateway `/health` 200 OK, saniyede dönüyor
- [ ] Search "Istanbul" 2 otel döndürüyor
- [ ] Comments distribution `total_comments > 0`
- [ ] Tarayıcı gizli pencere açık, DevTools açık, cache disabled
- [ ] Demo user için email/şifre hazır
- [ ] Admin hesabın `users.role='hotel_admin'`

---

## 🌐 1. Anasayfa — anonymous (oturum açık değil)

### TC-01: Anasayfa yükleniyor mu?

**Adımlar:**
1. https://hotel-booking-system-psi-beryl.vercel.app aç

**Beklenen:**
- ✅ Hero başlık: "Find your next stay..."
- ✅ Üst header'da `Stayfinder` logo + sağ üstte **Sign in / Sign up** butonları
- ✅ Search bar (Destination / Check-in / Check-out / Guests / Search)
- ✅ Sayfa aşağı kaydırılınca **Popular destinations** grid — 7 kart: Rome / Paris / Istanbul / Barcelona / New York / Tokyo / Bodrum
- ✅ "Value props" kutucukları: Trusted bookings / 15% member discount / AI travel concierge
- ✅ Sağ alt köşede coral renkli yuvarlak **AI chat butonu** (💬 ikonu)
- ✅ Footer: "Stayfinder · SE 4458 — Final project"

**Hata varsa:** Console'da kırmızı? Network'te 4xx/5xx? Screenshot al, yaz.

---

### TC-02: Popular destination kartlarına tıklama

**Adımlar:**
1. **Istanbul** kartına tıkla.

**Beklenen:**
- ✅ URL: `/search?destination=Istanbul&check_in=...&check_out=...&guests=2`
- ✅ SearchResults sayfasına yönlendirilir
- ✅ "Istanbul · 2 stays" başlığı (undefined değil!)
- ✅ 2 otel kartı listelenir: **Bosphorus Bay Hotel** ⭐⭐⭐⭐⭐ + **Sultanahmet Palace** ⭐⭐⭐⭐⭐
- ✅ Sağdaki harita yüklenir, 2 marker görünür, **tile'lar tam** (kesik kesik değil)

**Eğer harita kesik:** Hard refresh (Ctrl+Shift+R).

---

## 🔍 2. Search akışı — anonymous

### TC-03: Manuel search

**Adımlar:**
1. Anasayfaya geri dön (header'daki Stayfinder logosuna tıkla)
2. Search bar'a doldur:
   - Destination: `Rome`
   - Check-in: `2026-07-15`
   - Check-out: `2026-07-18`
   - Guests: `2`
3. **Search** butonuna bas

**Beklenen:**
- ✅ URL parametreleri doğru oluşur
- ✅ 2 otel: **Trastevere Boutique** ⭐⭐⭐ + **Hotel Roma Plaza** ⭐⭐⭐⭐
- ✅ "Rome · 2 stays" başlığı
- ✅ Otel kartlarında fiyat görünür ($180/night)
- ✅ **"Member 15% off"** etiketi **GÖRÜNMEMELİ** (anonim olduğun için indirim yok)
- ✅ Harita Rome odaklı, 2 marker

---

### TC-04: Sort dropdown

**Adımlar:**
1. Aynı search sayfasında sağ üstteki sort dropdown'a tıkla
2. "Price (low to high)" seç

**Beklenen:**
- ✅ Otel kartları fiyata göre yeniden sıralanır

---

### TC-05: Boş sonuç (Berlin)

**Adımlar:**
1. Search bar'da Destination olarak `Berlin` yaz, Search bas

**Beklenen:**
- ✅ "Berlin · 0 stays" başlığı
- ✅ "No hotels available for these dates." mesajı
- ✅ Crash olmaz, harita boş kalır

---

## 🏨 3. Otel detayı — anonymous

### TC-06: Otel detay sayfası açma

**Adımlar:**
1. Istanbul search sonuçlarında **Bosphorus Bay Hotel** kartına tıkla

**Beklenen:**
- ✅ URL: `/hotels/{uuid}?check_in=...&check_out=...&guests=2`
- ✅ Hero görseli + otel adı + adres + 5 yıldız etiketi
- ✅ "About this stay" → açıklama metni
- ✅ Amenities chip'leri (WiFi / Breakfast / Pool vs.)
- ✅ "Available rooms" — 2-3 oda tipi listelenir (Standard Double, Suite, vs.)
- ✅ "Guest ratings" kartı:
  - "Toplam X reviews" sayısı
  - 7.3 / 10 gibi ortalama puan
  - **Yatay bar chart (Recharts)** — Cleanliness / Staff / Amenities / Comfort / Eco-friendly
- ✅ "Reviews" başlığı altında **yorum kartları** (4 kullanıcı görünür)
- ✅ Sağda sticky booking widget:
  - "From $140 /night"
  - Check-in / Check-out / Guests gösteriliyor
  - **"Sign in to book"** butonu (henüz login değilsin)
  - Alt notta: "Members save 15% — Sign up" linki

---

### TC-07: Oda seçimi (login olmadan)

**Adımlar:**
1. Otel detay sayfasında bir odaya tıkla (Standard Double)

**Beklenen:**
- ✅ Oda highlight olur, mavi border alır
- ✅ Sticky widget altında özet: "Standard Double · 3 nights · $420.00"
- ✅ Buton "Sign in to book" diyor

**Adımlar (devam):**
2. "Sign in to book" butonuna bas

**Beklenen:**
- ✅ Login sayfasına yönlendirilir
- ✅ URL: `/login?next=%2Fhotels%2F...` (redirect parametresi var)

---

## 🔐 4. Authentication

### TC-08: Sign up (yeni kullanıcı)

**Adımlar:**
1. Header'dan **Sign up** veya `/signup` URL'sine git
2. Form doldur:
   - Display name: `Demo User`
   - Email: `demo+test1@example.com` _(her test için unique olsun)_
   - Password: `Test1234!`
3. **Sign up** bas

**Beklenen:**
- ✅ Toast: "Account created!" (yeşil)
- ✅ Anasayfaya yönlendirilir (`/`)
- ✅ Header'da artık **My Bookings / Admin / Kullanıcı adın / Logout** butonları
- ✅ Sağ üstte avatar/kullanıcı chip'inde "Demo User" yazıyor

---

### TC-09: Sign in (mevcut kullanıcı)

**Adımlar:**
1. Header'dan **Logout** bas
2. Header'dan **Sign in** bas, formu doldur (yukarıdaki email/password)
3. **Sign in** bas

**Beklenen:**
- ✅ Toast: "Welcome back!"
- ✅ Anasayfaya geri dön
- ✅ Header user state'i tekrar görünür

---

### TC-10: Google ile giriş (opsiyonel, kayıtta varsa göster)

**Adımlar:**
1. Logout yap
2. `/login` aç
3. "Continue with Google" bas
4. Google popup'tan hesap seç

**Beklenen:**
- ✅ Yeni sekmede Google auth, sonra ana siteye dön
- ✅ Toast: "Signed in with Google"

**Eğer hata:** `auth/unauthorized-domain` → Firebase Console → Authentication → Settings → Authorized domains → `hotel-booking-system-psi-beryl.vercel.app` ekli mi kontrol et.

---

## 💰 5. 15% discount doğrulama

### TC-11: Login durumunda fiyat değişikliği

**Adımlar:**
1. **Login durumda** Istanbul ara → Bosphorus Bay Hotel'i aç
2. Oda fiyatlarına bak

**Beklenen:**
- ✅ Standard Double odanın fiyatı **üstü çizili `$140`** + altında **kırmızı/coral `$119.00`** (15% indirimli)
- ✅ Kartta **"Member 15% off"** etiketi var
- ✅ Search sayfasında otel kartında da "Member 15% off" rozeti

**Karşılaştırma:**
- Logout yapıp aynı otele bak → tek fiyat `$140`, indirim yok

---

## 📅 6. Booking akışı

### TC-12: Rezervasyon oluşturma

**Adımlar (login olmuş halde):**
1. Bosphorus Bay Hotel detayında **Standard Double** odasını seç
2. Sağ sticky widget'taki **"Book now"** butonuna bas

**Beklenen:**
- ✅ Buton spinner göstererek loading state'e geçer
- ✅ ~1-2 sn sonra toast: "Booking confirmed"
- ✅ `/my-bookings` sayfasına otomatik yönlendirilir
- ✅ Listede **yeni booking** görünür:
  - Confirmed badge (yeşil)
  - Check-in / Check-out tarihleri
  - Guests sayısı
  - Toplam fiyat
  - **"Cancel" butonu**

**Background'da olması gerekenler (görünmez ama olur):**
- Postgres'te `bookings` row'u oluşur
- `room_availability` o dates için decrement olur
- RabbitMQ'ya `reservation.created` event publish edilir
- Notification-service consumer tetiklenir, Resend ile mail atar

---

### TC-13: Mail kontrolü

**Adımlar:**
1. Sign up'ta kullandığın email kutusunu aç (`demo+test1@example.com` → eğer gerçek bir email kullandıysan)

**Beklenen:**
- ✅ 1-2 dk içinde "Reservation Confirmed — Bosphorus Bay Hotel" mail'i gelir
- ✅ Mail içeriğinde otel adı, tarihler, fiyat var

**Not:** Eğer `example.com` gibi sahte email kullandıysan mail gelmez (Resend test domain `onboarding@resend.dev`'den sadece doğrulanmış adreslere gönderir). Test için kendi gerçek email'ini kullan.

---

### TC-14: My Bookings sayfası

**Adımlar:**
1. Header'dan **My Bookings** tıkla

**Beklenen:**
- ✅ Bookings listesi yüklenir
- ✅ Yeni booking + (varsa) seed'den gelen örnek bookings
- ✅ Cancelled olanlar kırmızı rozetli
- ✅ Confirmed olanlar yeşil rozetli, Cancel butonu var

---

### TC-15: Booking iptali

**Adımlar:**
1. Yeni booking'in **Cancel** butonuna bas
2. Confirm dialog'unda **OK** bas

**Beklenen:**
- ✅ Buton loading
- ✅ Toast: "Booking cancelled"
- ✅ Sayfa yenilenir, ilgili booking artık kırmızı **Cancelled** rozetli, Cancel butonu kaybolur

---

## 💬 7. Yorumlar (Comments)

### TC-16: Yorum yazma

**Adımlar (login olmuş halde):**
1. Bosphorus Bay Hotel detayına git
2. "Reviews" bölümünde "Leave a review" formuna in
3. Text alanına yaz: `Harika bir konaklama deneyimi yaşadım. Manzara muhteşemdi, personel çok ilgiliydi.`
4. 5 boyutu doldur:
   - Cleanliness: `10`
   - Staff: `9`
   - Amenities: `8`
   - Comfort: `10`
   - Eco-friendly: `7`
5. **Post review** bas

**Beklenen:**
- ✅ Toast: "Comment posted"
- ✅ Yorum listesi en üstünde **senin yorumun** görünür
- ✅ Sağ üstte ortalama puan ⭐ 8.8 gibi gösterilir
- ✅ "Guest ratings" toplam yorum sayısı +1 oldu
- ✅ Recharts grafiğindeki bar'lar güncellendi

---

### TC-17: Yorum dağılımı (5-dim chart)

**Adımlar:**
1. Hotel detail sayfası, "Guest ratings" kartı

**Beklenen:**
- ✅ Yatay bar chart 5 satır: Cleanliness / Staff / Amenities / Comfort / Eco
- ✅ Her bar 0-10 ölçekli
- ✅ Ortalama puan üstte gösterilir (örn. **8.2 / 10**)
- ✅ Hover ile bar'a gelirsen tooltip değer gösterir

---

## 🤖 8. AI Agent

### TC-18: AI chat widget açma

**Adımlar:**
1. Herhangi bir sayfada sağ alt köşedeki **coral renkli yuvarlak buton**a tıkla

**Beklenen:**
- ✅ Sağ altta küçük chat penceresi açılır (Framer Motion animasyonu)
- ✅ Üstte "Stayfinder AI · Powered by Llama 3.3 via Groq"
- ✅ Karşılama mesajı: "Hi! I'm Stayfinder's AI concierge..."

---

### TC-19: AI ile otel arama

**Adımlar:**
1. Chat input'una yaz:
   ```
   Find me a hotel in Rome from 2026-07-15 to 2026-07-18 for 2 guests
   ```
2. **Send** (veya Enter)

**Beklenen:**
- ✅ Senin mesajın sağda mavi bubble
- ✅ "…thinking" göstergesi
- ✅ ~3-5 sn sonra AI cevabı:
  - 2 otel listeler (Trastevere Boutique + Hotel Roma Plaza)
  - Her biri için yıldız + fiyat
  - "Let me know if you want to book or see comments" gibi follow-up

**Background:** AI agent → Groq → tool_call(`search_hotels`) → gateway → search-service → Postgres → cevap → LLM özetler.

---

### TC-20: AI ile yorum gösterme

**Adımlar:**
1. Aynı chat'te devam:
   ```
   Show me comments for the first hotel
   ```

**Beklenen:**
- ✅ AI son listelenen ilk otelin hotel_id'sini hatırlar
- ✅ tool_call(`get_hotel_comments`) yapar
- ✅ Cevap olarak: "X reviews, avg 7.3/10, top recent: ..."

---

### TC-21: AI ile booking (login durumdayken)

**Adımlar:**
1. Chat'te:
   ```
   Book the first room of the first hotel
   ```

**Beklenen:**
- ✅ AI önce **doğrulama** ister: "Are you sure you want to book ... ?"
- ✅ Sen "yes" diyince tool_call(`book_hotel`) yapar
- ✅ Booking oluşur (toast: "Booking confirmed")
- ✅ AI cevabı: "Done! Your reservation ID is ..."

---

## 🛠️ 9. Admin paneli

### TC-22: Admin sayfasına erişim

**Önkoşul:** Login olduğun user `users.role = 'hotel_admin'`. Değilse:
```bash
python scripts/promote_admin.py akdenizbatikan@hotmail.com
```

**Adımlar:**
1. Header'dan **Admin** linkine tıkla
2. `/admin/hotels` sayfasına git

**Beklenen:**
- ✅ Hotels listesi (Pagination Page 1 · 10 of 10)
- ✅ Her kart: hotel name + destination + yıldız + ID + description
- ✅ Üst sağda "New hotel" butonu

**Eğer 401/403:** Admin değilsin → console'da `Failed to load hotels` mesajı → role'ünü Postgres'te kontrol et.

---

### TC-23: Yeni otel oluşturma

**Adımlar:**
1. **New hotel** bas
2. Form doldur:
   - Name: `Test Hotel Demo`
   - Destination: `Test City`
   - Address: `1 Demo Street`
   - Latitude: `41.0`
   - Longitude: `28.0`
   - Admin email: `admin@test.com`
   - Star rating: `4`
   - Amenities: `WiFi, Breakfast`
   - Description: `Created during demo recording`
3. **Create** bas

**Beklenen:**
- ✅ Toast: "Hotel created"
- ✅ Form kapanır
- ✅ Listede en üstte yeni hotel görünür (admin-hotels query refresh oldu)

---

## ⚡ 10. Edge case'ler

### TC-24: Geçmiş tarih ile search

**Adımlar:**
1. Anasayfada Check-in: `2020-01-01`, Check-out: `2020-01-03`

**Beklenen:**
- ✅ Search çalışır, "0 stays" döner (geçmiş tarihlerde availability yok)
- ✅ Hata vermez, crash olmaz

---

### TC-25: Check-out < Check-in

**Adımlar:**
1. Check-in: `2026-07-18`, Check-out: `2026-07-15` (ters)
2. Search bas

**Beklenen:**
- ✅ Frontend validation: "Check-out must be after check-in" hata mesajı
- ✅ Request gönderilmez

---

### TC-26: Logout sonrası protected route

**Adımlar:**
1. Logout yap
2. Direkt URL'de `/my-bookings` aç

**Beklenen:**
- ✅ Login sayfasına yönlendirilir
- ✅ URL: `/login?next=%2Fmy-bookings`
- ✅ Login olunca `/my-bookings`'a geri dönerin

---

### TC-27: AI chat oturumdayken

**Adımlar:**
1. Chat'i kapatmadan başka sayfaya git (örn. /hotels/...)
2. Geri dön ve chat butonuna bas

**Beklenen:**
- ✅ Chat penceresi YENİ session ile açılır (in-memory state, sayfa değişince reset)
- ✅ Hata vermez

---

## ⏱️ 11. Performance + cold-start

### TC-28: Cold-start kontrolü

**Bu testi demoda göstermiyorsun ama önceden bil:**

15+ dk inactive bırak → ana sayfaya gel → search yap

**Beklenen:**
- İlk istek ~30 sn (cold start) — gateway ve search uyanır
- Sonraki tüm istekler <1 sn

**Demo öncesi:** Warmup workflow tetiklemen şart, soğuk başlama gözükmesin.

---

### TC-29: Network panel — tüm istekler 200

**Adımlar:**
1. F12 → Network sekmesi açık
2. Tüm yukarıdaki test case'leri yaparken kontrol et

**Beklenen:**
- ✅ Tüm `api/v1/*` istekleri **200, 201, 204** veya beklenen status code
- ✅ Hiçbiri **502, 504** vermez (cold start hariç)
- ✅ CORS hataları YOK (kırmızı yazılar Console'da)

---

## ✅ Final checklist (kaydı başlatmadan önce)

- [ ] TC-01 ile TC-23 arası hepsi yeşil
- [ ] Console'da kırmızı yok
- [ ] Network'te 5xx yok
- [ ] AI chat doğru otel listesi döndürüyor
- [ ] Admin paneli yükleniyor
- [ ] Harita kesintisiz, tile'lar tam
- [ ] Comments distribution chart render oluyor
- [ ] Booking + cancel + comment + admin işliyor
- [ ] Tarayıcının URL bar'ında doğru Vercel URL'i
- [ ] Render dashboard tabı açık (eğer servisleri göstereceksen)
- [ ] GCP Cloud Scheduler tabı açık (kısaca göstereceksen)
- [ ] GitHub repo açık (sonda göstereceksen)
- [ ] Mikrofon test edildi
- [ ] OBS / Loom kayıt tuşu hazır

---

## 🚨 Test sırasında bir şey kırılırsa

| Sorun | İlk müdahale |
|---|---|
| 502 Bad Gateway | Servis uyandı, ~30 sn bekle, retry |
| "undefined stays" | Hard refresh (Ctrl+Shift+R) |
| Harita kesik | Hard refresh + Network panel'de leaflet tiles 200 mü kontrol et |
| AI chat "function failed" | `/api/v1/agent/debug/search?destination=Rome` curl at, döndüğünü gör |
| Booking 401 | Token expire olmuş, logout/login |
| Comment POST 401 | Aynı, logout/login |
| Admin 403 | `python scripts/promote_admin.py <email>` çalıştır |
| Search 0 results | Seed boş, `python scripts/seed_demo_data.py` çalıştır |

---

## 📞 Acil destek

- Render dashboard: https://dashboard.render.com
- Vercel dashboard: https://vercel.com/dashboard
- GCP Cloud Scheduler: https://console.cloud.google.com/cloudscheduler
- Firebase Console: https://console.firebase.google.com
- GitHub Actions (warmup): https://github.com/batikanakdenizz/Hotel-Booking-System/actions
- Servis health URL'leri:
  - https://hbs-gateway.onrender.com/health
  - https://hbs-admin-service.onrender.com/health
  - https://hbs-search-service.onrender.com/health
  - https://hbs-booking-service.onrender.com/health
  - https://hbs-comments-service.onrender.com/health
  - https://hbs-notification-service.onrender.com/health
  - https://hbs-ai-agent-service.onrender.com/health
- AI agent debug endpoint:
  - https://hbs-gateway.onrender.com/api/v1/agent/debug/config
  - https://hbs-gateway.onrender.com/api/v1/agent/debug/search?destination=Istanbul

---

**Bu listenin tamamı yeşil → video çekimine geç.** İlk hata varsa bana yaz, beraber düzeltelim, sonra kayda başla.
