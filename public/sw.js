// Top Potada — çevrimdışı önbellek. Yeni sürüm yayımlarken SURUM'ü artır.
const SURUM = 'tp-v1';
const KABUK = ['./', 'index.html', 'backend.js', 'firebase-config.js', 'manifest.webmanifest', 'icons/icon-192.png', 'icons/icon-512.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(SURUM).then(c => c.addAll(KABUK)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => x !== SURUM).map(x => caches.delete(x)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  // Firebase sunucu çağrıları önbelleğe alınmaz
  if (u.hostname.endsWith('googleapis.com') || u.pathname.startsWith('/__/')) return;
  const sdk = u.hostname === 'www.gstatic.com' && u.pathname.startsWith('/firebasejs/');
  if (u.origin !== location.origin && !sdk) return;
  if (e.request.mode === 'navigate') {   // sayfa: önce ağ, yoksa önbellek
    e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open(SURUM).then(x => x.put('index.html', c)); return r; }).catch(() => caches.match('index.html')));
    return;
  }
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => { if (r.ok) { const c = r.clone(); caches.open(SURUM).then(x => x.put(e.request, c)); } return r; })));
});
