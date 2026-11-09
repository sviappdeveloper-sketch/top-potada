# Top Potada: Uygulama ve Play Store rehberi

Bu klasörde Top Potada'nın bağımsız uygulama sürümü var. Firebase sunucusuyla çalışıyor ve **Google ile giriş**, **seviye ligleri**, **turnuvalar**, **online oda** ve **basketpuan** özelliklerini içeriyor. Play Store'a, web uygulamasını Android paketine saran **Trusted Web Activity (TWA)** yöntemiyle çıkacak.

```
top-potada-app/
├─ public/                   ← yayımlanacak web uygulaması
│  ├─ index.html             ← oyunun tamamı
│  ├─ backend.js             ← Firebase bağlantısı (ve sunucusuz DEMO modu)
│  ├─ firebase-config.js     ← SENİN DOLDURACAĞIN ayarlar
│  ├─ manifest.webmanifest, sw.js, icons/   ← yüklenebilir uygulama (PWA)
│  ├─ gizlilik.html          ← gizlilik politikası (Play zorunlu)
│  ├─ hesap-silme.html       ← hesap silme sayfası (Play zorunlu)
│  └─ .well-known/assetlinks.json  ← Android uygulaması ile site bağlantısı
├─ firestore.rules           ← veritabanı güvenlik kuralları
├─ firebase.json, .firebaserc
├─ play-store/               ← mağaza metinleri, ikon (512), tanıtım görseli (1024×500)
└─ claude-surumu/            ← oyunun Claude üzerinde çalışan sürümü (tek dosya)
```

---

## 0. Önce dene (5 dakika, kurulum gerektirmez)

`firebase-config.js` doldurulmadığı sürece oyun **DEMO modunda** çalışır. Bu modda veriler yalnızca o tarayıcıda tutulur ve Google girişi taklit edilir. Bilgisayarda:

```
cd top-potada-app/public
python3 -m http.server 8080
```

Tarayıcıda `http://localhost:8080` adresini aç. Aynı tarayıcıda birkaç sekme açarsan her sekme ayrı bir oyuncu olur. Böylece lig, turnuva ve online odayı tek başına deneyebilirsin.

---

## 1. Firebase projesi (ücretsiz plan yeterli)

1. https://console.firebase.google.com adresinde **Proje oluştur**. Proje kimliğine örneğin `top-potada` de.
2. **Authentication → Başlayın → Sign-in method** bölümünde iki yöntemi etkinleştir:
   - **Google**: Etkinleştir ve destek e-postasını seç.
   - **Anonim (Anonymous)**: Etkinleştir. Misafir oyuncular bunu kullanır.
3. **Firestore Database → Veritabanı oluştur**. Üretim (production) modunu seç, bölge olarak Avrupa'yı seç (ör. `eur3` ya da `europe-west3`).
4. **Proje ayarları → Genel → Uygulamalarınız → Web (`</>`)** ile bir web uygulaması ekle. Verilen `firebaseConfig` değerlerini `public/firebase-config.js` dosyasına yapıştır.
   - `authDomain` alanına **`PROJE-ID.web.app`** yaz (`firebaseapp.com` yerine). Bu, Google girişinin uygulama içinde sorunsuz çalışması için önemli.
5. `.firebaserc` dosyasındaki `PROJE-ID` yerine kendi proje kimliğini yaz.

## 2. Yayınla (Firebase Hosting)

Bilgisayarında Node.js 20 veya üzeri kurulu olmalı.

```
npm install -g firebase-tools
firebase login
cd top-potada-app
firebase deploy --only hosting,firestore:rules
```

Yayın bitince oyun `https://PROJE-ID.web.app` adresinde açılır. Telefondan açıp Google ile girişi, ligi ve turnuvayı dene. Chrome menüsündeki **Ana ekrana ekle** ile uygulama gibi de yüklenebilir.

> Kendi alan adını (ör. toppotada.com) bağlarsan: Hosting → Özel alan adı ekle. Ardından Authentication → Settings → **Authorized domains** listesine o adı ekle ve `authDomain` alanını da o adla değiştir.

## 3. Android paketi (.aab)

Play Store'a yüklenecek dosya bir **Android App Bundle (.aab)**. İki yol var:

**A) PWABuilder (en kolayı, tarayıcıdan)**
1. https://www.pwabuilder.com adresine `https://PROJE-ID.web.app` yaz ve **Package for stores → Android** seç.
2. Paket kimliği olarak `com.toppotada.oyun` gir (değiştirirsen `assetlinks.json` dosyasında da değiştir). Uygulama adı: `Top Potada`.
3. İmzalama anahtarı için yeni anahtar oluşturulmasını seç. İndirilen zip'te `.aab` dosyası ve **imzalama anahtarı** var. Anahtarı ve şifrelerini güvenli bir yerde sakla; kaybolursa güncelleme yayımlayamazsın.

**B) Bubblewrap (komut satırı)**
```
npm install -g @bubblewrap/cli
bubblewrap init --manifest https://PROJE-ID.web.app/manifest.webmanifest
bubblewrap build
```

> **Hedef API:** 31 Ağustos 2026'dan beri yeni uygulamalar **Android 16'yı (API 36)** hedeflemek zorunda. Paketlemeden önce aracın güncel sürümünü kullan ve oluşan projede `targetSdkVersion` değerinin 36 olduğundan emin ol.

**Site bağlantısı (adres çubuğunun görünmemesi için şart):**
1. Play Console → uygulaman → **Test ve yayın → Uygulama bütünlüğü → Uygulama imzalama** bölümünden **Uygulama imzalama anahtarı SHA-256** parmak izini kopyala.
2. `public/.well-known/assetlinks.json` içindeki `PLAY-CONSOLE-...` yerine yapıştır. Kendi yükleme anahtarının parmak izini de listeye ekleyebilirsin.
3. `firebase deploy --only hosting` ile tekrar yayımla. Kontrol: `https://PROJE-ID.web.app/.well-known/assetlinks.json` açılmalı.

## 4. Google Play Console

1. **Geliştirici hesabı:** https://play.google.com/console adresinde tek seferlik 25 USD ödenir ve kimlik doğrulaması yapılır.
2. **Uygulama oluştur:** Ad *Top Potada*, varsayılan dil Türkçe, tür **Oyun**, **Ücretsiz**.
3. **Mağaza girişi:** `play-store/magaza-metinleri.md` dosyasındaki metinleri, 512 px ikonu, 1024×500 tanıtım görselini ve **en az 2 telefon ekran görüntüsünü** yükle. Ekran görüntülerini kendi telefonundan al.
4. **Uygulama içeriği** bölümünü doldur:
   - Gizlilik politikası: `https://PROJE-ID.web.app/gizlilik.html` (önce dosyadaki `[...]` alanlarını doldur)
   - Hesap silme: `https://PROJE-ID.web.app/hesap-silme.html`
   - Veri güvenliği: Yanıtlar `magaza-metinleri.md` dosyasında.
   - İçerik derecelendirme anketi, hedef kitle (13 yaş ve üzeri önerilir), reklam: yok.
5. **Kapalı test (yeni kişisel hesaplar için zorunlu):** En az **12 test kullanıcısı** kapalı teste katılmalı ve **14 gün boyunca kesintisiz** katılımda kalmalı. Sonra **Üretime erişim başvurusu** yapılır. Yolda düşenler olabileceği için 15–20 kişi davet etmek güvenli. Kuruluş (şirket) hesabıyla açılırsa bu şart yok, ama D-U-N-S numarası gerekiyor.

## 5. Doldurman gereken yerler

| Dosya | Ne yazılacak |
|---|---|
| `public/firebase-config.js` | Firebase web uygulaması ayarları, `authDomain: PROJE-ID.web.app` |
| `.firebaserc` | Proje kimliği |
| `public/gizlilik.html` | `[TARİH]`, `[AD SOYAD / ŞİRKET]`, `[E-POSTA ADRESİ]`, `[YAŞ SINIRI]` |
| `public/hesap-silme.html` | `[E-POSTA ADRESİ]` |
| `public/.well-known/assetlinks.json` | Paket kimliği ve SHA-256 parmak izi |
| `public/sw.js` | Her yeni yayında `SURUM` değerini artır (ör. `tp-v2`) |

## 6. Nasıl çalışıyor?

- **Misafir:** Uygulama açılınca anonim oturum açılır. Misafir tek oyunculu oyunu, aynı telefonda oyunu ve online odayı oynayabilir.
- **Üye:** Google ile giriş yapan herkes ücretsiz üye olur. Misafir hesap Google hesabına *bağlanır*, bu yüzden ilerleme kaybolmaz. Turnuva, lig ve basketpuan yalnızca üyeler içindir; puan durumunda yalnızca üyeler görünür. `firestore.rules` dosyası da turnuva ve lig yazmalarını yalnızca Google oturumlarına açar.
- **Lig:**
  - Bronz, Gümüş, Altın ve Elmas ligleri var; her takvim ayı bir sezon (Türkiye saatiyle).
  - Günde en fazla 3 maç oynanır. Galibiyet 3, beraberlik 1 puan.
  - Sezon sonunda en az 5 maç oynayanlar arasında ilk %20 bir üst lige çıkar, son %20 bir alt lige düşer.
  - Her ligin ilk 3'ü basketpuan alır: Bronz 5/3/1, Gümüş 10/6/3, Altın 15/9/5, Elmas 20/12/6.
  - Sezon geçişi ayrı bir sunucu görevi gerektirmez; her cihaz geçen sezonun kayıtlarından hesaplar.
- **Veri yapısı (Firestore):**
  - `pl/<uid>`: oyuncu (takma ad, üyelik, turnuva sonuçları, oda ödülleri)
  - `tours/<id>`: turnuvalar
  - `ligkayit/<sezon>_<uid>`: lig kayıtları
  - `rooms/<oda>/peers/<uid>`: online odalar

## 7. Bilinen sınırlar ve sonraki adımlar

- **Hile koruması:** Skorlar oyuncunun cihazında hesaplanıp kaydediliyor. Kurallar herkesin yalnızca kendi kaydını yazmasına izin veriyor, ama bilgili biri kendi skorunu elle değiştirebilir. Basketpuan ileride değer kazanacaksa (ödül, ücretli üyelik), **Firebase App Check** ve skorları sunucuda doğrulayan **Cloud Functions** eklenmeli. Cloud Functions, kullandıkça ödenen Blaze planı gerektirir.
- **Ücretli üyelik** istenirse Google Play Faturalandırma (Billing) eklenir. Mevcut yapıda yalnızca "üye mi?" kontrolüne bir koşul daha eklemek yeterli olacak şekilde hazırlandı.
- Online odada eski katılımcı kayıtları (`rooms/...`) Firestore'da birikir. Arada bir silinebilir ya da Firestore'un **TTL politikası** ile otomatik silinebilir.
- Kalabalık bir oyuncu kitlesinde turnuva ve lig kayıtlarının tamamı her cihaza indirilir. Yüzlerce oyuncuya kadar sorun yok; binlerce oyuncu için sorgular sayfalanmalı.
