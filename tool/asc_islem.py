#!/usr/bin/env python3
"""Top Potada: App Store Connect işlemleri (Codemagic'te çalışır, tarayıcı gerektirmez).

Yaptıkları (her çalıştırmada baştan, güvenle tekrar edilebilir):
 1. Uygulama kaydını paket kimliğinden (com.toppotada.oyun) bulur.
 2. Uygulama bilgileri: ad, alt başlık, gizlilik adresi (tr), kategori (Oyun > Spor / Gündelik).
 3. Sürüm (Config.xcconfig'teki MARKETING_VERSION) yoksa açar; telif satırını yazar.
 4. Sürüm metinleri: açıklama, anahtar kelimeler, tanıtım metni, destek ve pazarlama adresi.
 5. iPhone ekran görüntüleri (6.9"): app-store/ekran-goruntuleri/*.png yüklenir (eskiler silinir).
 6. Yaş derecelendirmesi: şiddet/kumar/cinsellik vb. yok, reklam var.
 7. İçerik hakları ve inceleme iletişim bilgileri + inceleme notu.
 8. Bu sürüme ait en son işlenmiş derlemeyi bekler ve sürüme bağlar.
 9. GONDER=evet ise sürümü Apple incelemesine gönderir.
Sonunda elle yapılması gerekenleri (App Privacy formu, fiyat vb.) listeler.

Ortam: ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_P8, (isteğe bağlı) GONDER, ASC_TEL
Metinler: app-store/metadata.json
"""
import glob
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

import jwt

BUNDLE = "com.toppotada.oyun"
API = "https://api.appstoreconnect.apple.com/v1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = json.load(open(os.path.join(ROOT, "app-store", "metadata.json"), encoding="utf-8"))
LOC = META["locale"]
GONDER = os.environ.get("GONDER", "").lower() in ("1", "evet", "yes", "true")

eksikler = []


def token():
    now = int(time.time())
    return jwt.encode(
        {"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1000, "aud": "appstoreconnect-v1"},
        os.environ["ASC_KEY_P8"],
        algorithm="ES256",
        headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"},
    )


def call(method, path, body=None, quiet=False):
    url = path if path.startswith("http") else API + path
    req = urllib.request.Request(
        url,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")
        if not quiet:
            print(f"HATA {method} {path} -> {e.code} {msg[:700]}")
        e.body = msg
        raise


def adim(baslik, fn):
    """Bir adım hata verirse yazdırıp devam eder (diğer adımlar yine yapılsın)."""
    print(f"\n== {baslik}")
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        print(f"   !! {baslik} tamamlanamadı: {e}")
        eksikler.append(f"{baslik}: otomatik yapılamadı (yukarıdaki HATA satırına bak)")
        return None


# ---------------------------------------------------------------- 1) uygulama
apps = call("GET", f"/apps?filter[bundleId]={BUNDLE}")["data"]
if not apps:
    print(f"App Store Connect'te {BUNDLE} paket kimlikli uygulama kaydı yok.")
    print("App Store Connect > Uygulamalar > + > Yeni Uygulama: Platform iOS, Ad 'Top Potada: Basket Ligi',")
    print(f"Birincil dil Türkçe, Paket kimliği {BUNDLE}, SKU toppotada. Sonra bu işlemi yeniden çalıştır.")
    sys.exit(1)
app = apps[0]
APP_ID = app["id"]
print("Uygulama:", app["attributes"]["name"], APP_ID, "birincil dil:", app["attributes"].get("primaryLocale"))


# ---------------------------------------------------------------- 2) uygulama bilgileri
def uygulama_bilgileri():
    infos = call("GET", f"/apps/{APP_ID}/appInfos")["data"]
    # düzenlenebilir olan (yayında olmayan) appInfo
    info = next((i for i in infos if i["attributes"].get("appStoreState") != "READY_FOR_SALE"
                 and i["attributes"].get("state") != "READY_FOR_DISTRIBUTION"), infos[0])
    iid = info["id"]
    rel = {k: {"data": {"type": "appCategories", "id": META[k]}} for k in
           ("primaryCategory", "primarySubcategoryOne", "primarySubcategoryTwo") if META.get(k)}
    try:
        call("PATCH", f"/appInfos/{iid}", {"data": {"type": "appInfos", "id": iid, "relationships": rel}})
        print("   kategori: Oyun > Spor, Gündelik")
    except urllib.error.HTTPError:
        eksikler.append("Kategori ayarlanamadı: Uygulama Bilgileri > Kategori = Oyunlar (Spor)")
    locs = call("GET", f"/appInfos/{iid}/appInfoLocalizations")["data"]
    attrs = {"name": META["name"], "subtitle": META["subtitle"], "privacyPolicyUrl": META["privacyPolicyUrl"]}
    l = next((x for x in locs if x["attributes"]["locale"] == LOC), None)
    if l:
        try:
            call("PATCH", f"/appInfoLocalizations/{l['id']}", {"data": {"type": "appInfoLocalizations", "id": l["id"], "attributes": attrs}})
        except urllib.error.HTTPError:
            # ad başka uygulamada kullanılıyor olabilir: adı değiştirmeden tekrar dene
            attrs.pop("name")
            call("PATCH", f"/appInfoLocalizations/{l['id']}", {"data": {"type": "appInfoLocalizations", "id": l["id"], "attributes": attrs}})
            eksikler.append(f"Uygulama adı '{META['name']}' yazılamadı (alınmış olabilir); mevcut ad korundu.")
    else:
        call("POST", "/appInfoLocalizations", {"data": {"type": "appInfoLocalizations", "attributes": {"locale": LOC, **attrs},
              "relationships": {"appInfo": {"data": {"type": "appInfos", "id": iid}}}}})
    print("   ad / alt başlık / gizlilik adresi yazıldı")
    return iid


INFO_ID = adim("Uygulama bilgileri", uygulama_bilgileri)

# ---------------------------------------------------------------- 3) sürüm
cfg = open(os.path.join(ROOT, "ios", "Config.xcconfig"), encoding="utf-8").read()
VER = re.search(r"^MARKETING_VERSION\s*=\s*(\S+)", cfg, re.M).group(1)
DUZENLENEBILIR = "PREPARE_FOR_SUBMISSION,DEVELOPER_REJECTED,REJECTED,METADATA_REJECTED,INVALID_BINARY"
surumler = call("GET", f"/apps/{APP_ID}/appStoreVersions?filter[platform]=IOS&filter[appStoreState]={DUZENLENEBILIR}&limit=5")["data"]
if surumler:
    surum = surumler[0]
    if surum["attributes"]["versionString"] != VER:
        try:
            call("PATCH", f"/appStoreVersions/{surum['id']}", {"data": {"type": "appStoreVersions", "id": surum["id"],
                  "attributes": {"versionString": VER}}})
            print(f"Sürüm numarası {VER} olarak güncellendi")
        except urllib.error.HTTPError:
            VER = surum["attributes"]["versionString"]
else:
    surum = call("POST", "/appStoreVersions", {"data": {"type": "appStoreVersions",
                 "attributes": {"platform": "IOS", "versionString": VER},
                 "relationships": {"app": {"data": {"type": "apps", "id": APP_ID}}}}})["data"]
    print("Yeni sürüm açıldı:", VER)
SID = surum["id"]
print("Sürüm:", VER, surum["attributes"].get("appStoreState", ""))
adim("Telif", lambda: call("PATCH", f"/appStoreVersions/{SID}", {"data": {"type": "appStoreVersions", "id": SID,
     "attributes": {"copyright": META["copyright"]}}}))


# ---------------------------------------------------------------- 4) sürüm metinleri
def surum_metinleri():
    locs = call("GET", f"/appStoreVersions/{SID}/appStoreVersionLocalizations")["data"]
    attrs = {k: META[k] for k in ("description", "keywords", "promotionalText", "supportUrl", "marketingUrl")}
    l = next((x for x in locs if x["attributes"]["locale"] == LOC), None)
    if l:
        call("PATCH", f"/appStoreVersionLocalizations/{l['id']}", {"data": {"type": "appStoreVersionLocalizations", "id": l["id"], "attributes": attrs}})
    else:
        l = call("POST", "/appStoreVersionLocalizations", {"data": {"type": "appStoreVersionLocalizations",
                 "attributes": {"locale": LOC, **attrs},
                 "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": SID}}}}})["data"]
    print("   açıklama, anahtar kelimeler, tanıtım metni, destek adresi yazıldı")
    return l["id"]


VLOC = adim("Sürüm metinleri", surum_metinleri)


# ---------------------------------------------------------------- 5) ekran görüntüleri
def ekran_goruntuleri():
    for tip, dosyalar in META["screenshots"].items():
        sets = call("GET", f"/appStoreVersionLocalizations/{VLOC}/appScreenshotSets")["data"]
        s = next((x for x in sets if x["attributes"]["screenshotDisplayType"] == tip), None)
        if not s:
            s = call("POST", "/appScreenshotSets", {"data": {"type": "appScreenshotSets",
                     "attributes": {"screenshotDisplayType": tip},
                     "relationships": {"appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": VLOC}}}}})["data"]
        for eski in call("GET", f"/appScreenshotSets/{s['id']}/appScreenshots")["data"]:
            call("DELETE", f"/appScreenshots/{eski['id']}")
        for yol in dosyalar:
            veri = open(os.path.join(ROOT, yol), "rb").read()
            ad = os.path.basename(yol)
            r = call("POST", "/appScreenshots", {"data": {"type": "appScreenshots",
                     "attributes": {"fileName": ad, "fileSize": len(veri)},
                     "relationships": {"appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": s["id"]}}}}})["data"]
            for op in r["attributes"]["uploadOperations"]:
                parca = veri[op["offset"]:op["offset"] + op["length"]]
                h = {x["name"]: x["value"] for x in op.get("requestHeaders", [])}
                urllib.request.urlopen(urllib.request.Request(op["url"], data=parca, method=op["method"], headers=h)).read()
            call("PATCH", f"/appScreenshots/{r['id']}", {"data": {"type": "appScreenshots", "id": r["id"],
                 "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(veri).hexdigest()}}})
            print("   yüklendi:", ad)


if VLOC:
    adim("Ekran görüntüleri", ekran_goruntuleri)


# ---------------------------------------------------------------- 6) yaş derecelendirmesi
def yas():
    d = call("GET", f"/appInfos/{INFO_ID}/ageRatingDeclaration")["data"]
    temel = {k: "NONE" for k in (
        "alcoholTobaccoOrDrugUseOrReferences", "contests", "gamblingSimulated", "horrorOrFearThemes",
        "matureOrSuggestiveThemes", "medicalOrTreatmentInformation", "profanityOrCrudeHumor",
        "sexualContentGraphicAndNudity", "sexualContentOrNudity", "violenceCartoonOrFantasy",
        "violenceRealistic", "violenceRealisticProlongedGraphicOrSadistic")}
    temel.update({"gambling": False, "unrestrictedWebAccess": False})
    call("PATCH", f"/ageRatingDeclarations/{d['id']}", {"data": {"type": "ageRatingDeclarations", "id": d["id"], "attributes": temel}})
    print("   temel sorular: hepsi 'yok'")
    # 2025'te eklenen sorular (API sürümüne göre bazıları olmayabilir: tek tek denenir)
    yeni = {"advertising": True, "userGeneratedContent": False, "messagingAndChat": False, "parentalControls": False,
            "ageAssurance": False, "healthOrWellnessTopics": False, "lootBox": False, "gunsOrOtherWeapons": "NONE"}
    for k, v in yeni.items():
        try:
            call("PATCH", f"/ageRatingDeclarations/{d['id']}", {"data": {"type": "ageRatingDeclarations", "id": d["id"], "attributes": {k: v}}}, quiet=True)
        except urllib.error.HTTPError:
            print(f"   (soru '{k}' API'de yok, atlandı)")
    print("   yeni sorular: reklam var; sohbet, kullanıcı içeriği, ganimet kutusu yok")


if INFO_ID:
    adim("Yaş derecelendirmesi", yas)

# ---------------------------------------------------------------- 7) içerik hakları + inceleme bilgileri
adim("İçerik hakları", lambda: call("PATCH", f"/apps/{APP_ID}", {"data": {"type": "apps", "id": APP_ID,
     "attributes": {"contentRightsDeclaration": META["contentRights"]}}}))


def inceleme():
    rv = dict(META["review"])
    tel = os.environ.get("ASC_TEL") or rv.get("contactPhone")
    rv.pop("contactPhone", None)
    if tel:
        rv["contactPhone"] = tel
    try:
        d = call("GET", f"/appStoreVersions/{SID}/appStoreReviewDetail", quiet=True).get("data")
    except urllib.error.HTTPError:
        d = None
    if d:
        if not tel and not d["attributes"].get("contactPhone"):
            eksikler.append("İnceleme iletişim telefonu yok: App Store Connect > sürüm > Uygulama İnceleme Bilgileri > Telefon "
                            "(ya da Codemagic'te ASC_TEL değişkeni, ör. +905xxxxxxxxx)")
        call("PATCH", f"/appStoreReviewDetails/{d['id']}", {"data": {"type": "appStoreReviewDetails", "id": d["id"], "attributes": rv}})
    else:
        if not tel:
            eksikler.append("İnceleme iletişim telefonu yok: Codemagic'te ASC_TEL değişkeni ekle (ör. +905xxxxxxxxx) ya da App Store Connect'te gir")
            return
        call("POST", "/appStoreReviewDetails", {"data": {"type": "appStoreReviewDetails", "attributes": rv,
             "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": SID}}}}})
    print("   iletişim ve inceleme notu yazıldı")


adim("İnceleme bilgileri", inceleme)


# ---------------------------------------------------------------- 8) derleme
def derleme():
    deadline = time.time() + 25 * 60
    while True:
        builds = call("GET", f"/builds?filter[app]={APP_ID}&filter[preReleaseVersion.version]={VER}"
                             f"&filter[preReleaseVersion.platform]=IOS&sort=-uploadedDate&limit=5")["data"]
        if not builds:
            eksikler.append(f"{VER} sürümü için yüklenmiş derleme yok: önce 'iOS TestFlight' işlemini çalıştır (main'e gönderim).")
            return None
        son = builds[0]
        a = son["attributes"]
        print(f"   derleme {a['version']}: {a['processingState']}")
        if a["processingState"] == "VALID":
            break
        if a["processingState"] in ("INVALID", "FAILED"):
            eksikler.append("Son derleme Apple tarafından reddedildi: App Store Connect > TestFlight'a ve e-postana bak.")
            return None
        if time.time() > deadline:
            eksikler.append("Derleme hâlâ işleniyor: biraz sonra bu işlemi yeniden çalıştır.")
            return None
        time.sleep(60)
    # şifreleme beyanı (Info.plist'te ITSAppUsesNonExemptEncryption=false var; yine de boşsa doldur)
    if a.get("usesNonExemptEncryption") is None:
        try:
            call("PATCH", f"/builds/{son['id']}", {"data": {"type": "builds", "id": son["id"], "attributes": {"usesNonExemptEncryption": False}}}, quiet=True)
        except urllib.error.HTTPError:
            pass
    call("PATCH", f"/appStoreVersions/{SID}/relationships/build", {"data": {"type": "builds", "id": son["id"]}})
    print("   derleme sürüme bağlandı:", a["version"])
    return son["id"]


BUILD = adim("Derleme", derleme)

# ---------------------------------------------------------------- elle yapılacaklar
print("\n== Kontroller")
try:
    ps = call("GET", f"/apps/{APP_ID}/appPriceSchedule", quiet=True)
    print("   fiyat planı var")
except urllib.error.HTTPError:
    eksikler.append("Fiyat: App Store Connect > Fiyatlandırma ve Kullanılabilirlik > Ücretsiz (0 TL), tüm ülkeler")
eksikler.append("App Privacy (Uygulama Gizliliği) formu API ile doldurulamıyor: yanıtlar app-store/README.md içinde. "
                "Formu bir kez doldurup 'Yayımla' demen yeterli.")

# ---------------------------------------------------------------- 9) incelemeye gönder
if GONDER:
    def gonder():
        if not BUILD:
            raise RuntimeError("bağlı derleme yok")
        sub = call("POST", "/reviewSubmissions", {"data": {"type": "reviewSubmissions", "attributes": {"platform": "IOS"},
                   "relationships": {"app": {"data": {"type": "apps", "id": APP_ID}}}}})["data"]
        call("POST", "/reviewSubmissionItems", {"data": {"type": "reviewSubmissionItems",
             "relationships": {"reviewSubmission": {"data": {"type": "reviewSubmissions", "id": sub["id"]}},
                               "appStoreVersion": {"data": {"type": "appStoreVersions", "id": SID}}}}})
        call("PATCH", f"/reviewSubmissions/{sub['id']}", {"data": {"type": "reviewSubmissions", "id": sub["id"],
             "attributes": {"submitted": True}}})
        print("   İNCELEMEYE GÖNDERİLDİ. Sonuç 1–3 gün içinde e-postayla gelir.")
    adim("İncelemeye gönder", gonder)
else:
    print("\n(İncelemeye gönderilmedi. Hazır olunca 'App Store: incelemeye gönder' işlemini çalıştır.)")

print("\n== EKSİKLER / ELLE YAPILACAKLAR" if eksikler else "\nEksik yok.")
for e in eksikler:
    print(" -", e)
print("Bitti.")
