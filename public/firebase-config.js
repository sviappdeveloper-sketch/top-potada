// =====================================================================
// Firebase ayarları
// Firebase konsolu → Proje ayarları → Genel → "Uygulamalarınız" → Web uygulaması
// bölümündeki değerleri buraya yapıştır. apiKey "BURAYA" olarak kaldıkça oyun
// sunucusuz DEMO modunda çalışır (veriler yalnızca bu tarayıcıda tutulur).
// =====================================================================
export const firebaseConfig = {
  apiKey: "AIzaSyCOtFBeHByIHxfS524tth_d3fp_ylShZnY",
  // Google girişinin uygulama içinde sorunsuz çalışması için authDomain olarak
  // barındırma adresini kullan: "<proje-id>.web.app" (firebaseapp.com yerine)
  authDomain: "top-potada.web.app",
  projectId: "top-potada",
  storageBucket: "top-potada.firebasestorage.app",
  messagingSenderId: "746866370670",
  appId: "1:746866370670:web:78e1407efa8db941d21e7f"
};

// Firebase JavaScript SDK sürümü (gstatic CDN)
export const FIREBASE_SDK = "12.12.0";
