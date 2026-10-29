/**
 * Service Worker - HSH Sales Pro v5.1 (Logo Chuẩn Hoa Sen Home & Menu Tinh Gọn)
 */
const CACHE_NAME = 'hsh-salespro-v5.1';
const CORE_ASSETS = [
    './',
    './index.html',
    './favicon.ico',
    './images/logo_hsh.png',
    './icons/icon-192.png',
    './icons/icon-512.png',
    './css/style.css',
    './js/app.js',
    './js/app-v4.js',
    './manifest.json',
    './data/products.json',
    './data/extras.json',
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(CORE_ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (e) => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        ).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (e) => {
    if (e.request.method !== 'GET') return;
    const url = new URL(e.request.url);

    // Network-first for JSON, HTML, CSS, JS so updates show immediately
    if (url.pathname.endsWith('.json') || url.pathname.endsWith('.js') || url.pathname.endsWith('.css') || url.pathname.endsWith('.html') || url.pathname === '/') {
        e.respondWith(
            fetch(e.request).then(res => {
                if (res.ok) {
                    const clone = res.clone();
                    caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
                }
                return res;
            }).catch(() => caches.match(e.request))
        );
        return;
    }

    // Cache-first for product images
    e.respondWith(
        caches.match(e.request).then(cached => {
            if (cached) return cached;
            return fetch(e.request).then(res => {
                if (res.ok && url.origin === self.location.origin) {
                    const clone = res.clone();
                    caches.open(CACHE_NAME).then(c => c.put(e.request, clone));
                }
                return res;
            });
        })
    );
});
