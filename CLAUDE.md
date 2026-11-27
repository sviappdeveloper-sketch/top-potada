# Top Potada — Claude devir notu

Bu dosya, uygulamada hangi Claude hesabı veya oturumu çalışırsa çalışsın kaldığı yerden devam edebilmesi için tutulur.
GitHub: `sviappdeveloper-sketch/top-potada`

## Çalışma kuralları (her oturumda uy)
- Kullanıcı kodlama bilmiyor ve Türkçe yazıyor. Türkçe ve sade cevap ver.
- Kullanıcı açıkça istemedikçe son kayıtlı sürümdeki hiçbir özelliği silme veya kaybetme. Değiştirmeden önce mevcut olanı diğer dallar dahil kontrol et. Kullanıcı daha önce lig işaretleri gibi ayrıntıların sonraki sürümde kaybolmasından şikâyet etti.
- Uygulamaları birbirine karıştırma. Bir uygulamanın Firebase, giriş veya mağaza ayarı değişirken diğerlerinin ayarına dokunma.
- Geliştirici adını her yerde tam olarak **Svi App Developer** diye yaz. Site sviapp.com, iletişim adresi iletisim@sviapp.com.
- Derlemeyi teslim ederken yalnızca APK dosyasının kendisini gönder. Zip, rar veya yanında başka dosya olmasın.
- Tüm testlerde (TestFlight ve Play) sitaresivi@icloud.com test kullanıcısı olarak ekli olsun.
- Mağaza ve konsol adımlarını (AdMob, Play Console, App Store Connect, Firebase) mümkün olduğunca kendin yap.
- Derlemeler ücretsiz yoldan, GitHub Actions ile yapılıyor. Codemagic dakikaları bitti.
- **Bu dosyayı güncel tut:** Her oturumun sonunda yaptığın işi tarihiyle "Son işlemler" bölümünün en üstüne ekle, "Bekleyen işler" bölümünü güncelle, sonra commit'leyip push'la.

## Uygulama durumu
- Basketbol oyunu, Android'de WebView olarak çalışıyor. Sürümler: Android **1.0.26**, iOS **1.0.4**.
- App Store'da yayında; Çin anakarasında satıştan kaldırıldı. Google Play'de kapalı testte; kullanıcı imzalı AAB'yi Play'e telefonundan yüklüyor.
- Güncellemeler hem App Store'a hem Google Play'e gidiyor.
- AdMob reklamları ve Google ile giriş var. Yönetici hesabıyla giriş yapılınca reklam çıkmıyor. TestFlight'ta dış test grubu var.
- GitHub Actions iş akışları: `apk.yml`, `ios.yml`, `testflight.yml`, `asc-gonder.yml`, `pages.yml`.
- Dallar: main, apk, asc-gonder, dis-test, geri-tusu-reklam-yonetici, hesap-ayri-kayit, ios-surumu, oda-sirali-oyun, test-cift-pota, testflight.

## Kullanıcının önemli istekleri (kalıcı)
- Macera modu 100 level olmalı ve zorluk giderek artmalı.
- Basketpuan (BP) ve can kuralları: galibiyet 10 BP, beraberlik 3 BP, her 30 BP 1 can eder. Can **en fazla 10** olur ve hiçbir yolla 10'u geçmez. Turnuva veya ligde 1. olmak +2 can, ödüllü reklam izlemek +2 can verir.
- BP ve can sağ kenarda görünür, ☰ menüsü canın yanında durur (iPhone çentiğinin altında kalmamalı).
- Lig kademeleri Bronz, Gümüş, Altın ve Elmas. Altın ligdeki oyuncunun takma adının yanında 🥇, Elmas ligdekinin yanında 💎 görünür.
- Her hesabın canı, BP'si ve ilerlemesi ayrı tutulur.
- "Rakip bul" yalnızca gerçek oyuncuyla eşleşir. Kodla açılan online odada oyun sıralı oynanır ve herkes aynı sonucu görür.
- Üst üste sayılarda yazılar çıkar: 3'te "Güzel", 4'te "Harika", 5'te "Efsane".
- Android geri tuşu ve yana kaydırma bir önceki menüye döner. Oyun içi menüde ses ve titreşim ayarları ile oyunu bitirme (puan kalmaz uyarısıyla) vardır.

## Son işlemler (en yeni en üstte)
- 2026-11-24: Can en fazla 10 oldu ve hiçbir yolla 10'u geçmiyor (Android 1.0.26).
- 2026-11-24: Can 10'a çıkarıldı. Bronz bilgisayar ligindeki rakip 130–220 puan atıyor (Android 1.0.25).
- 2026-11-23: Güvenlik: takma ad uzunluğu, lig seviyesi ve oda adı için sınırlar eklendi.
- 2026-11-23: Android'de dikey ekran zorunluluğu kaldırıldı (Play'in tablet/PC uyarısı yüzünden).
- 2026-11-23: Mağaza sürümleri iOS 1.0.4 ve Android 1.0.24 oldu. Online odada sıralı oyun ve ortak sonuç geldi. App Store gönderimi, incelemedeki eski gönderimi geri çekip yenisini gönderiyor.
- 2026-11-21: Her hesabın kendi canı/BP'si, reklamla +2 can, Güzel/Harika/Efsane yazıları eklendi. iOS 1.0.3 çıktı.

## Bekleyen işler / kontrol edilecekler
- Android 1.0.26'nın Play'e, iOS güncellemesinin App Store'a gönderilme durumunu konsollardan kontrol et.
