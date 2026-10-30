// Service worker «Кино на двоих». Версию подставляет build.py — при каждой сборке старый кэш сбрасывается.
const VERSION = "__VERSION__";
const CORE = `kino-core-${VERSION}`;
const POSTERS = "kino-posters";
const FONTS = "kino-fonts";
const PRECACHE = ["./", "index.html", "manifest.webmanifest",
  "icons/icon-192.png", "icons/icon-512.png", "icons/maskable-512.png", "icons/apple-touch-icon.png", "icons/favicon-32.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CORE).then(c => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith("kino-core-") && k !== CORE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // Страница: сначала сеть (чтобы получать обновления), без сети — из кэша
  if (req.mode === "navigate") {
    e.respondWith(fetch(req).then(r => { const copy = r.clone(); caches.open(CORE).then(c => c.put("index.html", copy)); return r; })
      .catch(() => caches.match("index.html")));
    return;
  }
  // Постеры: из кэша, а если нет — скачать и запомнить
  if (url.origin === location.origin && url.pathname.includes("/posters/")) {
    e.respondWith(caches.open(POSTERS).then(c => c.match(req).then(hit => hit ||
      fetch(req).then(r => { if (r.ok) c.put(req, r.clone()); return r; }))));
    return;
  }
  // Шрифты Google: отдаём из кэша и тихо обновляем
  if (url.hostname === "fonts.googleapis.com" || url.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.open(FONTS).then(c => c.match(req).then(hit => {
      const net = fetch(req).then(r => { if (r.ok || r.type === "opaque") c.put(req, r.clone()); return r; }).catch(() => hit);
      return hit || net;
    })));
    return;
  }
  // Остальное своё (иконки, манифест): кэш, потом сеть
  if (url.origin === location.origin) {
    e.respondWith(caches.match(req).then(hit => hit || fetch(req)));
  }
});
