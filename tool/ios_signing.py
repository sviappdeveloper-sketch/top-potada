#!/usr/bin/env python3
"""Top Potada: App Store Connect API ile iOS imza hazırlığı (Codemagic'te çalışır).

Hatim Kardeşim'deki tool/ios_signing.py ile aynı düzen, ek olarak:
- com.toppotada.oyun paket kimliği yoksa oluşturur,
- "Apple ile Giriş" (APPLE_ID_AUTH) yetkisini açar,
- App Store Connect'te uygulama kaydı yoksa açık bir uyarı yazar (kayıt API ile açılamıyor).

Ortam: ASC_KEY_ID, ASC_ISSUER_ID, ASC_KEY_P8, RUNNER_TEMP, P12_PASS
Çıktı: $RUNNER_TEMP/dagitim.p12, $RUNNER_TEMP/profil.mobileprovision,
       $GITHUB_ENV dosyasına PROFILE_NAME, PROFILE_UUID ve (varsa) APP_STORE_APP_ID.
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import jwt
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

BUNDLE = "com.toppotada.oyun"
APP_NAME = "Top Potada"
PROFILE_NAME = "TopPotada AppStore CI"
API = "https://api.appstoreconnect.apple.com/v1"
TMP = os.environ.get("RUNNER_TEMP", "/tmp")
P12_PASS = os.environ.get("P12_PASS", "toppotada")


def token():
    now = int(time.time())
    return jwt.encode(
        {"iss": os.environ["ASC_ISSUER_ID"], "iat": now, "exp": now + 1000, "aud": "appstoreconnect-v1"},
        os.environ["ASC_KEY_P8"],
        algorithm="ES256",
        headers={"kid": os.environ["ASC_KEY_ID"], "typ": "JWT"},
    )


def call(method, path, body=None, quiet=False):
    req = urllib.request.Request(
        API + path,
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
            print(f"HATA {method} {path} -> {e.code} {msg[:500]}")
        e.body = msg
        raise


# 1) Paket kimliği (yoksa oluştur)
bundles = [b for b in call("GET", f"/bundleIds?filter[identifier]={BUNDLE}")["data"]
           if b["attributes"]["identifier"] == BUNDLE]
if bundles:
    bundle = bundles[0]
    print("Paket kimliği var:", BUNDLE)
else:
    bundle = call("POST", "/bundleIds", {"data": {"type": "bundleIds", "attributes": {
        "identifier": BUNDLE, "name": APP_NAME, "platform": "IOS"}}})["data"]
    print("Paket kimliği oluşturuldu:", BUNDLE)

# 2) Apple ile Giriş yetkisi
# (Bu adım derlemeyi durdurmaz; sorun olursa uyarı yazar ve elle açma yolunu söyler.)
try:
    caps = call("GET", f"/bundleIds/{bundle['id']}/bundleIdCapabilities")["data"]
    have = any(c["attributes"].get("capabilityType") == "APPLE_ID_AUTH" for c in caps)
except urllib.error.HTTPError:
    have = False
if have:
    print("Apple ile Giriş yetkisi açık.")
else:
    base = {"type": "bundleIdCapabilities", "attributes": {"capabilityType": "APPLE_ID_AUTH"},
            "relationships": {"bundleId": {"data": {"type": "bundleIds", "id": bundle["id"]}}}}
    with_settings = json.loads(json.dumps(base))
    with_settings["attributes"]["settings"] = [{"key": "APPLE_ID_AUTH_APP_CONSENT",
                                                "options": [{"key": "PRIMARY_APP_CONSENT"}]}]
    done = False
    for body in (with_settings, base):
        try:
            call("POST", "/bundleIdCapabilities", {"data": body})
            done = True
            break
        except urllib.error.HTTPError as e:
            if e.code == 409:          # zaten açık
                done = True
                break
    print("Apple ile Giriş yetkisi açıldı." if done else
          "UYARI: Apple ile Giriş yetkisi API ile açılamadı. developer.apple.com → Identifiers → "
          "com.toppotada.oyun → 'Sign In with Apple' kutusunu işaretleyip kaydet, sonra derlemeyi yeniden başlat.")

# 3) App Store Connect uygulama kaydı (API ile açılamaz; yoksa yükleme başarısız olur)
apps = call("GET", f"/apps?filter[bundleId]={BUNDLE}")["data"]
if apps:
    print("App Store Connect kaydı var:", apps[0]["attributes"]["name"], apps[0]["id"])
    app_id = apps[0]["id"]
else:
    app_id = ""
    print("UYARI: App Store Connect'te com.toppotada.oyun için uygulama kaydı yok. "
          "Uygulamalar → + → Yeni Uygulama ile 'Top Potada' kaydını aç; yoksa TestFlight yüklemesi reddedilir.")

# 4) Dağıtım sertifikası (sınır doluysa en eskisini iptal edip yeniden dene)
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
csr = (x509.CertificateSigningRequestBuilder()
       .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Top Potada CI")]))
       .sign(key, hashes.SHA256()))
csr_pem = csr.public_bytes(serialization.Encoding.PEM).decode()


def create_cert():
    return call("POST", "/certificates", {"data": {"type": "certificates", "attributes": {
        "csrContent": csr_pem, "certificateType": "DISTRIBUTION"}}})


try:
    cert = create_cert()
except urllib.error.HTTPError:
    existing = call("GET", "/certificates?filter[certificateType]=DISTRIBUTION&limit=50")["data"]
    existing.sort(key=lambda c: c["attributes"].get("expirationDate", ""))
    if not existing:
        sys.exit(1)
    print("Sertifika sınırı dolu; en eski dağıtım sertifikası iptal ediliyor:", existing[0]["id"])
    call("DELETE", f"/certificates/{existing[0]['id']}")
    cert = create_cert()

cert_id = cert["data"]["id"]
x = x509.load_der_x509_certificate(base64.b64decode(cert["data"]["attributes"]["certificateContent"]))
p12 = pkcs12.serialize_key_and_certificates(b"dagitim", key, x, None,
                                            serialization.BestAvailableEncryption(P12_PASS.encode()))
open(os.path.join(TMP, "dagitim.p12"), "wb").write(p12)
print("Dağıtım sertifikası hazır:", cert_id)

# 5) Eski CI profillerini sil, yenisini oluştur (Apple ile Giriş yetkisini içerir)
for p in call("GET", f"/profiles?filter[name]={urllib.parse.quote(PROFILE_NAME)}&limit=50")["data"]:
    call("DELETE", f"/profiles/{p['id']}")
prof = call("POST", "/profiles", {"data": {
    "type": "profiles",
    "attributes": {"name": PROFILE_NAME, "profileType": "IOS_APP_STORE"},
    "relationships": {
        "bundleId": {"data": {"type": "bundleIds", "id": bundle["id"]}},
        "certificates": {"data": [{"type": "certificates", "id": cert_id}]},
    },
}})["data"]["attributes"]
open(os.path.join(TMP, "profil.mobileprovision"), "wb").write(base64.b64decode(prof["profileContent"]))
print("App Store profili hazır:", prof["uuid"])

with open(os.environ.get("GITHUB_ENV", "/dev/null"), "a") as f:
    f.write(f"PROFILE_NAME={PROFILE_NAME}\nPROFILE_UUID={prof['uuid']}\nAPP_STORE_APP_ID={app_id}\n")
