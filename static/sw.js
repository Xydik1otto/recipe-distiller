/* Recipe Distiller service worker: offline shell + cached recipe book.
   Strategy:
   - app shell (/, /index.html, manifest, favicon): cache-first, refresh in background;
   - GET /api/recipes* (the saved book): network-first, previous response stays
     as offline fallback; /api/recipes/export is refreshed on every online visit;
   - everything else: network, no offline fallback (extraction needs the net anyway). */
const CACHE = 'recipe-distiller-v1';
const SHELL = ['/', '/index.html', '/manifest.webmanifest', '/favicon.svg'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  if (req.mode === 'navigate' || url.pathname === '/') {
    e.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put('/', copy));
        return res;
      }).catch(() => caches.match('/'))
    );
    return;
  }

  if (url.pathname.startsWith('/api/recipes')) {
    // the recipe book: try the network, keep the last good copy for offline
    e.respondWith(
      fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      }).catch(() => caches.match(req))
    );
    return;
  }

  if (url.pathname.startsWith('/api/')) return; // extraction etc. — no offline

  // static assets: cache-first
  e.respondWith(
    caches.match(req).then((hit) => hit ||
      fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      }))
  );
});
