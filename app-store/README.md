# Top Potada: App Store'a yükleme

Derleme, imza ve yükleme Codemagic'te otomatik. Mağaza sayfası da (metinler, ekran görüntüleri, yaş derecesi, inceleme notu) Codemagic'ten doldurulur. Elle yapılacak az sayıda adım kaldı.

## Sıra

1. **App Store Connect'te uygulama kaydı** (yalnızca bir kez, kayıt yoksa)
   App Store Connect → Uygulamalar → **+** → Yeni Uygulama
   - Platform: iOS · Ad: `Top Potada: Basket Ligi` · Birincil dil: **Türkçe**
   - Paket kimliği: `com.toppotada.oyun` (listede yoksa önce `iOS TestFlight` işlemini bir kez çalıştır; kimliği o oluşturur)
   - SKU: `toppotada` · Kullanıcı erişimi: Tam erişim

2. **Firebase → Authentication → Sign-in method → Apple**: Etkinleştir (başka alan doldurmak gerekmez). Bu açık değilse iPhone'da "Apple ile giriş" hata verir.

3. **Codemagic → iOS TestFlight**: `main` dalına her gönderimde kendiliğinden çalışır, derlemeyi App Store Connect'e yükler.

4. **Codemagic → "App Store: sayfayı hazırla"** (Start new build ile): metinleri, 5 ekran görüntüsünü, kategoriyi, yaş derecesini, inceleme notunu yazar ve son derlemeyi sürüme bağlar. Sonunda **EKSİKLER** listesi yazar.
   - İnceleme için telefon numarası gerekiyor: Codemagic → uygulama → Environment variables → `asc` grubuna `ASC_TEL` = `+905xxxxxxxxx` ekle (ya da App Store Connect'te elle yaz).

5. **App Store Connect → Uygulama Gizliliği** (API ile yapılamıyor, bir kez): aşağıdaki yanıtları gir ve **Yayımla**.

6. **Fiyatlandırma ve Kullanılabilirlik**: Ücretsiz, tüm ülkeler (ilk seferde ister).

7. **Codemagic → "App Store: incelemeye gönder"**: aynı işler + Apple incelemesine gönderim. Sonuç genelde 1–3 gün içinde e-postayla gelir.

## Uygulama Gizliliği yanıtları

Reklam kimlikleri girildiyse (aşağıya bak) **Reklamlı** sütununu, girilmediyse **Reklamsız** sütununu kullan.

| Veri türü | Reklamsız | Reklamlı (AdMob) | Kimliğe bağlı mı | İzleme için mi |
|---|---|---|---|---|
| İletişim bilgileri → Ad | ✔ Uygulama işlevselliği | ✔ aynı | Evet | Hayır |
| İletişim bilgileri → E-posta | ✔ Uygulama işlevselliği | ✔ aynı | Evet | Hayır |
| Tanımlayıcılar → Kullanıcı kimliği | ✔ Uygulama işlevselliği | ✔ aynı | Evet | Hayır |
| Kullanıcı içeriği → Oyun içeriği | ✔ Uygulama işlevselliği | ✔ aynı | Evet | Hayır |
| Tanımlayıcılar → Aygıt kimliği | — | ✔ Üçüncü taraf reklamcılık, Analiz | Hayır | **Evet** |
| Kullanım verileri → Ürün etkileşimi | — | ✔ Üçüncü taraf reklamcılık, Analiz | Hayır | **Evet** |
| Kullanım verileri → Reklam verileri | — | ✔ Üçüncü taraf reklamcılık | Hayır | **Evet** |
| Konum → Yaklaşık konum | — | ✔ Üçüncü taraf reklamcılık | Hayır | **Evet** |
| Tanılama → Çökme ve Performans verileri | — | ✔ Analiz | Hayır | Hayır |

Diğer her şey (sağlık, finans, kişiler, fotoğraf, tarama geçmişi, hassas bilgi): **Toplanmıyor**.

## Reklamlar (iPhone)

`ios/Config.xcconfig` dosyasında şu an Google'ın **test** reklam kimlikleri var. Mağazaya "Test Ad" yazılı reklam çıkmasın diye uygulama bu durumda **reklamsız** çalışır (izleme izni de sorulmaz).
Reklam açmak için AdMob → Uygulama ekle → **iOS** → Top Potada; oluşan uygulama kimliğini ve iki reklam biriminin (Geçiş, Ödüllü) kimliklerini `TP_ADMOB_APP_ID`, `TP_AD_INTERSTITIAL`, `TP_AD_REWARDED` satırlarına yaz. Android kimlikleri iPhone'da çalışmaz.

## Google ile giriş (iPhone, isteğe bağlı)

`TP_GOOGLE_CLIENT_ID` boşken iPhone'da yalnızca **Apple ile giriş** görünür; bu App Store için yeterli. Google düğmesini de istersen: Firebase → Proje ayarları → iOS uygulaması ekle (`com.toppotada.oyun`) → GoogleService-Info.plist içindeki `CLIENT_ID` ve `REVERSED_CLIENT_ID` değerlerini xcconfig'e yaz.

## Dosyalar

- `metadata.json`: ad, alt başlık, açıklama, anahtar kelimeler, adresler, inceleme notu
- `ekran-goruntuleri/1-5.png`: 1320×2868 (iPhone 6.9")
- Destek: https://sviappdeveloper-sketch.github.io/top-potada/destek.html
- Gizlilik: https://sviappdeveloper-sketch.github.io/top-potada/gizlilik.html
