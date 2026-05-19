# Otel Rezervasyon Sistemi — Tam Proje Planı

**Ders:** SE 4458 Software Architecture & Design of Modern Large Scale Systems
**Ödev:** Bitirme Projesi — Grup 1 (Otel Rezervasyon Sistemi)
**Öğrenci:** Batıkan Akdeniz
**Plan versiyonu:** 1.0
**Son güncelleme:** 2026-05-17

> **Not:** Bu dosya `PROJECT_PLAN.md` dosyasının Türkçe çevirisidir. Kaynak kod, dosya/klasör isimleri, ortam değişkenleri, API endpoint'leri ve teknik terimler İngilizce olarak korunmuştur. Resmi proje artefaktı `PROJECT_PLAN.md` dosyasıdır.

---

## İçindekiler

1. [Proje Vizyonu ve Kapsam](#1-proje-vizyonu-ve-kapsam)
2. [Sabitlenmiş Teknoloji Yığını Kararları](#2-sabitlenmiş-teknoloji-yığını-kararları)
3. [Sistem Mimarisi](#3-sistem-mimarisi)
4. [Servis Kataloğu](#4-servis-kataloğu)
5. [Veri Modelleri](#5-veri-modelleri)
6. [API Spesifikasyonları](#6-api-spesifikasyonları)
7. [Depo (Repository) Yapısı](#7-depo-repository-yapısı)
8. [Harici Servisler — Manuel Kurulum Adımları](#8-harici-servisler--manuel-kurulum-adımları)
9. [Yerel Geliştirme Ortamı](#9-yerel-geliştirme-ortamı)
10. [Uygulama Fazları (Günlük)](#10-uygulama-fazları-günlük)
11. [Ortam Değişkenleri Referansı](#11-ortam-değişkenleri-referansı)
12. [Dağıtım (Deployment) Planı](#12-dağıtım-deployment-planı)
13. [Zamanlanmış Görevler Kurulumu](#13-zamanlanmış-görevler-kurulumu)
14. [Test Stratejisi](#14-test-stratejisi)
15. [Risk Kayıt Defteri ve Önlemler](#15-risk-kayıt-defteri-ve-önlemler)
16. [Demo ve Video Hazırlığı](#16-demo-ve-video-hazırlığı)
17. [Teslimat Kontrol Listesi](#17-teslimat-kontrol-listesi)
18. [Süre Tahmini](#18-süre-tahmini)

---

## 1. Proje Vizyonu ve Kapsam

SE 4458 Grup 1 Bitirme Projesi yönergesindeki 6 kullanım senaryosunu (use case) uygulayan, mikroservis tabanlı bir otel rezervasyon platformu inşa et:

- **Hotel Admin Service** — oteller ve oda müsaitliği için kimlik doğrulamalı CRUD
- **Hotel Search Service** — hedef + tarih + kişi sayısı arama; giriş yapmış kullanıcılar için %15 indirim
- **Book Hotel Service** — kapasite azaltma ile rezervasyon, kuyruğa event yayınlar
- **Hotel Comments Service** — 5 boyutlu puan dağılımıyla yorumlar (PDF mockup ile eşleşir: Temizlik / Personel ve servis / İmkân ve özellikler / Konaklama yerinin durumu / Çevre dostluğu)
- **Notification Service** — gecelik düşük kapasite uyarısı + rezervasyon onay tüketicisi (consumer)
- **AI Agent Service** — MCP tool'ları kullanarak sohbet tabanlı otel arama ve rezervasyon

**Karşılanan fonksiyonel olmayan gereksinimler:**

- Otel detayları için dağıtık önbellek (Upstash Redis)
- Yorumlar NoSQL veritabanında saklanır (MongoDB Atlas)
- Rezervasyonlar mesaj kuyruğuna yayınlanır (CloudAMQP üzerinden RabbitMQ)
- Harici IAM (Firebase Authentication) — yerel kimlik doğrulama yok
- Tek giriş noktası olarak API Gateway
- Versiyonlama (`/api/v1/`) ve sayfalama ile REST API'ler
- Her servise özel Dockerfile
- Bulut dağıtımı (Render + Vercel)
- Gecelik zamanlanmış görev (Google Cloud Scheduler)
- "Haritada göster" harita görünümü (Leaflet)
- Görsel yükleme — **ertelendi** (yalnızca olsa iyi olur)

**Toplam aylık maliyet:** $0 (tüm servisler ücretsiz katmanda).

---

## 2. Sabitlenmiş Teknoloji Yığını Kararları

### 2.1 Backend
| Bileşen | Seçim | Versiyon | Sebep |
|---|---|---|---|
| Dil | Python | 3.12 | Async, AI ekosistemi, tüm bağımlılıklar için olgun SDK'lar |
| Web framework | FastAPI | 0.115+ | Otomatik OpenAPI, Pydantic, async-native |
| ASGI sunucusu | Uvicorn | 0.32+ | Standart FastAPI çalışma zamanı |
| Doğrulama (Validation) | Pydantic | v2 | Tip-güvenli, hızlı, FastAPI'ye gömülü |
| ORM | SQLAlchemy | 2.x async | Standart, asyncpg ile async destek |
| Migration | Alembic | 1.13+ | Standart SQLAlchemy migration aracı |
| Postgres sürücüsü | asyncpg | 0.30+ | Async, en hızlı Python Postgres sürücüsü |
| MongoDB sürücüsü | Motor | 3.6+ | Async MongoDB sürücüsü |
| Redis istemcisi | redis-py (asyncio) | 5.2+ | Standart, async uyumlu |
| RabbitMQ istemcisi | aio-pika | 9.5+ | Async RabbitMQ, sağlam bağlantı yönetimi |
| Firebase Admin | firebase-admin | 6.6+ | JWT doğrulama için resmi Google SDK |
| HTTP istemcisi | httpx | 0.27+ | Async HTTP, gateway proxy ve AI agent tarafından kullanılır |
| Rate limiting | slowapi | 0.1.9+ | FastAPI uyumlu rate limiter |
| Logging | structlog | 24.4+ | Yapılandırılmış JSON log'lar |

### 2.2 AI Agent
| Bileşen | Seçim | Sebep |
|---|---|---|
| Protokol | Model Context Protocol (MCP) | 2025 Anthropic standardı, taşınabilir tool'lar |
| SDK | FastMCP (Python) | Dekoratör tabanlı tool kaydı |
| Taşıma (Transport) | stdio subprocess | Agent ile aynı container, ayrı deploy yok |
| LLM sağlayıcısı | Groq (birincil) | Ücretsiz katman, Llama 3.3 70B, düşük gecikme |
| LLM yedeği | OpenAI GPT-4o-mini (opsiyonel) | Kullanıcı OPENAI_API_KEY eklerse |
| Sohbet orkestrasyonu | Doğrudan httpx → Groq API | Hafif, üretimde LangChain bağımlılığı yok |

### 2.3 Veri Depoları
| Depo | Servis | Ücretsiz katman | Kullanıcı |
|---|---|---|---|
| İlişkisel | Supabase Postgres | 500 MB | admin, search, booking, notification |
| Doküman | MongoDB Atlas M0 | 512 MB | comments |
| Önbellek | Upstash Redis | 10k komut/gün, 256 MB | search (otel detay önbelleği) |
| Kuyruk | CloudAMQP Little Lemur | 1M mesaj/ay | booking → notification |

### 2.4 IAM ve Kimlik
| Bileşen | Seçim | Ücretsiz katman |
|---|---|---|
| IAM sağlayıcısı | Firebase Authentication | Sınırsız |
| Frontend SDK | `firebase` JS paketi | Ücretsiz |
| Backend doğrulama | `firebase-admin` Python | Ücretsiz |
| Token taksonomisi | Bearer (`Authorization` header'ında ID token) | — |

### 2.5 Frontend
| Bileşen | Seçim | Sebep |
|---|---|---|
| Build aracı | Vite | Hızlı HMR, modern |
| Dil | **TypeScript** | Type safety, portfolyo sinyali, backend OpenAPI ile tip paylaşımı |
| UI kütüphanesi | React 19 | En son stable, Suspense + concurrent özellikler |
| Component primitives | **shadcn/ui (Radix UI + Tailwind)** | Production kalitede accessible component'ler, customizable, modern industry standardı |
| Styling | **Tailwind CSS v4** | Utility-first, hızlı iterasyon, dark-mode native |
| Animasyon | **Framer Motion** | Sayfa/element geçişleri, kart hover, modal motion — wow factor |
| Server state | **TanStack Query (react-query)** | Caching, auto-refetch, optimistic updates — modern React veri-çekme standardı |
| Routing | react-router-dom v6 | Stable, nested route'lar |
| HTTP | axios + JWT interceptor | Tanıdık, TanStack Query ile entegre |
| Form'lar | **react-hook-form + zod** | Type-safe validation, performant, daha az re-render |
| Tarih picker | **react-day-picker** | Tarih aralığı native, accessible, themeable |
| Harita | react-leaflet + OpenStreetMap | Ücretsiz, API anahtarı yok |
| Grafik | Recharts | Hafif, React-native, declarative |
| İkonlar | **lucide-react** | Temiz SVG icon set, ~1000 ikon |
| Auth SDK | firebase JS | Firebase Auth entegrasyonu |
| Bildirimler | **sonner** (toast) | Modern toast kütüphanesi, shadcn uyumlu |

### 2.5.1 Tasarım prensipleri
- **Görsel referans:** Booking.com layout yapısı + Airbnb-warm modern estetik.
- **Palet:** Primary `#003580` (deep blue) veya `#ff5a5f` (Airbnb coral) — scaffold anında kilitlenecek. Accent `#feba02` (warm yellow). Nötr gri skalası (Tailwind `gray` veya `zinc`).
- **Tipografi:** Inter veya Manrope (variable font, modern hierarchy).
- **Spacing/radius:** Tailwind default'ları (kartlarda `rounded-xl`, cömert padding).
- **Mobile-first:** Her sayfa 375px genişlikte çalışmalı. Booking flow mobile'da bottom sheet olur.
- **Loading state'leri:** Skeleton component'leri (shadcn `Skeleton`), fetch sırasında asla boş ekran yok.
- **Empty state'leri:** Friendly illüstrasyon + CTA (örn. "Henüz rezervasyon yok — keşfetmeye başla →").
- **Error state'leri:** Geçici hatalar için toast (sonner), form hataları için inline mesajlar.
- **Erişilebilirlik:** Radix UI primitives a11y'yi halleder; icon'lara ARIA label ekle; chat widget ve admin tablolarında klavye navigasyonu test edilir.

### 2.6 Altyapı / DevOps
| Bileşen | Seçim | Ücretsiz katman |
|---|---|---|
| Backend hosting | Render | 750saat/servis/ay, Docker |
| Frontend hosting | Vercel | 100 GB bant genişliği |
| Zamanlayıcı (gecelik) | Google Cloud Scheduler | 3 iş/ay |
| Isındırma (warmup) pinger | cron-job.org | 50 iş |
| SMTP / E-posta | Resend | 100 e-posta/gün |
| CI | GitHub Actions | 2000 dk/ay |
| Container | Docker / Dockerfile (image commit yok) | — |

---

## 3. Sistem Mimarisi

### 3.1 Üst seviye diyagram

```
                   ┌─────────────────────────────────┐
                   │      React Frontend (Vercel)    │
                   │  • Login (Firebase)              │
                   │  • Search + Map (Leaflet)        │
                   │  • Hotel detail + Chart          │
                   │  • AI ChatWindow                 │
                   │  • Admin panel                   │
                   └─────────────────┬───────────────┘
                                     │ HTTPS + JWT
                                     ▼
                   ┌─────────────────────────────────┐
                   │   API Gateway (FastAPI)          │
                   │   Render                          │
                   │  • Route table (env-driven)      │
                   │  • Firebase JWT verify           │
                   │  • slowapi rate limit            │
                   │  • CORS                          │
                   │  • Request logging               │
                   └────┬──────┬──────┬──────┬──────┘
              ┌────────┘      │      │      │     └────────┐
              ▼               ▼      ▼      ▼              ▼
        ┌──────────┐   ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │  Admin   │   │  Search  │ │ Booking  │ │   Comments   │
        │  Service │   │  Service │ │  Service │ │   Service    │
        │ (Render) │   │ (Render) │ │ (Render) │ │   (Render)   │
        └────┬─────┘   └────┬─────┘ └────┬─────┘ └──────┬───────┘
             │              │              │             │
             │              ▼              │             ▼
             │      ┌──────────────┐       │       ┌──────────┐
             │      │   Upstash    │       │       │ MongoDB  │
             │      │    Redis     │       │       │  Atlas   │
             │      └──────────────┘       │       └──────────┘
             │                              │
             ▼                              ▼
       ┌──────────────────────────┐  ┌────────────┐
       │   Supabase Postgres       │  │ CloudAMQP   │
       │   • hotels                │  │ RabbitMQ    │
       │   • rooms                 │  │ reservations│
       │   • room_availability     │  │   queue     │
       │   • bookings              │  └─────┬──────┘
       │   • users                 │        │
       └──────────────────────────┘        │ consume
                                            ▼
                                  ┌───────────────────────┐
                                  │ Notification Service   │
                                  │ • RabbitMQ consumer    │
                                  │ • Nightly worker       │
                                  │ • Resend SMTP          │
                                  │ (Render)                │
                                  └─────────▲─────────────┘
                                            │ POST /trigger/nightly
                                            │
                                  ┌───────────────────────┐
                                  │ Google Cloud Scheduler │
                                  │ (daily 03:00 UTC)      │
                                  └───────────────────────┘

                          ╔════════════════════════════════════╗
                          ║   AI Agent Service (Render)         ║
                          ║   ┌──────────────────────────────┐  ║
                          ║   │ FastAPI /api/v1/agent/chat   │  ║
                          ║   └────────────┬─────────────────┘  ║
                          ║                │                    ║
                          ║                ▼ stdio subprocess   ║
                          ║   ┌──────────────────────────────┐  ║
                          ║   │ MCP Server (FastMCP)         │  ║
                          ║   │ Tools:                        │  ║
                          ║   │  • search_hotels             │  ║
                          ║   │  • book_hotel                │  ║
                          ║   │  • get_hotel_comments        │  ║
                          ║   └────────────┬─────────────────┘  ║
                          ║                │ httpx              ║
                          ║                ▼                    ║
                          ║   (gateway URL — same as frontend)  ║
                          ╚════════════════════════════════════╝
```

### 3.2 Kimlik doğrulama & yetkilendirme akışı

**Kimlik (kim):**
1. Kullanıcı frontend'i açar → Firebase Auth (e-posta/şifre kayıt veya giriş)
2. Firebase ID token (JWT) üretir
3. Frontend token'ı bellekte saklar, her API çağrısına `Authorization: Bearer <token>` ekler
4. Gateway isteği yakalar → `firebase-admin.auth.verify_id_token(token)`
5. Gateway UID'yi çözer, alt servise `X-User-Id` (Firebase UID) header'ı enjekte eder
6. Alt servisler gateway'e güvenir (servisler genel erişime kapalı, yalnızca gateway üzerinden)

**Yetkilendirme (ne — admin rolü):**
- Postgres'teki `users.role` admin rolü için **kaynak gerçektir** (`'user' | 'hotel_admin'`).
- İlk sign-in'de `users` satırı `role = 'user'` default'u ile upsert edilir. (Shared FastAPI dependency `Depends(get_or_create_user)` — auth'lu herhangi bir route'ta çalışır, `firebase_uid` yeniyse satırı oluşturur.)
- Admin promosyonu **out-of-band**: tek seferlik script `scripts/promote_admin.py <email>` `role = 'hotel_admin'` yapar. Demo seed (`seed_demo_data.py`) `admin@hotelapp.com` hesabını otomatik promote eder.
- Admin-only endpoint'ler (`/api/v1/admin/*` altındaki her şey) `Depends(require_admin)` kullanır:
  ```python
  async def require_admin(
      claims = Depends(verify_firebase_token),
      db = Depends(get_db),
  ):
      user = await db.fetch_one(
          "SELECT id, role FROM users WHERE firebase_uid = :uid",
          {"uid": claims["uid"]},
      )
      if not user or user["role"] != "hotel_admin":
          raise HTTPException(403, "admin only")
      return user
  ```
- Tüm adminler eşit — hotel-bazlı sahiplik yok. Herhangi `hotel_admin` herhangi bir oteli CRUD edebilir. Bu demo basitliği için bilinçli scope daraltma (multi-tenant ownership ileride genişletilebilir).

### 3.3 Rezervasyon event akışı (asenkron, durable + retry)

1. Kullanıcı frontend'de "Book"a tıklar
2. Frontend → `POST /api/v1/bookings` (JWT ile)
3. Gateway JWT doğrular → booking-service'e iletir
4. Booking-service (Postgres transaction):
   a. Transaction başlat (`SERIALIZABLE` veya `REPEATABLE READ`)
   b. Tarih aralığı için `room_availability` satırlarında `SELECT ... FOR UPDATE`
   c. Her tarihte `available_count > 0` olduğunu doğrula
   d. Her satır için `available_count` azalt
   e. `bookings` kaydı ekle
   f. Commit
5. **RabbitMQ'ya güvenilir publish** (DB commit sonrası):
   a. Topic exchange `reservations-exchange` `durable=True` ile declare (broker restart'a dayanır)
   b. Queue `q.reservations.notifications` `durable=True` ile declare
   c. Mesaj `delivery_mode=PERSISTENT` ile yayınla (broker diske yazar) ve routing key `reservation.created`
   d. Bağlantı `aio_pika.connect_robust(...)` — geçici kopmalarda otomatik reconnect
   e. **Publish-level retry policy:** exponential backoff ile 3 deneme (1s, 2s, 4s); terminal başarısızlıkta `booking_id` ile `publish_failed_terminal` log'la (manuel replay yolu)
6. Booking-service `201 Created` döner (booking kaydı kaynak gerçek; `notification_dispatched: bool` field publish sonucunu yansıtır)
7. Notification-service consumer:
   a. **Durable** kuyruğa `connect_robust` ile bağlanır
   b. `basic_consume` ile `auto_ack=False`
   c. Mesajı alır → Resend üzerinden "Rezervasyon onaylandı" emaili gönderir
   d. Email gönderimi başarısız → warning logla, in-app notification yine de yaz (failure isolation)
   e. Başarıda → `basic_ack`
   f. Yakalanmamış exception → `basic_nack(requeue=True)` (geçici hatalar broker tarafından tekrar denenir)

**Bilinen sınırlama (Dual-Write Problem, bkz. PPT_SE4458_04 slide 26-31):** Booking-service Postgres COMMIT ile başarılı publish arasında crash olursa (veya 3 retry de başarısız olursa), booking Postgres'te var ama event dispatch edilmez. Seçilen önlem (durable + persistent + retry) geçici başarısızlıkların ~%95'ini çözer ama exactly-once garanti vermez. Tam çözümler (Transactional Outbox veya SAGA Choreography) README'nin "Issues encountered" bölümünde sonraki iterasyon olarak dokümante edilir.

### 3.4 Gecelik düşük kapasite kontrolü

1. Google Cloud Scheduler her gün UTC 03:00'te tetiklenir
2. POST `https://notification-service.onrender.com/trigger/nightly` (header'da API anahtarı ile)
3. Notification-service:
   a. API anahtarını doğrular
   b. Postgres'i sorgular: her otel için sonraki 30 gün için doluluk yüzdesini hesaplar
   c. `occupied / total > 0.80` olan oteller için (≥%80 dolu = <%20 müsait)
   d. `hotels.admin_email` adresine e-posta gönderir
   e. Sonucu loglar

### 3.5 Otel detayı önbellek akışı (cache-aside, guideline uyumlu)

**Ne cache'leniyor:** Yalnızca statik otel alanları — `id`, `name`, `description`, `destination`, `address`, `latitude`, `longitude`, `star_rating`, `amenities`, `image_url`, ayrıca her odanın `room_type`, `capacity`, `base_price_per_night` değerleri. **Asla cache'lenmiyor:** `available_count` (dinamik, her booking ile değişir) ve indirim uygulanmış fiyat (istek başı, auth durumuna bağlı).

**Neden bu şekilde:** Guideline açıkça *"Hotel details will be stored in a separate distributed cache like Redis"* diyor — search sonuçları değil. Availability'yi cache'lemek iki bug doğurur: (a) booking sonrası bayatlamış müsaitlik (kullanıcı book edemeyeceği odayı görür), (b) cache anahtarı auth durumunu içermezse kullanıcılar arası indirim sızıntısı. Yalnızca statik detayı cache'lemek bu iki bug'ı da elimine eder.

**Cache anahtarları:**
- `hotel:{hotel_id}` → statik otel detayı JSON'u (24s TTL)
- `destination:{name_lower}:hotel_ids` → o destination'daki otel UUID listesi (6s TTL, opsiyonel optimizasyon)

**Search akışı (`GET /api/v1/search?...`):**
1. Frontend → gateway üzerinden search-service'e `destination`, `check_in`, `check_out`, `guests`, `page`, `limit` ile
2. **Destination için hotel ID'leri çöz** — `redis.get("destination:rome:hotel_ids")` denenir; miss ise Postgres `SELECT id FROM hotels WHERE LOWER(destination)=LOWER(?) AND deleted_at IS NULL` sorgulanır ve 6s cache'lenir
3. **Taze müsaitlik sorgusu** — Postgres `rooms JOIN room_availability`; `hotel_id IN (...)`, `[check_in, check_out)` tarih aralığı, `capacity >= guests`, ve aralıktaki her tarihte `available_count > 0` filtreleri uygulanır. **Asla cache'lenmez** — burası dinamik kısım
4. **Her sonuç için otel detayını hidrate et** — her benzersiz `hotel_id` için `redis.get("hotel:{id}")`; miss ise Postgres'ten `SELECT` ve `redis.set(..., ex=86400)`
5. **Cevabı oluştur** — statik detay (cache'den) + oda müsaitliği (taze) + `base_price_per_night` birleştir
6. **İndirimi cevap oluşturma anında uygula** — istek geçerli JWT taşıyorsa `price = base_price * 0.85` ve `discount_applied: true`. İndirimli değer **asla cache'e yazılmaz**
7. Sayfala, döndür

**Otel detay endpoint'i (`GET /api/v1/search/hotels/{id}`):**
1. `redis.get("hotel:{id}")` → hit ise cache'den döndür (auth varsa runtime'da indirim uygula)
2. Miss ise Postgres'ten oku, 24s cache'le, döndür

**Cache invalidation (write-through tetikleyici):**
- Admin `PUT /api/v1/admin/hotels/{id}` → admin-service DB commit sonrası `redis.delete("hotel:{id}")` yapar
- Admin `POST/DELETE /api/v1/admin/hotels` → admin-service ilgili `destination:{name_lower}:hotel_ids` anahtarını siler
- Oda/müsaitlik değişiklikleri (`PUT /api/v1/admin/rooms/{id}/availability`, booking commit'leri) **cache'e dokunmaz** — availability cache'lenmediği için invalidation gerekmez

**Neden bu doğru:**
- Yüksek hit rate — otel kümesi küçük, sürekli okunur
- Müsaitlik her zaman taze — booking sonrası "hayalet müsaitlik" bug'ı yok
- İndirim mantığı cache'den ayrık — kullanıcılar arası fiyat sızıntısı yok
- Admin güncellemeleri explicit `redis.delete` ile anında yayılır
- Guideline non-functional gereksinimine birebir uyar

---

## 4. Servis Kataloğu

### 4.1 Gateway (`services/gateway/`)

**Sorumluluklar:** route yönlendirme, Firebase JWT doğrulama, rate limiting (60 istek/dk/IP), CORS, istek loglama.

**Endpoint'ler:** Aşağıdaki prefix'lerle eşleşen her şeyi proxy eder.

| Prefix | Alt servis | Auth |
|---|---|---|
| `/api/v1/admin/*` | admin-service | Zorunlu |
| `/api/v1/search/*` | search-service | İsteğe bağlı (token = %15 indirim) |
| `/api/v1/bookings/*` | booking-service | Zorunlu |
| `/api/v1/comments/*` | comments-service | POST/DELETE için zorunlu, GET için isteğe bağlı |
| `/api/v1/agent/*` | ai-agent-service | İsteğe bağlı (token = agent kullanıcı olarak hareket eder) |
| `/health` | yerel | Açık |

**Teknoloji:** FastAPI + httpx + slowapi + firebase-admin.

### 4.2 Admin Service (`services/admin-service/`)

**Sorumluluklar:** Otel + Oda CRUD, oda müsaitlik yönetimi, **otel düzeyindeki write işlemlerinden sonra cache invalidation** (DB commit sonrası `hotel:{id}` ve ilgili `destination:{name_lower}:hotel_ids` anahtarlarını sil).

**Endpoint'ler:**
- `POST /api/v1/admin/hotels` — otel oluştur (lat, long, admin_email zorunlu)
- `GET /api/v1/admin/hotels` — sayfalama ile otel listele
- `GET /api/v1/admin/hotels/{id}` — otel detayını al
- `PUT /api/v1/admin/hotels/{id}` — oteli güncelle
- `DELETE /api/v1/admin/hotels/{id}` — soft delete
- `POST /api/v1/admin/hotels/{id}/rooms` — oda oluştur
- `GET /api/v1/admin/hotels/{id}/rooms` — sayfalama ile odaları listele
- `PUT /api/v1/admin/rooms/{id}/availability` — tarih aralığı için müsaitliği ayarla/güncelle
- `GET /api/v1/admin/rooms/{id}/availability?from=…&to=…` — müsaitliği al

**Depolama:** Supabase Postgres (`hotels`, `rooms`, `room_availability` tabloları).

### 4.3 Search Service (`services/search-service/`)

**Sorumluluklar:** Postgres'e karşı tarih aralığı müsaitlik sorgusu (her zaman taze), Redis'ten statik otel detayını hidrate etme (`hotel:{id}` üzerinde cache-aside), auth'lu istekler için cevap oluşturma anında %15 indirim uygulama, sayfalama. **Search-service write işlemlerinin yan etkisi olarak hotel-detail cache'ine asla yazmaz — yalnızca read miss'te doldurur; invalidation admin-service'in sorumluluğundadır.**

**Endpoint'ler:**
- `GET /api/v1/search?destination=&check_in=&check_out=&guests=&page=&limit=` — otel ara (müsaitlik taze, statik detay cache'li)
- `GET /api/v1/search/hotels/{id}` — otel detayı (cache-aside)

**Caching:** Bkz. §3.5. Cache **yalnızca statik otel detayını** tutar (`hotel:{id}`, 24s TTL) ve opsiyonel destination → hotel-id lookup'u (`destination:{name}:hotel_ids`, 6s TTL). Müsaitlik ve indirimli fiyatlar **asla** cache'lenmez.

**Depolama:** Supabase Postgres (müsaitlik + cache-miss fallback) + Upstash Redis (sıcak otel detayları).

### 4.4 Booking Service (`services/booking-service/`)

**Sorumluluklar:** Transaction'lı kapasite azaltma ile rezervasyon oluşturma, `reservation.created` event'ini **güvenilir şekilde yayınlama** (durable exchange + persistent message + exponential-backoff retry, bkz. §3.3), idempotency anahtarı yönetimi.

**Endpoint'ler:**
- `POST /api/v1/bookings` — tarih aralığı için oda rezerve et
- `GET /api/v1/bookings` — kullanıcının rezervasyonlarını listele (JWT UID kullanır)
- `GET /api/v1/bookings/{id}` — rezervasyon detayını al
- `DELETE /api/v1/bookings/{id}` — rezervasyonu iptal et (kapasite geri yükleme)

**Depolama:** Supabase Postgres + RabbitMQ yayını.

### 4.5 Comments Service (`services/comments-service/`)

**Sorumluluklar:** **5 boyutlu** puanlarla yorum CRUD (PDF mockup ile eşleşir: `cleanliness`, `staff`, `amenities`, `comfort`, `eco_friendliness`, mockup'taki gibi 1-10 ölçek), per-service distribution grafiği için toplama endpoint'i.

**Endpoint'ler:**
- `POST /api/v1/comments` — yorum ekle (auth gerekli)
- `GET /api/v1/comments/hotels/{hotel_id}?page=&limit=` — yorumları listele
- `GET /api/v1/comments/hotels/{hotel_id}/distribution` — puan dağılımı toplaması
- `DELETE /api/v1/comments/{id}` — kendi yorumunu sil

**Depolama:** MongoDB Atlas.

### 4.6 Notification Service (`services/notification-service/`)

**Sorumluluklar:** Yeni rezervasyonlar için RabbitMQ consumer + gecelik düşük kapasite uyarısı için zamanlanmış görev.

**Endpoint'ler:**
- `POST /trigger/nightly` — Google Cloud Scheduler tarafından çağrılır (API anahtarı auth)
- `GET /health`

**Worker'lar:**
- `queue_consumer` — FastAPI lifespan içinde asyncio görevi olarak çalışır, `reservations` kuyruğunu tüketir, onay e-postası gönderir
- `occupancy_checker` — `/trigger/nightly` tarafından çağrılır, düşük müsaitlikli otelleri tarar, admin uyarısı gönderir

**Depolama:** Supabase Postgres (okuma) + Resend SMTP.

### 4.7 AI Agent Service (`services/ai-agent-service/`)

**Sorumluluklar:** Sohbet endpoint'i, LLM orkestrasyonu, tool sunucu subprocess'ini yöneten MCP istemcisi.

**Endpoint'ler:**
- `POST /api/v1/agent/chat` — `{message: str, session_id: str, token?: str}` → `{response: str}`

**MCP Server tool'ları:**
- `search_hotels(destination, check_in, check_out, guests)` → JSON otel listesi
- `book_hotel(hotel_id, room_id, check_in, check_out, token)` → rezervasyon onayı
- `get_hotel_comments(hotel_id)` → yorumlar + puanlar

**Depolama:** Bellek içi oturum haritası (sekme başına).

---

## 5. Veri Modelleri

### 5.1 Postgres Şeması (Supabase)

```sql
-- Schema: public
-- Used by: admin, search, booking, notification services

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firebase_uid VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(32) NOT NULL DEFAULT 'user', -- 'user' | 'hotel_admin'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_firebase_uid ON users(firebase_uid);

CREATE TABLE hotels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    destination VARCHAR(255) NOT NULL, -- searchable city/region (e.g., "Rome", "Istanbul")
    address TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    admin_email VARCHAR(255) NOT NULL,   -- recipient of low-capacity alerts
    star_rating SMALLINT,                -- 1-5
    amenities JSONB DEFAULT '[]',        -- ["wifi", "pool", "breakfast", ...]
    image_url TEXT,                      -- optional, may be NULL in v1
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ                -- soft delete
);

CREATE INDEX idx_hotels_destination ON hotels(LOWER(destination));
CREATE INDEX idx_hotels_location ON hotels(latitude, longitude);

CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hotel_id UUID NOT NULL REFERENCES hotels(id) ON DELETE CASCADE,
    room_type VARCHAR(100) NOT NULL,     -- "Single", "Double", "Suite"
    capacity SMALLINT NOT NULL,           -- max guests per room
    base_price_per_night DECIMAL(10,2) NOT NULL,
    total_rooms SMALLINT NOT NULL,        -- how many of this type exist
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rooms_hotel_id ON rooms(hotel_id);

CREATE TABLE room_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    available_count SMALLINT NOT NULL,    -- decremented on booking
    UNIQUE(room_id, date)
);

CREATE INDEX idx_room_availability_date ON room_availability(room_id, date);

CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    room_id UUID NOT NULL REFERENCES rooms(id),
    hotel_id UUID NOT NULL REFERENCES hotels(id),
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    guests SMALLINT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'confirmed', -- 'confirmed' | 'cancelled'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_dates ON bookings(check_in, check_out);
```

### 5.2 MongoDB Şeması (Comments)

```javascript
// Collection: comments
// Database: hotel_booking_comments

{
  _id: ObjectId,
  hotel_id: String,           // UUID from Postgres hotels.id
  user_id: String,            // Firebase UID
  user_display_name: String,
  text: String,               // comment body
  ratings: {                  // 5-dimensional, each on 1-10 scale (matches PDF mockup)
    cleanliness:      Number, // Temizlik
    staff:            Number, // Personel ve servis
    amenities:        Number, // İmkân ve özellikler
    comfort:          Number, // Konaklama yerinin durumu, imkânları ve kolaylıkları
    eco_friendliness: Number  // Çevre dostluğu
  },
  overall_rating: Number,     // computed average of the 5 ratings (1-10 scale)
  created_at: ISODate,
  deleted_at: ISODate         // null if active
}

// Indexes:
db.comments.createIndex({ hotel_id: 1, created_at: -1 });
db.comments.createIndex({ user_id: 1 });
```

### 5.3 Puan Dağılımı Toplaması

```javascript
// Endpoint: GET /api/v1/comments/hotels/{hotel_id}/distribution
// MongoDB aggregation pipeline:

[
  { $match: { hotel_id: "...", deleted_at: null } },
  { $group: {
      _id: null,
      total_comments: { $sum: 1 },
      avg_cleanliness:      { $avg: "$ratings.cleanliness" },
      avg_staff:            { $avg: "$ratings.staff" },
      avg_amenities:        { $avg: "$ratings.amenities" },
      avg_comfort:          { $avg: "$ratings.comfort" },
      avg_eco_friendliness: { $avg: "$ratings.eco_friendliness" },
      avg_overall:          { $avg: "$overall_rating" },
      // Score distribution buckets (overall 1-10 ölçek, 1-10 bucket'lara bölünmüş)
      ratings_breakdown: {
        $push: { $floor: "$overall_rating" }
      }
  }}
]
```

Frontend bunu PDF mockup'ı yansıtacak şekilde **5 servis boyutu** üzerinde yatay bar chart + overall puan dağılımı histogramı olarak render eder.

### 5.4 RabbitMQ Mesaj Formatı

**Exchange:** `reservations-exchange` (topic, **durable=True**)
**Queue:** `q.reservations.notifications` (**durable=True**)
**Routing key:** `reservation.created`
**Mesaj:** `delivery_mode=PERSISTENT` (broker diske yazar; broker-restart dayanıklılığı için zorunlu)
**Consumer:** `auto_ack=False` → başarıda explicit `basic_ack` / geçici hata'da `basic_nack(requeue=True)`

```json
{
  "event_type": "reservation.created",
  "booking_id": "uuid",
  "user_email": "user@example.com",
  "user_display_name": "John Doe",
  "hotel_id": "uuid",
  "hotel_name": "Hotel Roma Plaza",
  "check_in": "2026-07-15",
  "check_out": "2026-07-18",
  "guests": 2,
  "total_price": 630.00,
  "created_at": "2026-05-17T10:30:00Z"
}
```

---

## 6. API Spesifikasyonları

### 6.1 Sözleşmeler (Conventions)
- Tüm endpoint'ler `/api/v1/` prefix'ini kullanır
- Sayfalama: `?page=1&limit=20` (varsayılan page=1, limit=20, max=100)
- Hatalar: `{ "detail": "message", "code": "ERROR_CODE" }`
- Tarihler: ISO 8601 (`2026-07-15`)
- Tarih-saat: ISO 8601 UTC (`2026-05-17T10:30:00Z`)
- Kimlik doğrulama: `Authorization: Bearer <firebase_id_token>`

### 6.2 Örnek: POST /api/v1/admin/hotels

**İstek**
```http
POST /api/v1/admin/hotels HTTP/1.1
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{
  "name": "Hotel Roma Plaza",
  "description": "Luxury hotel in city center",
  "destination": "Rome",
  "address": "Via del Corso 123, Rome, Italy",
  "latitude": 41.9028,
  "longitude": 12.4964,
  "admin_email": "admin@romaplaza.com",
  "star_rating": 4,
  "amenities": ["wifi", "pool", "breakfast"]
}
```

**Cevap 201**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Hotel Roma Plaza",
  "destination": "Rome",
  "latitude": 41.9028,
  "longitude": 12.4964,
  "admin_email": "admin@romaplaza.com",
  "created_at": "2026-05-17T10:30:00Z"
}
```

### 6.3 Örnek: GET /api/v1/search

**İstek**
```http
GET /api/v1/search?destination=Rome&check_in=2026-07-15&check_out=2026-07-18&guests=2&page=1&limit=10 HTTP/1.1
Authorization: Bearer eyJhbGc...   # optional - if present, applies 15% discount
```

**Cevap 200**
```json
{
  "page": 1,
  "limit": 10,
  "total": 23,
  "items": [
    {
      "hotel_id": "uuid",
      "name": "Hotel Roma Plaza",
      "destination": "Rome",
      "latitude": 41.9028,
      "longitude": 12.4964,
      "star_rating": 4,
      "amenities": ["wifi", "pool", "breakfast"],
      "image_url": null,
      "available_rooms": [
        {
          "room_id": "uuid",
          "room_type": "Double",
          "capacity": 2,
          "price_per_night": 178.50,
          "original_price": 210.00,
          "discount_applied": true
        }
      ]
    }
  ]
}
```

### 6.4 Tam endpoint tablosu

| Servis | Method | Path | Auth | Notlar |
|---|---|---|---|---|
| admin | POST | /api/v1/admin/hotels | ✓ | Otel oluştur |
| admin | GET | /api/v1/admin/hotels | ✓ | Sayfalamayla listele |
| admin | GET | /api/v1/admin/hotels/{id} | ✓ | Otel detayı |
| admin | PUT | /api/v1/admin/hotels/{id} | ✓ | Otel güncelle |
| admin | DELETE | /api/v1/admin/hotels/{id} | ✓ | Soft delete |
| admin | POST | /api/v1/admin/hotels/{id}/rooms | ✓ | Oda oluştur |
| admin | GET | /api/v1/admin/hotels/{id}/rooms | ✓ | Odaları listele |
| admin | PUT | /api/v1/admin/rooms/{id}/availability | ✓ | Müsaitlik aralığı ayarla |
| admin | GET | /api/v1/admin/rooms/{id}/availability | ✓ | Müsaitlik al |
| search | GET | /api/v1/search | opt | Otel ara |
| search | GET | /api/v1/search/hotels/{id} | opt | Önbellekli detay |
| booking | POST | /api/v1/bookings | ✓ | Oda rezerve et |
| booking | GET | /api/v1/bookings | ✓ | Kullanıcı rezervasyonları |
| booking | GET | /api/v1/bookings/{id} | ✓ | Rezervasyon detayı |
| booking | DELETE | /api/v1/bookings/{id} | ✓ | İptal |
| comments | POST | /api/v1/comments | ✓ | Yorum ekle |
| comments | GET | /api/v1/comments/hotels/{id} | – | Yorumları listele |
| comments | GET | /api/v1/comments/hotels/{id}/distribution | – | Puan dağılımı |
| comments | DELETE | /api/v1/comments/{id} | ✓ | Kendi yorumunu sil |
| notify | POST | /trigger/nightly | API anahtarı | Cloud Scheduler tetikleyici |
| agent | POST | /api/v1/agent/chat | opt | AI agent ile sohbet |

---

## 7. Depo (Repository) Yapısı

```
Hotel-Booking-System/
├── .github/
│   └── workflows/
│       ├── ci.yml                          # pytest + lint on PR
│       └── deploy.yml                      # optional: notify Render
├── docs/
│   ├── Guide/                              # final guideline (existing)
│   ├── Lecture_Slides/                     # slides (existing)
│   ├── PROJECT_PLAN.md                     # this document
│   └── ARCHITECTURE.md                     # ER diagram + design rationale
├── frontend/                               # Vite + React + TypeScript (Vercel)
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts                  # axios with JWT interceptor
│   │   │   ├── endpoints.ts               # typed endpoint definitions
│   │   │   ├── hotels.ts                  # TanStack Query hooks: useHotels, useHotel, useSearch
│   │   │   ├── bookings.ts                # useBookings, useCreateBooking
│   │   │   ├── comments.ts                # useComments, useDistribution
│   │   │   └── agent.ts                   # useAgentChat
│   │   ├── components/
│   │   │   ├── ui/                        # shadcn/ui primitives
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── AdminShell.tsx         # admin sidebar layout
│   │   │   ├── hotel/
│   │   │   │   ├── HotelCard.tsx
│   │   │   │   ├── HotelGallery.tsx       # photo carousel
│   │   │   │   ├── RoomCard.tsx
│   │   │   │   └── AmenitiesGrid.tsx      # lucide icon grid
│   │   │   ├── search/
│   │   │   │   ├── SearchBar.tsx          # destination + dates + guests
│   │   │   │   ├── FilterPane.tsx         # star rating, amenities, price range
│   │   │   │   └── MapView.tsx            # react-leaflet, list ile sync
│   │   │   ├── booking/
│   │   │   │   ├── BookingWidget.tsx      # sticky reserve panel
│   │   │   │   ├── BookingModal.tsx       # multi-step reserve flow
│   │   │   │   └── BookingSuccess.tsx
│   │   │   ├── comments/
│   │   │   │   ├── CommentList.tsx
│   │   │   │   ├── CommentForm.tsx        # 5-boyutlu rating input (slider 1-10)
│   │   │   │   └── RatingChart.tsx        # Recharts bar + histogram
│   │   │   ├── agent/
│   │   │   │   └── ChatWidget.tsx         # floating bottom-right chat
│   │   │   └── common/
│   │   │       ├── ProtectedRoute.tsx
│   │   │       ├── AdminRoute.tsx         # role kontrolü
│   │   │       └── Skeletons.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx               # hero search + featured destinations
│   │   │   ├── SearchResults.tsx          # list + map layout
│   │   │   ├── HotelDetail.tsx            # gallery + rooms + booking + comments
│   │   │   ├── MyBookings.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── SignUpPage.tsx
│   │   │   ├── ForbiddenPage.tsx
│   │   │   └── admin/
│   │   │       ├── HotelsPage.tsx         # data table CRUD
│   │   │       ├── HotelEditPage.tsx      # tabs: detail / rooms / availability
│   │   │       ├── AvailabilityCalendar.tsx
│   │   │       └── BookingsOverview.tsx   # occupancy chart
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useDebounce.ts
│   │   ├── lib/
│   │   │   ├── firebase.ts
│   │   │   ├── utils.ts                   # cn() helper from shadcn
│   │   │   └── format.ts                  # date/currency formatters
│   │   ├── types/
│   │   │   ├── hotel.ts                   # backend Pydantic ile aynı
│   │   │   ├── booking.ts
│   │   │   ├── comment.ts
│   │   │   └── api.ts
│   │   ├── App.tsx                        # routes + QueryClientProvider
│   │   ├── main.tsx
│   │   └── index.css                      # Tailwind directives
│   ├── public/
│   ├── components.json                    # shadcn config
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── .env.example
├── services/
│   ├── shared/                            # editable Python package
│   │   ├── shared/
│   │   │   ├── __init__.py
│   │   │   ├── config.py                 # pydantic-settings base
│   │   │   ├── logging.py                # structlog config
│   │   │   ├── pagination.py
│   │   │   ├── schemas/                  # Pydantic v2 models
│   │   │   │   ├── hotel.py
│   │   │   │   ├── room.py
│   │   │   │   ├── booking.py
│   │   │   │   ├── comment.py
│   │   │   │   └── user.py
│   │   │   ├── auth/
│   │   │   │   ├── firebase.py           # verify_id_token wrapper
│   │   │   │   └── deps.py               # FastAPI Depends() helpers
│   │   │   └── clients/
│   │   │       ├── postgres.py           # async engine + session
│   │   │       ├── mongo.py              # motor client
│   │   │       ├── redis.py              # asyncio redis
│   │   │       └── rabbitmq.py           # aio-pika connection pool
│   │   └── pyproject.toml
│   ├── gateway/                          # FastAPI proxy
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routes.py
│   │   │   └── middleware/
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── admin-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   ├── models/                   # SQLAlchemy ORM
│   │   │   └── repositories/
│   │   ├── migrations/                   # Alembic
│   │   ├── alembic.ini
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── search-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   └── services/                 # cache, pricing
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── booking-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   └── services/                 # booking, queue publisher
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── comments-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   └── services/
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   ├── notification-service/
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/                  # /trigger/nightly
│   │   │   ├── workers/                  # queue consumer, occupancy checker
│   │   │   └── services/                 # email
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   └── ai-agent-service/
│       ├── app/
│       │   ├── main.py
│       │   ├── agent.py
│       │   ├── mcp_client.py
│       │   └── session.py
│       ├── mcp_server/
│       │   ├── server.py
│       │   └── tools/
│       ├── requirements.txt
│       ├── Dockerfile
│       └── .env.example
├── infrastructure/
│   ├── docker-compose.yml                # local dev: full stack
│   ├── render.yaml                       # Render Blueprint
│   └── postman_collection.json           # API test collection
├── scripts/
│   ├── warmup.py                         # cron-job.org pings here
│   ├── seed_demo_data.py                 # demo data seeder
│   └── load_test.js                      # k6 (ported from midterm)
├── .gitignore
├── .env.example                          # root env template
├── CLAUDE.md                             # existing
└── README.md                             # main project README
```

---

## 8. Harici Servisler — Manuel Kurulum Adımları

> **ÖNEMLİ:** Bu kurulum adımlarını kendin tamamlamak zorundasın. Kod tarafında entegrasyonların kurulmasına yardım edebilirim ancak senin yerine hesap açamam. Her bölüm, tek bir `.env.template` dosyasında toplaman gereken ortam değişkenleriyle biter.

### 8.1 Supabase (Postgres)

**Ücretsiz katman:** 500 MB depolama, 2 GB egress/ay, 50 eşzamanlı bağlantı, kart gerekmez.

**Adımlar:**
1. https://supabase.com adresine git ve **Sign up**'a tıkla (en hızlı kurulum için GitHub login)
2. Giriş yaptıktan sonra **New project**'e tıkla
3. Proje adı: `hotel-booking-system`
4. Veritabanı şifresi: güçlü bir şifre üret ve **bir şifre yöneticisine kaydet** — connection string için gerekecek
5. Bölge: sana en yakını seç (örn. Türkiye için `Central EU (Frankfurt)`)
6. Fiyatlandırma planı: **Free**
7. **Create new project**'e tıkla — sağlama için yaklaşık 2 dakika bekle
8. Hazır olduğunda **Settings → Database**'e git
9. **Connection string** altında URI'yi kopyala (URI sekmesi). Şuna benzer:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxx.supabase.co:5432/postgres
   ```
10. `[YOUR-PASSWORD]` kısmını gerçek şifrenle değiştir
11. Ayrıca **Settings → API** altından **Project URL** ve **anon public key**'i not et (ileride görseller için Supabase Storage kullanırsan frontend'de lazım olabilir)

**Bunları topla:**
```bash
POSTGRES_URL=postgresql://postgres:<password>@db.xxxxxxxxxx.supabase.co:5432/postgres
POSTGRES_HOST=db.xxxxxxxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your-password>
POSTGRES_DB=postgres
```

### 8.2 Firebase Authentication

**Ücretsiz katman:** Sınırsız kimlik doğrulama, 50k MAU SMS doğrulama (SMS kullanmayacağız).

**Adımlar:**
1. https://console.firebase.google.com adresine git
2. Bir Google hesabıyla giriş yap
3. **Add project**'e tıkla
4. Proje adı: `hotel-booking-system`
5. **Google Analytics'i devre dışı bırak** (gerekli değil, kurulumu basitleştirir)
6. **Create project**'e tıkla — yaklaşık 30 saniye bekle
7. Hazır olduğunda, sol menüden **Build → Authentication**'a tıkla
8. **Get started**'a tıkla
9. **Sign-in method** sekmesi altında şunları etkinleştir:
   - **Email/Password** (kalem simgesine tıkla → AÇ konumuna getir → Save)
   - **Google** (isteğe bağlı, tek tıkla giriş için)
10. Şimdi frontend entegrasyonu için **web uygulaması** oluştur:
    - Proje genel bakış sayfasında **</> Web simgesi**ne tıkla ("Add app")
    - Uygulama takma adı: `hotel-booking-web`
    - "Firebase Hosting"i **işaretleme**
    - **Register app**'e tıkla
    - Gösterilen `firebaseConfig` nesnesini kopyala — şuna benzer:
      ```js
      const firebaseConfig = {
        apiKey: "AIzaSyXXX...",
        authDomain: "hotel-booking-system.firebaseapp.com",
        projectId: "hotel-booking-system",
        storageBucket: "hotel-booking-system.appspot.com",
        messagingSenderId: "123456789",
        appId: "1:123:web:abc"
      };
      ```
11. Şimdi **service account** oluştur (backend JWT doğrulama için):
    - **Project Settings** (dişli simgesi) → **Service accounts** sekmesine git
    - **Generate new private key**'e tıkla
    - Onayla ve JSON dosyasını indir
    - Güvenli bir konumda `firebase-service-account.json` olarak kaydet
    - **Bu dosyayı git'e COMMIT ETME** (`.gitignore`'da)

**Bunları topla:**
```bash
# Frontend (.env in frontend/)
VITE_FIREBASE_API_KEY=AIzaSyXXX...
VITE_FIREBASE_AUTH_DOMAIN=hotel-booking-system.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=hotel-booking-system
VITE_FIREBASE_APP_ID=1:123:web:abc

# Backend (.env for services)
FIREBASE_SERVICE_ACCOUNT_JSON=<paste full JSON content as single line>
# OR
FIREBASE_SERVICE_ACCOUNT_PATH=/secrets/firebase-service-account.json
FIREBASE_PROJECT_ID=hotel-booking-system
```

### 8.3 MongoDB Atlas (Comments)

**Ücretsiz katman:** M0 shared cluster, 512 MB depolama, kart gerekmez.

**Adımlar:**
1. https://www.mongodb.com/cloud/atlas/register adresine git
2. Kaydol (Google login çalışır)
3. Onboarding sorularını cevapla:
   - Hedef: "Learning MongoDB"
   - Dil: "Python"
   - **Finish**'e tıkla
4. Dağıtım seçeneği belirle:
   - **M0 FREE** seç
   - Sağlayıcı: **AWS**
   - Bölge: sana en yakın (örn. `eu-central-1` Frankfurt)
   - Cluster adı: `hotel-booking-cluster`
   - **Create deployment**'a tıkla
5. **Güvenlik kurulumu**:
   - Kimlik doğrulama yöntemi: **Username and Password**
   - Kullanıcı adı: `hotelapp`
   - Şifre: güçlü oluştur, şifre yöneticisine kaydet
   - **Create user**'a tıkla
6. **Ağ erişimi**:
   - **Add my current IP address**'e tıkla (yerel geliştirme için)
   - **AYRICA** **Add a different IP address**'e tıkla → `0.0.0.0/0` gir (Render deploy için — ücretsiz katmanda Render IP'leri dinamik olduğu için gereklidir)
   - **Add Entry**'e tıkla
7. Cluster hazır olduktan sonra (yaklaşık 3 dakika), **Connect**'e tıkla
   - **Drivers** → Python → versiyon 3.12 veya üzeri seç
   - Connection string'i kopyala:
     ```
     mongodb+srv://hotelapp:<password>@hotel-booking-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - `<password>` kısmını gerçek şifrenle değiştir
8. Veritabanını oluştur:
   - **Database → Browse Collections**'a git
   - **Add my own data**'ya tıkla
   - Veritabanı adı: `hotel_booking_comments`
   - Koleksiyon adı: `comments`
   - **Create**'e tıkla

**Bunları topla:**
```bash
MONGO_URL=mongodb+srv://hotelapp:<password>@hotel-booking-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=hotel_booking_comments
```

### 8.4 Upstash Redis (Cache)

**Ücretsiz katman:** 10.000 komut/gün, 256 MB max DB boyutu, 1 veritabanı.

**Adımlar:**
1. https://upstash.com adresine git
2. GitHub veya Google ile kaydol
3. **Create Database**'e tıkla
4. Ad: `hotel-booking-cache`
5. Tür: **Regional** (daha ucuz, ücretsiz için yeterli)
6. Bölge: sana en yakın (örn. `eu-central-1` Frankfurt)
7. Eviction: **allkeys-lru** (dolduğunda otomatik temizle)
8. TLS: **Enabled** (varsayılan, gerekli)
9. **Create**'e tıkla
10. Veritabanı sayfasında göreceklerin:
    - **Endpoint**: `xxx-yyy-zzz.upstash.io`
    - **Port**: `6379`
    - **Password**: gösterilir — bunu kopyala
    - **REST URL** ve **REST Token** (isteğe bağlı, REST yerine Redis protokolünü kullanacağız)
11. Standart Redis URL formatı:
    ```
    rediss://default:<password>@xxx-yyy-zzz.upstash.io:6379
    ```
    Not: TLS için `rediss://` (çift 's')

**Bunları topla:**
```bash
REDIS_URL=rediss://default:<password>@xxx-yyy-zzz.upstash.io:6379
```

### 8.5 CloudAMQP (RabbitMQ)

**Ücretsiz katman "Little Lemur":** 1 milyon mesaj/ay, 100 bağlantı, 1k kuyruk, 100 MB disk.

**Adımlar:**
1. https://www.cloudamqp.com adresine git
2. **Try it for free**'ye tıkla → kaydol (GitHub login çalışır)
3. **Create new instance**'a tıkla
4. Ad: `hotel-booking-mq`
5. Plan: **Little Lemur** (ücretsiz)
6. Bölge: en yakın (örn. `Amazon Web Services - eu-central-1`)
7. Tag'leri boş bırak
8. **Create instance**'a tıkla
9. Detayları görmek için yeni instance'a tıkla
10. **URL** alanını not et — şuna benzer:
    ```
    amqps://username:password@xxx.rmq.cloudamqp.com/username
    ```
11. (İsteğe bağlı) Admin UI'yi açmak için **RabbitMQ Manager** bağlantısına tıkla — bağlantıyı doğrula

**Bunları topla:**
```bash
RABBITMQ_URL=amqps://username:password@xxx.rmq.cloudamqp.com/username
```

### 8.6 Groq (LLM API)

**Ücretsiz katman:** Llama 3.3 70B Versatile için 30 req/dk, 6000 token/dk.

**Adımlar:**
1. https://console.groq.com adresine git
2. Kaydol (Google login çalışır)
3. Giriş yaptıktan sonra, sol menüden **API Keys**'e git
4. **Create API Key**'e tıkla
5. Ad: `hotel-booking-agent`
6. Anahtarı kopyala (yalnızca bir kez gösterilir)

**Bunları topla:**
```bash
GROQ_API_KEY=gsk_xxxxxxxxxxxxxx
GROQ_MODEL=llama-3.3-70b-versatile
```

### 8.7 Resend (E-posta/SMTP)

**Ücretsiz katman:** 100 e-posta/gün, 3000/ay, 1 alan adı.

**Adımlar:**
1. https://resend.com adresine git
2. Kaydol (GitHub login çalışır)
3. Giriş yaptıktan sonra dashboard'da olacaksın
4. **API Keys** → **Create API Key**'e tıkla
5. Ad: `hotel-booking-notifier`
6. İzin: **Full access** (veya yalnızca gönderim)
7. Anahtarı kopyala
8. E-posta göndermek için:
   - **Ücretsiz seçenek:** Resend'in test alan adı `onboarding@resend.dev`'i kullan (yalnızca kayıtlı e-posta adresine gönderir)
   - **Daha iyi seçenek:** Kendi alan adını ekle ve doğrula — ancak alan adı sahipliği gerektirir
   - **Bu proje için:** Bildirimler yalnızca demo amaçlı olduğundan test alan adını kullan

**Bunları topla:**
```bash
RESEND_API_KEY=re_xxxxxxxxxxxxxx
EMAIL_FROM=onboarding@resend.dev   # change if you verify your own domain
```

### 8.8 Render (Backend Hosting)

**Ücretsiz katman:** 750 saat/ay/servis, 512 MB RAM, 0.1 CPU, 15 dk hareketsizlikten sonra uyur.

**Adımlar:**
1. https://render.com adresine git
2. **GitHub** ile kaydol (repo tabanlı deploy için zorunlu)
3. Render'a repo erişimi yetkisi ver
4. **Henüz deploy etme** — kodu GitHub'a push'ladıktan sonra `render.yaml` Blueprint kullanacağız
5. Not: Servisleri sonraki bir fazda Blueprint üzerinden oluşturacaksın

**Bunları topla:** _Henüz env vars gerekmez — Render dashboard URL'i `https://dashboard.render.com` olacak_

### 8.9 Vercel (Frontend Hosting)

**Ücretsiz katman:** 100 GB bant genişliği/ay, otomatik HTTPS, GitHub entegrasyonu.

**Adımlar:**
1. https://vercel.com adresine git
2. **GitHub** ile kaydol
3. Vercel'i yetkilendir
4. GitHub'a push'ladıktan sonra projeyi import edeceğiz

**Bunları topla:** _Vercel dashboard URL'i: https://vercel.com/dashboard_

### 8.10 Google Cloud Scheduler (Gecelik Görev)

**Ücretsiz katman:** Tüm Google Cloud projelerinde toplam 3 iş/ay ücretsiz. Faturalama hesabı gerekir ama ücretsiz katmanda kalırsan ücret kesilmez.

**Adımlar:**
1. https://console.cloud.google.com adresine git
2. Google hesabıyla giriş yap
3. Yeni proje oluştur:
   - Üstteki proje seçiciye tıkla → **New Project**
   - Ad: `hotel-booking-system`
   - **Create**'e tıkla
4. **Faturalamayı etkinleştir** (Scheduler için zorunlu ama ücretsiz katmanda ücret kesilmez):
   - **Billing**'e git
   - Bir faturalama hesabı bağla (kredi kartı eklenmesi gerekir, ücretsiz katmanda ücret kesilmez)
5. **Cloud Scheduler API'yi etkinleştir**:
   - Üstte "Cloud Scheduler API" araması yap
   - **Enable**'a tıkla
6. **Henüz işi oluşturma** — notification-service deploy edilene kadar bekle (Faz 8). Deploy edilmiş Render URL'i lazım olacak.

**Bunları topla:** _Henüz env vars yok — Cloud Scheduler endpoint'ine vurur, anahtara ihtiyaç duymaz_

### 8.11 cron-job.org (Isındırma Pinger'ı)

**Ücretsiz katman:** 50 cronjob, dakika hassasiyetinde.

**Adımlar:**
1. https://cron-job.org adresine git
2. Kaydol (e-posta + şifre, kart yok)
3. E-postayı doğrula
4. **Henüz iş oluşturma** — servisler deploy edilene kadar bekle

**Bunları topla:** _UI üzerinden yapılandırılır, env vars yok_

### 8.12 GitHub Deposu

**Adımlar:**
1. https://github.com adresine git (hesabın var: `batikanakdenizz`)
2. **New repository**'ye tıkla
3. Ad: `Hotel-Booking-System` veya `se4458-hotel-booking-system`
4. Açıklama: "SE 4458 Final Project — Microservice Hotel Booking System with AI Agent"
5. **Public** (teslim için zorunlu)
6. README ile **başlatma** — yerelde zaten var
7. **Create repository**'ye tıkla
8. Repo URL'sini (HTTPS) kopyala: `https://github.com/batikanakdenizz/<repo-name>.git`

**Bunları topla:**
```bash
GITHUB_REPO_URL=https://github.com/batikanakdenizz/Hotel-Booking-System.git
```

---

## 9. Yerel Geliştirme Ortamı

### 9.1 Gerekli araçlar

| Araç | Versiyon | Amaç | Kurulum |
|---|---|---|---|
| Docker Desktop | En son | Servisleri + DB'leri yerelde çalıştır | https://www.docker.com/products/docker-desktop |
| Python | 3.12+ | Servisleri Docker'sız çalıştır (isteğe bağlı) | https://www.python.org/downloads/ |
| Node.js | 20+ LTS | Frontend dev sunucu | https://nodejs.org |
| Git | Herhangi | Versiyon kontrolü | https://git-scm.com |
| VS Code (veya PyCharm) | En son | Editör | https://code.visualstudio.com |
| k6 | En son | Yük testi (isteğe bağlı) | https://k6.io/docs/get-started/installation |
| Postman / Bruno | En son | API testi | https://www.postman.com veya https://www.usebruno.com |
| MongoDB Compass | İsteğe bağlı | Atlas için GUI | https://www.mongodb.com/products/compass |

### 9.2 VS Code önerilen eklentiler
- Python (Microsoft)
- Pylance
- Docker
- ESLint
- Prettier
- REST Client
- Thunder Client (veya Postman eklentisi)

### 9.3 Yerel ortam dosyası

Repo kökünde `.env` oluştur (gitignored). Her servisin `.env.example`'ı hangi alt kümeye ihtiyaç duyduğunu söyler. Kökteki `.env` `docker-compose.yml` için her şeyi içerebilir.

---

## 10. Uygulama Fazları (Günlük)

> **Tahmini toplam süre:** 1-2 hafta içinde ~40-60 saat.

### Faz 0 — İskelet (Gün 1, ~2-3 saat)
**Hedef:** Boş repo `docker compose up` ile tüm servisler `{"status": "ok", "service": "<name>"}` cevabı veriyor.

**Görevler:**
1. Klasör yapısı oluştur
2. Her servis için stub `main.py` yaz (FastAPI + `/health`)
3. Her servise özgü `requirements.txt`, `Dockerfile`, `.env.example`
4. `pyproject.toml`, `__init__.py`, `config.py` içeren `services/shared/` paketi
5. `infrastructure/docker-compose.yml` — yerel stack
6. Kök `README.md`, `.gitignore`, `ARCHITECTURE.md` stub
7. Vite + React frontend iskeleti
8. `git init`, ilk commit, GitHub'a push

**Doğrulama:**
- `docker compose -f infrastructure/docker-compose.yml up` başarılı
- Tüm `/health` endpoint'leri 200 döner
- Frontend dev sunucu http://localhost:5173 üzerinde boş bir sayfa gösterir

### Faz 1 — Harici servis kurulumu (Gün 1-2, ~2-3 saat, manuel)
**Hedef:** Tüm bulut hesapları oluşturuldu, tüm env vars yerel `.env`'de.

**Görevler:** Yukarıdaki Bölüm 8'i tamamla — her alt bölüm.

**Doğrulama:**
- `.env` tüm kimlik bilgileriyle dolu
- Yerel makineden Supabase Postgres'e `psql` ile bağlanabiliyorsun
- Upstash'e `redis-cli ping` çalışıyor
- Compass ile MongoDB Atlas'a bağlanabiliyorsun

### Faz 2 — Shared paket + veri katmanı (Gün 2-3, ~6 saat)
**Hedef:** SQLAlchemy modelleri, Pydantic şemaları, Alembic migration'ları, seed data.

**Görevler:**
1. `services/shared/shared/clients/` — Postgres/Mongo/Redis/RabbitMQ async istemciler
2. `services/shared/shared/schemas/` — tüm Pydantic modelleri (Hotel, Room, Booking, Comment, User)
3. `services/shared/shared/auth/firebase.py` — `verify_id_token` wrapper
4. `services/admin-service/app/models/` — SQLAlchemy ORM (Hotel, Room, RoomAvailability, Booking, User)
5. admin-service'te Alembic'i başlat: `alembic init migrations`
6. İlk migration'ı oluştur: `alembic revision --autogenerate -m "initial schema"`
7. Migration'ı Supabase'e uygula: `alembic upgrade head`
8. `scripts/seed_demo_data.py` — 10 otel seed et (Rome, Paris, Istanbul, NYC vb.) odalar, müsaitlik, örnek rezervasyonlarla; **ayrıca `admin@hotelapp.com` hesabını otomatik olarak `role='hotel_admin'` yap** (bu kullanıcının önce Firebase'e bir kere sign-up olduğu varsayımıyla)
9. `scripts/promote_admin.py <email>` — herhangi bir kullanıcıyı admin rolüne çıkaran standalone helper (README ve demo hazırlığı için kullanılır)
10. Seed script'i çalıştır

**Doğrulama:**
- Supabase'de tablolar mevcut (Table Editor üzerinden kontrol et)
- Seed script'i 10 oteli başarıyla oluşturur
- Python REPL'den Postgres sorgulanabilir

### Faz 3 — Admin servisi (Gün 3, ~3 saat)
**Hedef:** `role='hotel_admin'` ile korunan oteller + odalar + müsaitlik için tam CRUD (kimlik için Firebase JWT + yetki için Postgres role check, bkz. §3.2).

**Görevler:**
1. `routers/hotels.py` — POST/GET/PUT/DELETE
2. `routers/rooms.py` — POST/GET, müsaitlik PUT/GET
3. `repositories/` — DB erişim fonksiyonları
4. §3.2'deki shared dependency `Depends(require_admin)` ekle (Firebase JWT doğrular, `users.role` lookup yapar, `hotel_admin` değilse 403 döner)
5. Otel düzeyinde write işlemlerinde cache invalidation — Postgres COMMIT sonrası `redis.delete(f"hotel:{id}")` ve `redis.delete(f"destination:{name_lower}:hotel_ids")` (bkz. §3.5, §4.2)
6. `/docs`'ta otomatik Swagger

**Doğrulama:**
- Postman koleksiyonu: admin user otel oluşturabilir, listeleyebilir, güncelleyebilir, silebilir
- Auth: `Authorization` header'ı olmayan istekler **401** döner
- Authz: geçerli JWT ama `role='user'` taşıyan istekler **403** döner (iki seed hesabı ile test: `admin@hotelapp.com` (admin) ve `user@hotelapp.com` (normal))
- Cache invalidation: `PUT /hotels/{id}` sonrası search-service'den gelen sonraki `GET` güncellenmiş payload döner (cache key silindi)

### Faz 4 — Search servisi (Gün 4, ~4 saat)
**Hedef:** Tarih aralığı müsaitlik araması (Postgres'ten her zaman taze) + otel-detayı cache-aside (Redis `hotel:{id}`, 24s TTL) + cevap oluşturma anında uygulanan %15 indirim + sayfalama. **§3.5'e göre — müsaitlik veya indirimli fiyat asla cache'lenmez.**

**Görevler:**
1. `routers/search.py` — ana arama endpoint'i + otel-detay endpoint'i
2. `services/hotel_detail_cache.py` — özellikle `hotel:{id}` için cache-aside helper (search sonuçları DEĞİL). Read'de: `redis.get` → miss → Postgres `SELECT` → `redis.set(..., ex=86400)`. Admin tarafı invalidation: admin-service tarafından yapılır, search-service değil.
3. `services/destination_index.py` — `destination:{name_lower}:hotel_ids` için opsiyonel cache (6s TTL)
4. `services/pricing_service.py` — bir isteğin auth durumu ve base fiyat verildiğinde final fiyat + `discount_applied` flag döner (runtime hesaplama, asla cache'e yazılmaz)
5. `services/availability_query.py` — tarih aralığı + kapasite filtresi ile Postgres join (`rooms` + `room_availability`), `(hotel_id, room_id, available_count, base_price)` satırlarını döner (her zaman taze)

**Doğrulama:**
- Soğuk detay lookup: `GET /api/v1/search/hotels/{id}` ilk çağrı Postgres'i çağırır (loglar cache miss + DB query gösterir)
- Sıcak detay lookup: ikinci çağrı Redis'i çağırır (loglar cache hit gösterir) — TTL 24s
- Search sonuçları: müsaitlik satırları cache durumu ne olursa olsun her zaman Postgres'ten gelir (loglar her search çağrısında DB query gösterir)
- İndirim: token taşıyan istek `price = base_price * 0.85` ve `discount_applied: true` döner; aynı arama token'sız `base_price` ve `discount_applied: false` döner (kullanıcılar arası indirim sızıntısı olmadığını kanıtlar)
- Cache invalidation: admin otel güncelledikten sonra, search-service'in sonraki detay çağrısı güncellenmiş payload döner (admin-service'in `redis.delete` çalıştı)
- `/api/v1/search?destination=Rome` Roma otellerini paginated yapıda döner

### Faz 5 — Booking servisi (Gün 4, ~3.5 saat)
**Hedef:** Transaction'lı rezervasyon + güvenilir durable publish.

**Görevler:**
1. `routers/bookings.py`
2. `services/booking_service.py` — Postgres transaction:
   - Tarih aralığı için `room_availability` satırlarında SELECT FOR UPDATE
   - Tüm tarihlerde `available_count > 0` olduğunu doğrula
   - Her satırı azalt
   - `bookings`'e INSERT
   - COMMIT
3. `services/queue_publisher.py` — commit sonrası güvenilir publisher:
   - Auto-reconnect için `aio_pika.connect_robust(...)`
   - Exchange/queue'yu `durable=True` ile declare
   - `delivery_mode=PERSISTENT` ile publish
   - Retry decorator'a sar (örn. `tenacity`): 3 deneme, exponential backoff (1s/2s/4s)
   - Terminal başarısızlıkta: `booking_id` ile structlog.error, `False` döndür; endpoint yine 201 döner (DB kaynak gerçek) `notification_dispatched: false` field'ı ile
4. Idempotency anahtarı yönetimi (`Idempotency-Key` header → `bookings.idempotency_key` unique index'i kontrol)

**Doğrulama:**
- Rezervasyon Postgres satırları oluşturur
- Kapasite azaldı
- Mesaj CloudAMQP RabbitMQ Manager'da `delivery_mode=2` ile görünür
- Test senaryosu: notification-service consumer'ı durdur, 3 booking yap → 3 event durably kuyrukta bekler, consumer'ı başlat → 3 email dispatch edilir (mesaj kaybı yok)

### Faz 6 — Comments servisi (Gün 5, ~3 saat)
**Hedef:** PDF mockup ile eşleşen **5 boyutlu rating**'lerle MongoDB CRUD + distribution grafiğini besleyen aggregation endpoint'i.

**Görevler:**
1. `routers/comments.py`
2. 5 rating field'ı içeren Pydantic şemaları (`cleanliness`, `staff`, `amenities`, `comfort`, `eco_friendliness`), her biri 1-10 arasında constrained
3. `services/comment_service.py` — insert'te `overall_rating`'i `mean(5 boyut)` olarak hesapla
4. `/distribution` endpoint'i için aggregation pipeline (boyut başına avg + bucketed overall histogram)
5. Soft delete (`deleted_at`)

**Doğrulama:**
- 5 rating'in hepsiyle yorum POST edilebilir; bir tane eksikse 422 döner
- GET `created_at DESC` ile sayfalanmış yorumları döner
- `/distribution` 5 ortalama + bucketed overall histogram JSON döner, PDF mockup şekline uyar (Temizlik/Personel/İmkân/Konaklama durumu/Çevre dostluğu)

### Faz 7 — Notification servisi (Gün 5, ~4 saat)
**Hedef:** Kuyruk tüketicisi (her zaman çalışır) + gecelik endpoint.

**Görevler:**
1. `routers/trigger.py` — API anahtarı header kontrolü ile `POST /trigger/nightly`
2. `workers/queue_consumer.py` — `lifespan` içinde başlatılan async consumer
3. `workers/occupancy_checker.py` — sonraki 30 gün için Postgres sorgusu
4. `services/email_service.py` — Resend HTTP API istemcisi

**Doğrulama:**
- Sahte bir rezervasyon gönder → saniyeler içinde e-posta gelir
- `/trigger/nightly`'yi manuel çağır → düşük kapasiteli otel varsa admin e-postası gelir

### Faz 8 — Gateway (Gün 6, ~3 saat)
**Hedef:** Tüm trafik auth + rate limit ile gateway'den geçer.

**Görevler:**
1. `routes.py` — ENV güdümlü URL'lerle route tablosu
2. `middleware/auth.py` — korumalı prefix'ler için Firebase JWT doğrula
3. `middleware/rate_limit.py` — slowapi 60 istek/dk IP başına
4. Frontend origin için CORS

**Doğrulama:**
- Önceki tüm test istekleri `http://localhost:8080` üzerinden çalışır
- Korumalı endpoint'ler token olmadan reddedilir

### Faz 9 — AI Agent servisi (Gün 7, ~5 saat)
**Hedef:** Arama + rezervasyon intentlerini MCP tool'larıyla gerçekleştiren sohbet endpoint'i.

**Görevler:**
1. MCP sunucusunu `SE448-AiAgentFlight`'tan port et:
   - `query_flights` → `search_hotels` değişimi
   - `buy_ticket` → `book_hotel` değişimi
   - `get_hotel_comments` ekle
2. `app/agent.py` — Groq API istemcisi (httpx, OpenAI uyumlu endpoint)
3. `app/mcp_client.py` — MCP sunucu subprocess'ini spawn'lar (SE448 ile aynı pattern)
4. Oturum yönetimi (`session_id` ile anahtarlanmış bellek içi dict)
5. Tool çağrı döngüsü: LLM → tool seçimi → MCP çağrısı → sonuç → LLM → cevap

**Doğrulama:**
- "Find hotels in Rome for July 15-18 for 2 adults" ile POST `/api/v1/agent/chat` liste döner
- Devamında "Book the first one" rezervasyon oluşturur

### Faz 10 — Frontend (Gün 8-10, ~14-16 saat)
**Hedef:** Production-kalite UX: Booking.com seviyesinde arama, Airbnb-warm estetik, animasyonlu, responsive, tamamen typed.

**Faz 10.1 — İskelet & temeller (~2-3sa)**
1. `npm create vite@latest -- --template react-ts`
2. Tailwind v4 kur, `tailwind.config.ts` + `index.css` yapılandır
3. shadcn/ui'yi başlat (`npx shadcn@latest init`) — base color & tema seç
4. Kur: `framer-motion`, `@tanstack/react-query`, `react-hook-form`, `zod`, `react-day-picker`, `react-leaflet`, `recharts`, `lucide-react`, `sonner`, `firebase`, `axios`
5. `lib/firebase.ts` — Firebase'i initialize et, `auth` export et
6. `api/client.ts` — `auth.currentUser.getIdToken()` ile JWT interceptor'lı axios instance
7. `App.tsx` — `<QueryClientProvider>` + `<BrowserRouter>` + `<Toaster>` (sonner) + route tablosu
8. `hooks/useAuth.ts` — `onAuthStateChanged`'a subscribe, `user`, `role`, `loading` expose

**Faz 10.2 — Auth sayfaları (~1-2sa)**
9. `LoginPage` — split-screen: hotel hero görsel (Unsplash) + form. shadcn `<Input>` `<Button>` + react-hook-form + zod schema. Email/password + "Continue with Google". Başarısızlıkta error toast
10. `SignUpPage` — aynı layout, password strength indicator, terms checkbox
11. `ProtectedRoute` + `AdminRoute` HOC'ları — login'e veya `/forbidden`'a redirect

**Faz 10.3 — Home + Search (~3-4sa)**
12. `HomePage`:
    - Hero section: gradient background veya Unsplash hotel collage + floating glass-effect search bar
    - **SearchBar component** — destination input (autocomplete API hint'inden), date range picker (react-day-picker), guest counter (shadcn `<Popover>` ile stepper)
    - "Popular destinations" grid (6 şehir kartı Unsplash görseller ile)
    - "Featured hotels" carousel (TanStack Query → `useHotels(featured=true)`)
    - Scroll'da Framer Motion fade-in
13. `SearchResults`:
    - İki kolonlu: solda filtre+liste (60%), sağda Leaflet harita (40%, sticky)
    - Filtre pane: yıldız rating (checkbox), amenities (toggle chips), fiyat slider (shadcn `Slider`)
    - Sıralama dropdown (price asc/desc, star, distance)
    - HotelCard listesi: fotoğraf, isim, yıldız, amenity chip'leri, fiyat (auth'lu ise üstü çizili + indirimli)
    - Kart hover → harita marker pulse; marker tıkla → kart görünüme scroll
    - Yükleme'de skeleton (8 kart), sonuç yoksa empty state

**Faz 10.4 — Hotel detay + Booking (~3-4sa)**
14. `HotelDetail`:
    - Foto galerisi (HotelGallery) — ana görsel + thumbnail strip, tıkla → lightbox
    - Header: isim + yıldız + adres + harita mini-link
    - Üç kolonlu body:
      - Sol: description, AmenitiesGrid (lucide icon'lar), location
      - Orta: oda kartları (RoomCard) — type, capacity, fiyat, "Reserve"
      - Sağ: sticky BookingWidget — date picker + guests + total + "Reserve Now" CTA
    - Yorum bölümü:
      - Sol: RatingChart (Recharts) — PDF mockup'ı yansıtacak şekilde 5 servis boyutu üzerinde yatay bar chart (cleanliness/staff/amenities/comfort/eco-friendliness, 1-10 ölçek) + overall puan dağılımı histogramı
      - Sağ: CommentList + "Write a comment" form (auth'lu ise)
15. `BookingModal` — multi-step (shadcn Dialog):
    - Step 1: tarih/guest review
    - Step 2: user info review (Firebase profile'dan auto-fill)
    - Step 3: confirm + "Reserve" button
    - Başarı → checkmark animasyon (Framer Motion) + "Email gönderildi" mesajı + "View my bookings" link

**Faz 10.5 — Kullanıcı & admin alanları (~2-3sa)**
16. `MyBookings` — kullanıcının rezervasyon kart listesi (TanStack Query), status filtresi, cancel button (status='confirmed')
17. `AdminShell` — shadcn `<NavigationMenu>` ile sidebar
18. Admin `HotelsPage` — TanStack Table ile shadcn `<DataTable>` (search, sort, paginate). "Add Hotel" → `HotelModal` form
19. `HotelEditPage` — shadcn `<Tabs>`: "Detail" / "Rooms" / "Availability"
20. `AvailabilityCalendar` — ay grid'i, her hücre `available_count` gösterir, hücre tıkla → edit. Save → batch PUT
21. `BookingsOverview` — read-only occupancy chart (Recharts area chart)

**Faz 10.6 — AI ChatWidget (~1-2sa)**
22. Floating action button (sağ alt, gradient, lucide message-circle ikonu) her sayfada
23. Açıldığında → 400×600 dialog (Framer Motion slide-up)
24. Mesaj balonları (user sağ, AI sol), typing indicator (3 nokta animasyon)
25. AI arama sonucu döndüğünde: inline mini HotelCard listesi; tıkla → detaya navigate
26. Quick suggestion chip'leri: "Find hotels in Rome", "Show my bookings"
27. `agent.ts` → `/api/v1/agent/chat`'e TanStack Query mutation

**Faz 10.7 — Cila (~1-2sa)**
28. Header'da dark mode toggle (Tailwind `dark:` shadcn'den geliyor)
29. 404 sayfası (illüstrasyonlu)
30. Mobile sweep: mobile'da bottom-sheet booking, hamburger nav, haritayı gizle (toggle button)
31. Performans: admin sayfalarını `React.lazy` + `Suspense` ile lazy-load
32. Lighthouse audit ≥ 90 (Performance + Accessibility + Best Practices)

**Doğrulama:**
- Tam kullanıcı akışı yerelde uçtan uca çalışır (sign up → search → book → comment → AI chat)
- Lighthouse home + search + detail sayfasında ≥ 90
- 375px mobile genişliğinde çalışır (Chrome DevTools)
- Admin UI üzerinden hotel yönetebilir (demo için Postman gerekmez)
- Dark mode toggle çalışır
- Tüm loading state'lerde skeleton, tüm error'larda toast

### Faz 11 — Yerel entegrasyon testi (Gün 10, ~3 saat)
**Hedef:** Her şey `docker compose up` üzerinden çalışır + Postman koleksiyonu geçer.

**Görevler:**
1. Tüm endpoint'leri kapsayan Postman koleksiyonu
2. Uçtan uca manuel test:
   - Kaydol → admin otel oluşturur → kullanıcı arar → kullanıcı rezerve eder → kullanıcı yorum bırakır → kullanıcı AI ile sohbet eder
3. Bulunan hataları düzelt
4. Arama endpoint'i için k6 yük testi (vize'den port et)

### Faz 12 — Bulut dağıtımı (Gün 11, ~4 saat)
**Hedef:** Tüm servisler Render'a, frontend Vercel'a deploy edildi.

**Görevler:**
1. `infrastructure/render.yaml`'ı finalize et
2. Render dashboard'da: **New → Blueprint** → repoyu bağla → uygula
3. Her servis için yerel `.env`'den env vars'ı yapıştır
4. Build'leri bekle (7 servis için ~10-15 dk)
5. Frontend'i Vercel'a deploy et:
   - **Add New Project** → GitHub repoyu import et
   - Kök dizin: `frontend`
   - Framework preset: Vite
   - Env vars ekle (VITE_FIREBASE_*)
   - Deploy
6. Vercel'da `VITE_API_GATEWAY_URL`'i deploy edilmiş gateway'e işaret edecek şekilde güncelle
7. Vercel frontend alan adına izin vermek için gateway'de CORS'u güncelle

**Doğrulama:**
- Tüm Render servisleri "Live" gösterir
- Vercel frontend açılır, giriş yapılabilir, arama yapılabilir

### Faz 13 — Zamanlanmış görevler + warmup (Gün 11, ~2 saat)
**Hedef:** Gecelik görev zamanında çalışır, servisler uyumaz.

**Görevler:**
1. **Google Cloud Scheduler**:
   - https://console.cloud.google.com/cloudscheduler adresine git
   - **Create Job**
   - Ad: `nightly-occupancy-check`
   - Sıklık: `0 3 * * *` (her gün UTC 03:00)
   - Saat dilimi: `Europe/Istanbul`
   - Hedef tipi: **HTTP**
   - URL: `https://notification-service.onrender.com/trigger/nightly`
   - HTTP method: POST
   - Header'lar: `X-Cron-Secret: <notification-service env var'ı ile eşleşen rastgele bir secret>`
   - Auth header: boş bırak
   - **Create**'e tıkla
2. Warmup için **cron-job.org**:
   - Her Render servis URL'i için bir tane olmak üzere 7 cronjob oluştur
   - Sıklık: her 10 dakikada bir
   - URL: `https://<service>.onrender.com/health`
   - Başlık: `warmup-<service>`
   - Veya: tüm servislere yönlendiren `scripts/warmup.py` endpoint'ini pingleyen tek bir iş

**Doğrulama:**
- Cloud Scheduler işini manuel tetikle → bildirim gelir
- 30 dk bekle — herhangi bir Render servis URL'sini ziyaret et → cold start yok

### Faz 14 — Dokümantasyon + demo (Gün 12, ~4 saat)
**Hedef:** README cilalanmış, ARCHITECTURE.md'de ER diyagramı, demo videosu kaydedilmiş.

**Görevler:**
1. `README.md`'yi güncelle:
   - Deploy edilmiş URL'leri doldur (Vercel frontend, gateway, servis başına Swagger)
   - Nihai varsayımlar listesi
   - Karşılaşılan sorunlar (geliştirme sırasında bulunan gerçek problemler)
2. `ARCHITECTURE.md`:
   - ER diyagramı (dbdiagram.io kullan — ücretsiz, PNG export eder)
   - Servis etkileşim diyagramı
   - Tasarım karar günlüğü
3. Demo videosu (maks. 5 dk):
   - **Senaryo:**
     - 0:00-0:30 — Proje tanıtımı, ekranda mimari diyagramı
     - 0:30-1:00 — Kullanıcı olarak kaydol, giriş yap
     - 1:00-2:00 — "Rome" otelleri ara, haritayı göster, otele tıkla, yorum grafiğini görüntüle
     - 2:00-2:30 — Oda rezerve et, admin'de kapasite azalmasını göster
     - 2:30-3:00 — Admin olarak giriş yap, yeni otel ekle
     - 3:00-4:00 — AI agent sohbet: "Find hotels in Paris for next month, 2 people"
     - 4:00-4:30 — RabbitMQ mesajının geldiğini, e-postanın alındığını göster
     - 4:30-5:00 — Mimari özeti, GitHub linki
4. YouTube'a **Unlisted** olarak yükle
5. Video linkini README'ye ekle

**Doğrulama:**
- README yönergeye göre tüm gerekli bölümlere sahip
- Video 5 dk altında oynar
- Tüm linkler çalışır

---

## 11. Ortam Değişkenleri Referansı

> Her servisin kendi `.env` dosyası vardır. Kök `.env` `docker-compose.yml` için her şeyi toplar.

### 11.1 Paylaşılan (tüm backend servisleri için gerekli)
```bash
# Auth
FIREBASE_PROJECT_ID=hotel-booking-system
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}   # full JSON as string

# Logging
LOG_LEVEL=INFO
```

### 11.2 admin-service, search-service, booking-service, notification-service
```bash
POSTGRES_URL=postgresql+asyncpg://postgres:<password>@db.xxx.supabase.co:5432/postgres
```

### 11.3 search-service ve admin-service (ek olarak — ikisi de Redis'e ihtiyaç duyar)
```bash
# search-service: cache-aside okumaları + hotel:{id} üzerinde miss-fill
# admin-service: otel CRUD commit'leri sonrası invalidation (redis.delete)
REDIS_URL=rediss://default:<password>@xxx.upstash.io:6379
HOTEL_DETAIL_TTL_SECONDS=86400        # hotel:{id} için 24s
DESTINATION_INDEX_TTL_SECONDS=21600   # destination:{name}:hotel_ids için 6s
```

### 11.4 booking-service (ek olarak)
```bash
RABBITMQ_URL=amqps://user:password@xxx.cloudamqp.com/user
RABBITMQ_EXCHANGE=reservations-exchange
RABBITMQ_ROUTING_KEY=reservation.created
RABBITMQ_PUBLISH_MAX_RETRIES=3        # exponential-backoff retry sayısı
RABBITMQ_PUBLISH_TIMEOUT_S=10         # deneme başına timeout
```

### 11.5 comments-service
```bash
MONGO_URL=mongodb+srv://hotelapp:<password>@xxx.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=hotel_booking_comments
```

### 11.6 notification-service (ek olarak)
```bash
RABBITMQ_URL=amqps://user:password@xxx.cloudamqp.com/user
RABBITMQ_QUEUE=q.reservations.notifications
RESEND_API_KEY=re_xxx
EMAIL_FROM=onboarding@resend.dev
CRON_SECRET=<random-uuid-for-google-scheduler-auth>
```

### 11.7 gateway
```bash
ADMIN_SERVICE_URL=http://admin-service:8001
SEARCH_SERVICE_URL=http://search-service:8002
BOOKING_SERVICE_URL=http://booking-service:8003
COMMENTS_SERVICE_URL=http://comments-service:8004
NOTIFICATION_SERVICE_URL=http://notification-service:8005
AGENT_SERVICE_URL=http://ai-agent-service:8006
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://hotel-booking.vercel.app
RATE_LIMIT_PER_MINUTE=60
```

### 11.8 ai-agent-service
```bash
GATEWAY_URL=http://gateway:8080
GROQ_API_KEY=gsk_xxx
GROQ_MODEL=llama-3.3-70b-versatile
OPENAI_API_KEY=                  # optional fallback
```

### 11.9 frontend (`frontend/.env`)
```bash
VITE_FIREBASE_API_KEY=AIzaSyXXX
VITE_FIREBASE_AUTH_DOMAIN=hotel-booking-system.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=hotel-booking-system
VITE_FIREBASE_APP_ID=1:123:web:abc
VITE_API_GATEWAY_URL=http://localhost:8080  # or https://gateway.onrender.com in prod
```

---

## 12. Dağıtım (Deployment) Planı

### 12.1 Render Blueprint

`infrastructure/render.yaml` tüm 7 backend servisini deklaratif olarak tanımlar. GitHub'a push'ladıktan sonra Render dashboard'da:

1. **New → Blueprint**
2. Reponu seç
3. Render `render.yaml`'i parse eder, oluşturulacak 7 servisi gösterir
4. **Apply**'a tıkla
5. Her servis için env vars gir (Render bunları runtime'da enjekte eder)
6. Build'leri bekle

Her servis bağımsız deploy edilir. Build context monorepo köküdür; her `Dockerfile` `services/<svc>/...` yollarına başvurur.

### 12.2 Render servis ayarları (servis başına)

- **Tip:** Web Service (sadece tüketici notification-service Background Worker olabilirdi — ama `/trigger/nightly` HTTP endpoint'i çalışsın diye Web Service yapıyoruz)
- **Ortam:** Docker
- **Build komutu:** Dockerfile'dan otomatik
- **Health check path:** `/health`
- **Plan:** Free
- **Auto-deploy:** Evet (`main` branch push üzerine)

### 12.3 Vercel frontend

1. Vercel dashboard → **Add New → Project**
2. GitHub repoyu import et
3. **Projeyi yapılandır:**
   - Framework Preset: Vite
   - Kök dizin: `frontend`
   - Build komutu: `npm run build`
   - Output dizini: `dist`
4. **Ortam değişkenleri:** yerel `frontend/.env`'den tüm `VITE_*`'ları ekle
   - Kritik: `VITE_API_GATEWAY_URL=https://<your-gateway>.onrender.com`
5. **Deploy**

### 12.4 Dağıtım sonrası ayarlamalar

- **CORS:** Vercel deploy ettikten sonra Vercel URL'sini (örn. `https://hotel-booking-system-xxx.vercel.app`) kopyala ve Render'daki gateway servisinin `CORS_ALLOWED_ORIGINS` env var'ını güncelle
- **Firebase Auth alan adı whitelist'i:** Firebase console → Authentication → Settings → **Authorized domains**'de Vercel alan adını ekle

---

## 13. Zamanlanmış Görevler Kurulumu

### 13.1 Google Cloud Scheduler — Gecelik Doluluk Kontrolü

**Tek seferlik kurulum (notification-service deploy edildikten sonra):**

1. https://console.cloud.google.com/cloudscheduler
2. `hotel-booking-system` projeni seç
3. **Create Job:**
   ```
   Name:               nightly-occupancy-check
   Region:             europe-west1 (or closest)
   Description:        Daily check for hotels with <20% availability
   Frequency:          0 3 * * *
   Timezone:           Europe/Istanbul
   Target type:        HTTP
   URL:                https://notification-service-xxx.onrender.com/trigger/nightly
   HTTP method:        POST
   Auth header:        None (use custom header instead)
   Add header:         X-Cron-Secret = <CRON_SECRET env var value>
   Body:               {} (empty JSON)
   Retry config:       Max attempts 1
   ```
4. **Create**'e tıkla
5. **Test:** ⋮ menü → **Force run** → notification-service log'larını kontrol et

### 13.2 cron-job.org — Servis Isındırma

**Her Render servisi için** (7 servis), veya hepsini pingleyen tek endpoint kullanan tek bir iş:

**Seçenek A (basit, 7 iş):**
1. https://cron-job.org/en/members/jobs/
2. **Create cronjob**
3. Başlık: `warmup-gateway`
4. URL: `https://gateway-xxx.onrender.com/health`
5. Zamanlama: **Her 10 dakikada bir** (`*/10 * * * *`)
6. Kaydet
7. Her servis için tekrarla

**Seçenek B (1 iş + warmup script):**
1. Gateway'e tüm servisleri fan-out şekilde pingleyen bir `/warmup` endpoint'i ekle
2. Her 10 dakikada bir `https://gateway-xxx.onrender.com/warmup`'a vuran tek bir cron-job.org işi

50 iş limitini korumak için Seçenek B'yi seç.

---

## 14. Test Stratejisi

### 14.1 Unit testler (pytest)
- Servis başına: `tests/` klasörü
- Odak: iş mantığı (%15 indirim fiyatlandırması, müsaitlik hesabı, puan toplaması)
- Mock'lanmış DB istemcileri

### 14.2 Entegrasyon testleri
- testcontainers ile Postgres + Mongo + Redis'i ayağa kaldır (isteğe bağlı, ileri kurulum için)
- Veya: docker-compose + pytest kullan

### 14.3 Uçtan uca (Postman koleksiyonu)
- `infrastructure/postman_collection.json`
- İstek öncesi: Firebase'e giriş, token'ı kaydet
- Testler: otel oluştur → ara → rezerve et → yorum yap → sohbet et

### 14.4 Yük testi (k6) — bonus
- `SE4458-AirlineTicketing/loadtests/`'ten port et
- Senaryolar:
  - `/api/v1/search` üzerinde sabit 20 VU
  - Rezervasyon üzerinde 50 VU ramp
- Yerelde staging veya production'a karşı çalıştır
- Sonuçları README'ye belgele

---

## 15. Risk Kayıt Defteri ve Önlemler

| Risk | Olasılık | Etki | Önlem |
|---|---|---|---|
| Render ücretsiz katmanı uykuya geçince demo gecikir | Yüksek | Orta | cron-job.org her 10 dk'da warmup |
| Upstash 10k komut/gün limitine ulaşılır | Düşük | Orta | `hotel:{id}` üzerinde 24s TTL — sıcak anahtarlar yalnızca miss/invalidation'da vurulur; çok düşük cardinality (otel başına bir anahtar), Upstash konsolundan kullanımı izle |
| MongoDB Atlas M0 bağlantı fırtınası | Düşük | Orta | Servis başına tek istemci, bağlantı havuzu |
| CloudAMQP bağlantı limiti (100) | Düşük | Düşük | aio-pika `connect_robust` + tek bağlantı havuzu |
| Firebase kota sorunları | Çok düşük | Yüksek | Ücretsiz katman sınırsız, risk yok |
| Mobil dondurma öncesi Cuma demosu | uygun değil | uygun değil | Proje ile ilgisiz, risk yok |
| Postgres ile RabbitMQ arası dual-write (booking commit başarılı, publish başarısız) | Orta | Orta | Durable exchange/queue + persistent message + 3-retry exponential backoff (geçici başarısızlıkların ~%95'ini çözer). Bilinen sınırlama README'de dokümante; tam çözüm Outbox/SAGA (PPT_04 slide 26-31). |
| MCP sunucu subprocess Render'da başarısız olur | Orta | Yüksek | Deploy öncesi yerel Docker'da stdio transport'u test et; MCP bozulursa doğrudan LangChain @tool yedeği |
| Demo sırasında Groq rate limit | Orta | Orta | Mümkün olduğunda LLM cevaplarını cache'le, yedek olarak OpenAI anahtarı |
| Postgres bağlantı havuzu tükenir | Düşük | Yüksek | Servis başına SQLAlchemy `pool_size=5, max_overflow=10` |
| Render ücretsizde cold start > 30s | Orta | Orta | Warmup servisleri sıcak tutar; halihazırda sıcak oturumdan demo yap |
| Shared paket nedeniyle Render'da build başarısız olur | Orta | Yüksek | Önce yerel olarak monorepo context'i ile docker build'i test et |

---

## 16. Demo ve Video Hazırlığı

### 16.1 Demo öncesi kontrol listesi (kayıttan 1 saat önce)
- [ ] Tüm cron-job.org warmup'ları son 10 dk'da çalışmış (servisler sıcak)
- [ ] Supabase'de seed data güncel
- [ ] Rezervasyonlu test kullanıcı hesabı oluşturulmuş
- [ ] Admin hesabının otel sahipliği var
- [ ] Tarayıcı önbelleği temizlenmiş, taze pencere kullan
- [ ] Kayıt yazılımı hazır (OBS Studio, ücretsiz)
- [ ] Mikrofon ses testi

### 16.2 5 dakikalık video senaryosu (detaylı)

| Süre | Aksiyon | Notlar |
|---|---|---|
| 0:00-0:20 | Başlık kartı + mimari diyagram | "SE 4458 Final — Batikan Akdeniz" |
| 0:20-0:40 | Mimariyi gez (gateway, servisler, DB'ler, kuyruk, AI) | ARCHITECTURE.md diyagramını kullan |
| 0:40-1:00 | Frontend'i aç, yeni kullanıcı olarak kaydol | Firebase login'i göster |
| 1:00-1:30 | "Rome" ara, haritayı (Leaflet) göster, girişli olduğunda %15 indirimi göster | İndirim etiketini vurgula |
| 1:30-2:00 | Otele tıkla → yorum grafiği (Recharts) | MongoDB'den bahset |
| 2:00-2:30 | Oda rezerve et → rezervasyon onayını göster → Resend e-postası için inbox'ı kontrol et | Kuyruk + bildirimi göster |
| 2:30-3:00 | Admin panelini aç, yeni oda müsaitliği ekle | Auth'lı CRUD'u göster |
| 3:00-4:00 | AI ChatWindow aç: "Find me a hotel in Paris for July 20-23 for 2 adults" → "Book the first option" | MCP tool çağrılarını göster |
| 4:00-4:30 | CloudAMQP RabbitMQ Manager'da mesajı göster | Kuyruk altyapısını göster |
| 4:30-5:00 | Render dashboard'da 7 servisin live olduğunu, GitHub URL'yi göster | Bitir |

### 16.3 Kayıt ipuçları
- Kayıttan önce senaryoyu 2-3 kez prova et
- Yavaş ve net konuş
- Bildirimleri kapat, diğer sekmeleri kapat
- 1080p, 30 fps kaydet
- Gerekirse uzun yükleme sürelerini kes (maks. 5 dk)
- YouTube'a **unlisted** video olarak yükle → README'ye link ekle

---

## 17. Teslimat Kontrol Listesi

### 17.1 Final_Guideline.pdf'e göre

- [ ] Public GitHub deposu linki
- [ ] README içerir:
  - [ ] Deploy edilmiş URL'ler (frontend + en azından gateway)
  - [ ] Tasarım gerekçesi
  - [ ] **Varsayımlar** bölümü, şunlar dahil:
    - [ ] Hotel admin rolü `scripts/promote_admin.py` ile out-of-band ayarlanır (self-service promotion UI yok)
    - [ ] Resend ücretsiz katman test domaini `onboarding@resend.dev` yalnızca kayıtlı e-postalara gönderir (demo sınırlaması)
    - [ ] Tüm adminler tüm otelleri yönetebilir (otel-bazlı ownership yok) — bilinçli scope reduction
    - [ ] PDF mockup ile eşleşmek için 5 rating boyutu seçildi (Temizlik / Personel ve servis / İmkân ve özellikler / Konaklama yerinin durumu / Çevre dostluğu); ölçek 1-10
  - [ ] **Karşılaşılan sorunlar** bölümü, şunlar dahil:
    - [ ] **Booking'de Postgres ile RabbitMQ arası dual-write** — durable exchange/queue + persistent message + 3-deneme exponential-backoff retry + `connect_robust` auto-reconnect ile önlem alındı; tam çözüm (Outbox / SAGA, PPT_04 slide 26-31) sonraki iterasyon olarak not edildi
    - [ ] Render ücretsiz katman cold-start cron-job.org warmup ile önlendi
    - [ ] Geliştirme sırasında bulunan ve düzeltilen gerçek bug'lar
  - [ ] Veri modelleri (ER diyagramı, link veya gömülü)
  - [ ] Video linki (maks. 5 dk, unlisted YouTube)

### 17.2 Kod kalitesi

- [ ] Her servisin 200 dönen `/health` endpoint'i var
- [ ] Her servisin otomatik üretilmiş `/docs` (Swagger UI) sayfası var
- [ ] Baştan sona `/api/v1/` API versiyonlama
- [ ] Tüm liste endpoint'lerinde sayfalama
- [ ] Servis başına Dockerfile (commit edilmiş, Docker imajı değil)
- [ ] `.gitignore` secret'ları, kimlik bilgilerini, `__pycache__`, `node_modules`'ü hariç tutar
- [ ] SQLite kullanımı yok
- [ ] Yerel auth yok — yalnızca Firebase
- [ ] Gateway'de CORS yapılandırıldı

### 17.3 Mimari uyumluluk

- [ ] Tüm servislerin önünde API Gateway
- [ ] Otel detayları için dağıtık önbellek (Redis)
- [ ] Yalnızca yorumlar için NoSQL (MongoDB)
- [ ] Rezervasyonlar için RabbitMQ kuyruğu
- [ ] Harici IAM (Firebase Auth)
- [ ] Gecelik zamanlanmış görev (Google Cloud Scheduler)
- [ ] En az 3 servis ayrı deploy edildi (bizde 7 var)
- [ ] Harita görünümü ("Haritada göster") çalışıyor
- [ ] Girişli kullanıcılara %15 indirim
- [ ] AI Agent sohbet arama + rezervasyon için çalışıyor

---

## 18. Süre Tahmini

| Faz | Saat | Takvim Günü (çalışma) |
|---|---|---|
| 0. İskelet | 2-3 | 0.5 |
| 1. Harici servisler | 2-3 | 0.5 (paralel) |
| 2. Shared + veri | 4-6 | 1 |
| 3. Admin servisi | 3 | 0.5 |
| 4. Search servisi | 4 | 0.5-1 |
| 5. Booking servisi | 3.5 | 0.5 |
| 6. Comments servisi | 3 | 0.5 |
| 7. Notification servisi | 4 | 0.5-1 |
| 8. Gateway | 3 | 0.5 |
| 9. AI Agent | 5 | 1 |
| 10. Frontend | 14-16 | 2.5-3 |
| 11. Entegrasyon testi | 3 | 0.5 |
| 12. Bulut dağıtımı | 4 | 0.5-1 |
| 13. Zamanlanmış görevler | 2 | 0.25 |
| 14. Doc + demo videosu | 4 | 0.5 |
| **TOPLAM** | **60-73 saat** | **9-12 çalışma günü** |

Beklenmedik sorunlar için %20 buffer ekle → **~10-13 çalışma günü**.

Günde 4-6 saat çalışırsan bu **2-3 hafta** eder.

---

## Ek A — Yararlı Referanslar

- FastAPI dokümanları: https://fastapi.tiangolo.com
- SQLAlchemy 2.0 async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Pydantic v2: https://docs.pydantic.dev/latest/
- aio-pika eğitimi: https://aio-pika.readthedocs.io/en/latest/quick-start.html
- motor (async MongoDB): https://motor.readthedocs.io
- firebase-admin Python: https://firebase.google.com/docs/admin/setup
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- FastMCP: https://github.com/jlowin/fastmcp
- Render Blueprints: https://render.com/docs/blueprint-spec
- Vercel Vite deploy: https://vercel.com/docs/frameworks/vite
- Google Cloud Scheduler: https://cloud.google.com/scheduler/docs
- Leaflet React: https://react-leaflet.js.org
- Recharts: https://recharts.org
- dbdiagram.io (ER): https://dbdiagram.io
- Groq API (OpenAI uyumlu): https://console.groq.com/docs/quickstart

## Ek B — Sık Kullanılan Komutlar

```bash
# Local development
docker compose -f infrastructure/docker-compose.yml up
docker compose -f infrastructure/docker-compose.yml up admin-service
docker compose logs -f gateway

# Database
cd services/admin-service
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1

# Run a single service without Docker
cd services/admin-service
pip install -e ../shared
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend
npm install
npm run dev    # http://localhost:5173
npm run build

# Tests
cd services/admin-service
pytest

# Seed data
python scripts/seed_demo_data.py

# Deploy
git push origin main   # Render + Vercel auto-deploy on push
```

---

**Proje Planı v1.0 Sonu**

Bu plan canlı bir belgedir. Uygulama sırasında kararlar değiştikçe güncelle. Her faz, sonraki aşamaya geçmeden önce gözden geçirilebilecek çalışan bir artefakt üretmelidir.
