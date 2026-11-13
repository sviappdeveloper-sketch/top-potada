# Top Potada: Google Play'e yükleme

Paket kimliği: `com.toppotada.oyun` · Hedef SDK 36 · Ücretsiz, reklamlı (AdMob), uygulama içi satın alma yok.

## Bu klasörde hazır olanlar

- `listing.json`: uygulama adı, kısa açıklama (80 karakter), tam açıklama, kategori, iletişim ve gizlilik adresi
- `simge-512.png`: uygulama simgesi (512×512)
- `one-cikan-gorsel-1024x500.png`: öne çıkan görsel
- `ekran-goruntuleri/1-5.png`: telefon ekran görüntüleri (1080×2160)

## İmzalı paket (AAB)

Play, yükleme anahtarıyla imzalı AAB ister. Anahtar (`top-potada-upload.jks`) **depoya konmaz** (depo herkese açık).
Anahtar dosyası ve şifresi sana ayrıca verildi; bir yerde güvenle sakla. Kaybolursa Play desteğinden yeni yükleme anahtarı istenebilir ama zahmetlidir.

Her güncellemede imzalı paket otomatik çıksın diye (bir kez):
GitHub → depo → Settings → Secrets and variables → Actions → **New repository secret**
- `PLAY_KEYSTORE_B64` = anahtar dosyasının base64 hâli (`top-potada-upload.jks.base64.txt` dosyasının içeriği)
- `PLAY_KEYSTORE_PASS` = anahtar şifresi

Bundan sonra `main`'e her gönderimde `apk` dalında **TopPotada-play.aab** (imzalı) de oluşur.

## Play Console adımları (sırayla)

1. **Geliştirici hesabı**: play.google.com/console → hesap aç (bir kerelik 25 $, kimlik doğrulaması).
2. **Uygulama oluştur**: Ad `Top Potada: Basket Ligi` · Dil Türkçe · Oyun · Ücretsiz · beyanları işaretle.
3. **Play App Signing**: ilk yüklemede "Google tarafından oluşturulan anahtar" seçeneğini kabul et (varsayılan).
4. **Kurulum > Uygulama içeriği** (soldaki menü):
   - Gizlilik politikası: `https://sviappdeveloper-sketch.github.io/top-potada/gizlilik.html`
   - Reklamlar: **Evet, reklam içeriyor**
   - Uygulama erişimi: **Tüm işlevler özel erişim gerekmeden kullanılabilir** (misafir olarak oynanır; lig/turnuva için Google ile ücretsiz giriş)
   - İçerik derecelendirmesi: anketi doldur: kategori **Oyun**; şiddet, cinsellik, küfür, kumar, uyuşturucu: **Hayır**; kullanıcılar etkileşime geçebilir mi: **Evet** (online oda, takma adlar); konum paylaşımı: Hayır; dijital satın alma: Hayır → sonuç genelde **3+ / PEGI 3**
   - Hedef kitle: **13 yaş ve üzeri** (13-15, 16-17, 18+). Çocuklara yönelik değil.
   - Reklam kimliği: **Evet**, amaç **Reklam veya pazarlama** ve **Analiz**
   - Veri güvenliği: aşağıdaki tablo
   - Hükümet uygulaması: Hayır · Finans: Hayır · Sağlık: Hayır
5. **Mağazada görünme > Ana mağaza girişi**: `listing.json` metinleri + bu klasördeki görseller.
6. **Test > Kapalı test**: yeni bir kanal oluştur, `TopPotada-play.aab`'yi yükle, testçi e-posta listesi ekle.
   - Yeni kişisel hesaplarda **üretime çıkmak için en az 12 testçinin 14 gün boyunca kapalı teste katılmış olması** zorunlu.
7. **Firebase (Google ile giriş için önemli)**: Play, uygulamayı kendi anahtarıyla yeniden imzalar. Play Console → Test ve yayınla → Kurulum → **Uygulama imzalama** sayfasındaki
   *Uygulama imzalama anahtarı sertifikası* **SHA-1** ve **SHA-256** değerlerini kopyala →
   Firebase Console → Proje ayarları → Android uygulaması (`com.toppotada.oyun`) → **Parmak izi ekle**. Bunu yapmazsan Play'den indirilen uygulamada Google ile giriş çalışmaz.
   Yükleme anahtarının parmak izleri de eklenebilir (dosyayla birlikte verildi).
8. **AdMob**: AdMob → Uygulamalar → Top Potada (Android) → Uygulama ayarları → **Play Store'a bağla** (uygulama yayınlanınca). Ayrıca `app-ads.txt` istenirse web sitesine eklenir.
9. 14 gün dolunca **Üretim** kanalına aynı paketi (ya da yenisini) gönder → Google incelemesi (genelde birkaç gün).

## Veri güvenliği yanıtları

Veriler aktarım sırasında şifrelenir: **Evet**. Kullanıcı verilerini silme isteği: **Evet** (uygulama içinde: adına dokun → Hesabım → Hesabımı sil; ya da destek e-postası).

| Veri türü | Toplanıyor | Paylaşılıyor | Amaç | Zorunlu mu |
|---|---|---|---|---|
| Kişisel bilgiler → Ad (takma ad) | Evet | Hayır | Uygulama işlevselliği, Hesap yönetimi | İsteğe bağlı |
| Kişisel bilgiler → E-posta adresi | Evet | Hayır | Hesap yönetimi | İsteğe bağlı (yalnız giriş yapanlar) |
| Kişisel bilgiler → Kullanıcı kimlikleri | Evet | Hayır | Uygulama işlevselliği, Hesap yönetimi | Zorunlu |
| Uygulama etkinliği → Uygulama etkileşimleri | Evet | Evet (AdMob) | Analiz, Reklam | Zorunlu |
| Uygulama etkinliği → Oyun içi içerik (skorlar, takma ad) | Evet | Hayır | Uygulama işlevselliği | Zorunlu |
| Cihaz veya diğer kimlikler (reklam kimliği) | Evet | Evet (AdMob) | Reklam, Analiz | Zorunlu |
| Konum → Yaklaşık konum | Evet | Evet (AdMob) | Reklam | Zorunlu |
| Uygulama bilgileri ve performans → Kilitlenme günlükleri, Teşhis | Evet | Evet (AdMob) | Analiz | Zorunlu |

Diğer her şey (finans, sağlık, mesajlar, fotoğraf, kişiler, takvim, dosyalar, tarama geçmişi): **Toplanmıyor**.
