// =====================================================================
// Firebase ayarları
// Firebase konsolu → Proje ayarları → Genel → "Uygulamalarınız" → Web uygulaması
// bölümündeki değerleri buraya yapıştır. apiKey "BURAYA" olarak kaldıkça oyun
// sunucusuz DEMO modunda çalışır (veriler yalnızca bu tarayıcıda tutulur).
// =====================================================================
export const firebaseConfig = {
  apiKey: "BURAYA",
  // Google girişinin uygulama içinde sorunsuz çalışması için authDomain olarak
  // barındırma adresini kullan: "<proje-id>.web.app" (firebaseapp.com yerine)
  authDomain: "PROJE-ID.web.app",
  projectId: "PROJE-ID",
  storageBucket: "PROJE-ID.firebasestorage.app",
  messagingSenderId: "",
  appId: ""
};

// Firebase JavaScript SDK sürümü (gstatic CDN)
export const FIREBASE_SDK = "12.12.0";
