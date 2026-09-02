// Service Worker for AI Smart City Concierge
// Provides offline support, caching strategies, and background sync

const CACHE_NAME = 'city-concierge-v1';
const STATIC_CACHE = 'city-concierge-static-v1';
const DYNAMIC_CACHE = 'city-concierge-dynamic-v1';
const API_CACHE = 'city-concierge-api-v1';
const IMAGE_CACHE = 'city-concierge-images-v1';

const STATIC_ASSETS = [
  '/', '/index.html', '/manifest.json', '/favicon.svg',
];

const CACHE_STRATEGIES = {
  networkFirst: 'network-first',
  cacheFirst: 'cache-first',
  staleWhileRevalidate: 'stale-while-revalidate',
  networkOnly: 'network-only',
  cacheOnly: 'cache-only',
};

const ROUTES = [
  { pattern: /^\/assets\/.*\.(js|css|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot)$/, strategy: CACHE_STRATEGIES.cacheFirst, cache: STATIC_CACHE },
  { pattern: /^\/icons\/.*\.(png|svg)$/, strategy: CACHE_STRATEGIES.cacheFirst, cache: STATIC_CACHE },
  { pattern: /\/manifest\.json$/, strategy: CACHE_STRATEGIES.cacheFirst, cache: STATIC_CACHE },
  { pattern: /\/favicon\.svg$/, strategy: CACHE_STRATEGIES.cacheFirst, cache: STATIC_CACHE },
  { pattern: /^https:\/\/tile\.openstreetmap\.org\/.*$/, strategy: CACHE_STRATEGIES.staleWhileRevalidate, cache: IMAGE_CACHE },
  { pattern: /^https:\/\/api\.mapbox\.com\/.*$/, strategy: CACHE_STRATEGIES.staleWhileRevalidate, cache: IMAGE_CACHE },
  { pattern: /^\/.*\.(png|jpg|jpeg|gif|webp|svg)$/, strategy: CACHE_STRATEGIES.staleWhileRevalidate, cache: IMAGE_CACHE },
  { pattern: /^\/api\/v1\/auth\/.*$/, strategy: CACHE_STRATEGIES.networkFirst, cache: API_CACHE },
  { pattern: /^\/api\/v1\/conversations\/.*$/, strategy: CACHE_STRATEGIES.networkFirst, cache: API_CACHE },
  { pattern: /^\/api\/v1\/itineraries\/.*$/, strategy: CACHE_STRATEGIES.networkFirst, cache: API_CACHE },
  { pattern: /^\/api\/v1\/pois\/.*$/, strategy: CACHE_STRATEGIES.networkFirst, cache: API_CACHE },
  { pattern: /^\/api\/v1\/transit\/.*$/, strategy: CACHE_STRATEGIES.networkFirst, cache: API_CACHE },
  { pattern: /^\/api\/v1\/weather\/.*$/, strategy: CACHE_STRATEGIES.networkFirst, cache: API_CACHE },
  { pattern: /^\/api\/v1\/users\/.*$/, strategy: CACHE_STRATEGIES.networkFirst, cache: API_CACHE },
  { pattern: /^\/api\/v1\/ws\/.*$/, strategy: CACHE_STRATEGIES.networkOnly },
  { pattern: /^\/api\/v1\/conversations\/.*\/messages\/stream/, strategy: CACHE_STRATEGIES.networkOnly },
  { pattern: /^\/.*$/, strategy: CACHE_STRATEGIES.staleWhileRevalidate, cache: DYNAMIC_CACHE },
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => Promise.all(
      cacheNames.filter((name) => ![STATIC_CACHE, DYNAMIC_CACHE, API_CACHE, IMAGE_CACHE].includes(name))
        .map((name) => caches.delete(name))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  if (request.method !== 'GET') {
    if (request.method === 'POST' && url.pathname.includes('/api/')) {
      event.respondWith(handleNetworkOnly(request));
    }
    return;
  }

  if (!url.protocol.startsWith('http')) return;

  const route = ROUTES.find((r) => r.pattern.test(request.url));
  const strategy = route ? route.strategy : CACHE_STRATEGIES.networkFirst;
  const cacheName = route ? route.cache : DYNAMIC_CACHE;

  switch (strategy) {
    case CACHE_STRATEGIES.cacheFirst:
      event.respondWith(handleCacheFirst(request, cacheName));
      break;
    case CACHE_STRATEGIES.networkFirst:
      event.respondWith(handleNetworkFirst(request, cacheName));
      break;
    case CACHE_STRATEGIES.staleWhileRevalidate:
      event.respondWith(handleStaleWhileRevalidate(request, cacheName));
      break;
    case CACHE_STRATEGIES.networkOnly:
      event.respondWith(handleNetworkOnly(request));
      break;
    case CACHE_STRATEGIES.cacheOnly:
      event.respondWith(handleCacheOnly(request, cacheName));
      break;
    default:
      event.respondWith(handleNetworkFirst(request, cacheName));
  }
});

async function handleCacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
  if (cachedResponse) return cachedResponse;

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
  }
}

async function handleNetworkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) cache.put(request, networkResponse.clone());
    return networkResponse;
  } catch (error) {
    const cachedResponse = await cache.match(request);
    if (cachedResponse) return cachedResponse;
    return new Response(JSON.stringify({ error: 'Offline', message: 'No cached data available' }), { status: 503, headers: { 'Content-Type': 'application/json' } });
  }
}

async function handleStaleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
  const fetchPromise = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) cache.put(request, networkResponse.clone());
    return networkResponse;
  }).catch(() => cachedResponse);
  return cachedResponse || fetchPromise;
}

async function handleNetworkOnly(request) {
  try { return await fetch(request); } catch (error) {
    return new Response(JSON.stringify({ error: 'Offline', message: 'Real-time data requires network connection' }), { status: 503, headers: { 'Content-Type': 'application/json' } });
  }
}

async function handleCacheOnly(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
  return cachedResponse || new Response('Not available offline', { status: 503 });
}
// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-itinerary') event.waitUntil(syncItinerary());
  else if (event.tag === 'sync-conversation') event.waitUntil(syncConversation());
  else if (event.tag === 'sync-feedback') event.waitUntil(syncFeedback());
});

async function syncItinerary() {
  const cache = await caches.open('city-concierge-pending');
  const requests = await cache.keys();
  for (const request of requests) {
    try { await fetch(request); await cache.delete(request); } catch (error) { console.log('Failed to sync itinerary:', error); }
  }
}

async function syncConversation() {
  const cache = await caches.open('city-concierge-pending');
  const requests = await cache.keys();
  for (const request of requests) {
    if (request.url.includes('/conversations/') && request.url.includes('/messages')) {
      try { await fetch(request); await cache.delete(request); } catch (error) { console.log('Failed to sync conversation:', error); }
    }
  }
}

async function syncFeedback() {
  const cache = await caches.open('city-concierge-pending');
  const requests = await cache.keys();
  for (const request of requests) {
    if (request.url.includes('/feedback')) {
      try { await fetch(request); await cache.delete(request); } catch (error) { console.log('Failed to sync feedback:', error); }
    }
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  if (!event.data) return;
  const data = event.data.json();
  const options = {
    body: data.body, icon: '/icons/icon-192x192.png', badge: '/icons/badge-72x72.png',
    vibrate: [200, 100, 200], data: data.data || {}, actions: data.actions || [],
    requireInteraction: data.requireInteraction || false,
  };
  event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action) {
    const actionUrl = event.notification.data[`action_${event.action}_url`];
    if (actionUrl) event.waitUntil(clients.openWindow(actionUrl));
  } else if (event.notification.data.url) {
    event.waitUntil(clients.openWindow(event.notification.data.url));
  }
});

// Message handling from main thread
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') self.skipWaiting();
  else if (event.data === 'clearCache') event.waitUntil(clearAllCaches());
  else if (event.data?.type === 'cacheItinerary') event.waitUntil(cacheItineraryForOffline(event.data.itinerary));
  else if (event.data?.type === 'cacheConversation') event.waitUntil(cacheConversationForOffline(event.data.conversation));
});

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(cacheNames.map((name) => caches.delete(name)));
}

async function cacheItineraryForOffline(itinerary) {
  const cache = await caches.open('city-concierge-offline');
  const response = new Response(JSON.stringify(itinerary), { headers: { 'Content-Type': 'application/json' } });
  await cache.put(`/offline/itinerary/${itinerary.id}`, response);
}

async function cacheConversationForOffline(conversation) {
  const cache = await caches.open('city-concierge-offline');
  const response = new Response(JSON.stringify(conversation), { headers: { 'Content-Type': 'application/json' } });
  await cache.put(`/offline/conversation/${conversation.id}`, response);
}

// Periodic background sync
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'update-weather') event.waitUntil(updateWeatherCache());
  else if (event.tag === 'update-transit') event.waitUntil(updateTransitCache());
});

async function updateWeatherCache() { console.log('Periodic weather update triggered'); }
async function updateTransitCache() { console.log('Periodic transit update triggered'); }

console.log('Service Worker loaded: City Concierge v1');