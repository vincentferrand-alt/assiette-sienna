/* Service worker : l'appli s'ouvre même sans internet.
   - la page : réseau d'abord (pour recevoir les nouvelles versions), sinon la copie gardée sur l'appareil ;
   - les modules Firebase : gardés sur l'appareil après le premier chargement ;
   - produits-off.json : géré par l'appli elle-même (IndexedDB), pas ici. */
const V = 'assiette-v1';
const CORE = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(CORE)).catch(() => {}).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
function fromCache(r) {
  return caches.match(r, { ignoreSearch: true }).then(m => m || caches.match('./index.html'))
    .then(m => m || new Response('Hors ligne', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }));
}
function networkFirst(r) {
  return new Promise(resolve => {
    let done = false;
    const finish = x => { if (!done) { done = true; resolve(x); } };
    // réseau trop lent (mauvais wifi) : au bout de 3 s on ouvre la copie de l'appareil
    const t = setTimeout(() => caches.match(r, { ignoreSearch: true }).then(m => { if (m) finish(m); }), 3000);
    fetch(r).then(res => {
      if (res.ok) { const cp = res.clone(); caches.open(V).then(c => c.put(r, cp)); }
      clearTimeout(t); finish(res);
    }).catch(() => { clearTimeout(t); fromCache(r).then(finish); });
  });
}
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin === location.origin) {
    if (u.pathname.endsWith('produits-off.json')) return;
    e.respondWith(networkFirst(r));
  } else if (u.hostname === 'www.gstatic.com' && u.pathname.startsWith('/firebasejs/')) {
    e.respondWith(caches.match(r).then(m => m || fetch(r).then(res => {
      if (res.ok) { const cp = res.clone(); caches.open(V).then(c => c.put(r, cp)); }
      return res;
    })));
  }
});
