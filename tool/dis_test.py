#!/usr/bin/env python3
"""Top Potada: TestFlight dış test (harici test) hazırlığı. Codemagic'te çalışır, tekrar edilebilir.

 1. "Dış test" adlı harici test grubunu bulur ya da açar, herkese açık davet bağlantısını açar.
 2. TestFlight test bilgileri (tr): ne test edilecek, geri bildirim e-postası, gizlilik adresi.
 3. Beta inceleme iletişim bilgileri (app-store/metadata.json → review, telefon ASC_TEL).
 4. En son işlenmiş derlemeyi bulur: şifreleme beyanı, "Bu sürümde neler var" metni.
 5. Derlemeyi gruba ekler ve Apple'ın beta incelemesine gönderir (zaten gönderildiyse atlar).
 6. TESTERS ortam değişkenindeki e-postaları (virgülle) gruba ekler. E-postalar depoya yazılmaz:
    Codemagic'te "Start new build" > Environment variables ile ya da elle App Store Connect'ten eklenir.

Ortam: ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_P8, (isteğe bağlı) TESTERS, ASC_TEL
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

import jwt

BUNDLE = "com.toppotada.oyun"
GRUP = "Dış test"
API = "https://api.appstoreconnect.apple.com/v1"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = json.load(open(os.path.join(ROOT, "app-store", "metadata.json"), encoding="utf-8"))
NE_TEST = ("Top Potada bir sokak basketbolu atış oyunu. Lütfen şunları dene: Tek oyuncu > Macera levelleri, "
           "Rakiple oyna (hızlı maç, bilgisayar ligi ve turnuvası), Çoklu oyuncu > online oda (bir arkadaşınla kod paylaşarak), "
           "Google ya da Apple ile giriş, turnuva ve lig ekranları, oyun içi menü (ses, titreşim, oyunu bitir) ve "
           "telefonun geri hareketiyle menüler arası dönüş. Hata, takılma ya da garip bir şey görürsen "
           "TestFlight'ta ekran görüntüsü alıp geri bildirim gönder.")
YENI = "Dış test sürümü: Macera levelleri, savunmacılar, rakiple oyna ekranı ve canlı odada rakip atışları."
eksik = []


def token():
    now = int(time.time())
    return jwt.encode({"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1000, "aud": "appstoreconnect-v1"},
                      os.environ["ASC_KEY_P8"], algorithm="ES256", headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"})


def call(method, path, body=None, quiet=False):
    url = path if path.startswith("http") else API + path
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")
        if not quiet:
            print(f"HATA {method} {path.split('?')[0]} -> {e.code} {msg[:600]}")
        e.body = msg
        raise


def adim(baslik, fn):
    print(f"\n== {baslik}")
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        print(f"   !! tamamlanamadı: {e}")
        eksik.append(baslik)
        return None


apps = call("GET", f"/apps?filter[bundleId]={BUNDLE}")["data"]
if not apps:
    sys.exit(f"{BUNDLE} için App Store Connect kaydı yok.")
APP = apps[0]["id"]
print("Uygulama:", apps[0]["attributes"]["name"], APP)


# ---------------------------------------------------------------- 1) grup
def grup():
    gs = call("GET", f"/apps/{APP}/betaGroups?limit=200")["data"]
    for g in gs:
        print(f"   mevcut grup: {g['attributes']['name']} ({'iç' if g['attributes'].get('isInternalGroup') else 'dış'})")
    g = next((g for g in gs if not g["attributes"].get("isInternalGroup") and g["attributes"]["name"] == GRUP), None) \
        or next((g for g in gs if not g["attributes"].get("isInternalGroup")), None)
    if not g:
        g = call("POST", "/betaGroups", {"data": {"type": "betaGroups", "attributes": {"name": GRUP},
                 "relationships": {"app": {"data": {"type": "apps", "id": APP}}}}})["data"]
        print("   dış test grubu açıldı:", GRUP)
    else:
        print("   dış test grubu:", g["attributes"]["name"])
    try:
        g = call("PATCH", f"/betaGroups/{g['id']}", {"data": {"type": "betaGroups", "id": g["id"], "attributes": {
            "publicLinkEnabled": True, "publicLinkLimitEnabled": True, "publicLinkLimit": 1000,
            "feedbackEnabled": True}}})["data"]
    except Exception:  # noqa: BLE001
        print("   (herkese açık bağlantı derleme onaylanınca açılabilir)")
    return g


G = adim("Dış test grubu", grup)
if not G:
    sys.exit(1)


# ---------------------------------------------------------------- 2) test bilgileri
def test_bilgisi():
    locs = call("GET", f"/apps/{APP}/betaAppLocalizations")["data"]
    attrs = {"description": NE_TEST, "feedbackEmail": META["review"]["contactEmail"],
             "privacyPolicyUrl": META["privacyPolicyUrl"], "marketingUrl": META["marketingUrl"]}
    l = next((l for l in locs if l["attributes"]["locale"] in ("tr", "tr-TR")), None)
    if l:
        call("PATCH", f"/betaAppLocalizations/{l['id']}", {"data": {"type": "betaAppLocalizations", "id": l["id"], "attributes": attrs}})
    else:
        call("POST", "/betaAppLocalizations", {"data": {"type": "betaAppLocalizations", "attributes": {**attrs, "locale": "tr"},
             "relationships": {"app": {"data": {"type": "apps", "id": APP}}}}})
    print("   test açıklaması ve geri bildirim e-postası yazıldı")


adim("Test bilgileri", test_bilgisi)


# ---------------------------------------------------------------- 3) beta inceleme iletişim
def iletisim():
    d = call("GET", f"/apps/{APP}/betaAppReviewDetail")["data"]
    a, rv = d["attributes"], META["review"]
    tel = os.environ.get("ASC_TEL") or a.get("contactPhone") or rv.get("contactPhone")
    yeni = {"contactFirstName": a.get("contactFirstName") or rv["contactFirstName"],
            "contactLastName": a.get("contactLastName") or rv["contactLastName"],
            "contactEmail": a.get("contactEmail") or rv["contactEmail"],
            "demoAccountRequired": False, "notes": rv.get("notes", "")[:3900]}
    if tel:
        yeni["contactPhone"] = tel
    call("PATCH", f"/betaAppReviewDetails/{d['id']}", {"data": {"type": "betaAppReviewDetails", "id": d["id"], "attributes": yeni}})
    if not tel:
        eksik.append("Beta inceleme telefonu yok: App Store Connect > TestFlight > Test Bilgileri'nde telefon gir "
                     "(ya da Codemagic'te ASC_TEL, ör. +905xxxxxxxxx) ve işlemi yeniden çalıştır")
    print("   iletişim bilgileri tamam" + ("" if tel else " (telefon eksik)"))


adim("Beta inceleme iletişim bilgileri", iletisim)


# ---------------------------------------------------------------- 4) derleme
def derleme():
    for _ in range(40):
        bs = call("GET", f"/builds?filter[app]={APP}&sort=-uploadedDate&limit=5&fields[builds]=version,processingState,expired,usesNonExemptEncryption,uploadedDate")["data"]
        bs = [b for b in bs if not b["attributes"].get("expired")]
        if bs and bs[0]["attributes"]["processingState"] == "VALID":
            b = bs[0]
            print(f"   derleme {b['attributes']['version']} ({b['attributes']['uploadedDate'][:10]})")
            if b["attributes"].get("usesNonExemptEncryption") is None:
                call("PATCH", f"/builds/{b['id']}", {"data": {"type": "builds", "id": b["id"], "attributes": {"usesNonExemptEncryption": False}}}, quiet=True)
            return b
        print("   derleme işleniyor, bekleniyor…" if bs else "   derleme yok, bekleniyor…")
        time.sleep(30)
    raise RuntimeError("işlenmiş derleme bulunamadı")


B = adim("Son derleme", derleme)


def yenilikler():
    ls = call("GET", f"/builds/{B['id']}/betaBuildLocalizations")["data"]
    l = next((l for l in ls if l["attributes"]["locale"] in ("tr", "tr-TR")), None)
    if l:
        call("PATCH", f"/betaBuildLocalizations/{l['id']}", {"data": {"type": "betaBuildLocalizations", "id": l["id"], "attributes": {"whatsNew": YENI}}})
    else:
        call("POST", "/betaBuildLocalizations", {"data": {"type": "betaBuildLocalizations", "attributes": {"locale": "tr", "whatsNew": YENI},
             "relationships": {"build": {"data": {"type": "builds", "id": B["id"]}}}}})
    print("   'Neler test edilecek' yazıldı")


def gruba_ekle():
    call("POST", f"/betaGroups/{G['id']}/relationships/builds", {"data": [{"type": "builds", "id": B["id"]}]})
    print("   derleme gruba eklendi")


def incelemeye():
    try:
        s = call("GET", f"/builds/{B['id']}/betaAppReviewSubmission", quiet=True).get("data")
    except urllib.error.HTTPError:
        s = None
    if s:
        print("   zaten gönderilmiş, durum:", s["attributes"].get("betaReviewState"))
        return
    s = call("POST", "/betaAppReviewSubmissions", {"data": {"type": "betaAppReviewSubmissions",
             "relationships": {"build": {"data": {"type": "builds", "id": B["id"]}}}}})["data"]
    print("   Apple beta incelemesine gönderildi:", s["attributes"].get("betaReviewState"))


if B:
    adim("Neler test edilecek", yenilikler)
    adim("Derlemeyi gruba ekle", gruba_ekle)
    adim("Beta incelemesine gönder", incelemeye)


# ---------------------------------------------------------------- 6) testçiler
def testciler():
    mails = [m.strip() for m in os.environ.get("TESTERS", "").replace(";", ",").split(",") if "@" in m]
    if not mails:
        print("   TESTERS boş: testçileri App Store Connect'ten elle ekle (README'ye bak)")
        return
    for m in mails:
        try:
            call("POST", "/betaTesters", {"data": {"type": "betaTesters", "attributes": {"email": m},
                 "relationships": {"betaGroups": {"data": [{"type": "betaGroups", "id": G["id"]}]}}}}, quiet=True)
            print(f"   eklendi: {m[:2]}***")
        except urllib.error.HTTPError as e:
            print(f"   {m[:2]}***: {e.code} {getattr(e, 'body', '')[:200]}")


adim("Testçiler", testciler)

g = call("GET", f"/betaGroups/{G['id']}")["data"]["attributes"]
print("\n== Sonuç")
print("Grup:", g["name"], "| herkese açık bağlantı:", g.get("publicLink") or "(beta incelemesi onaylanınca görünür)")
for e in eksik:
    print(" - EKSİK:", e)
