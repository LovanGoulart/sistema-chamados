/* ═══════════════════════════════════════════════════════════════
   Service Worker - Sistema de Chamados Colégio Mauá
   Estratégias: Cache-First (estáticos), Network-First (páginas),
   Stale-While-Revalidate (API), Network-Only (POST/auth)
   ═══════════════════════════════════════════════════════════════ */

const CACHE_VERSION = 'v2';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const PAGES_CACHE = `pages-${CACHE_VERSION}`;
const API_CACHE = `api-${CACHE_VERSION}`;
const IMAGES_CACHE = `images-${CACHE_VERSION}`;

// Assets críticos para precache (app shell)
const PRECACHE_ASSETS = [
  '/',
  '/offline',
  '/static/css/estilos.css',
  '/static/js/scripts.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// URLs que NUNCA devem ser cacheadas
const NETWORK_ONLY_PATTERNS = [
  /\/login/,
  /\/logout/,
  /\/admin\/usuarios/,
  /\/admin\/setores/,
  /\/admin\/logs/,
  /\/notificacoes\/ler-todas/,
  /\/api\//,
  /\/upload/,
  /\/enviar-mensagem/,
  /\/atualizar-status/
];

// Páginas dinâmicas (Network-First)
const PAGES_PATTERNS = [
  /\/$/,
  /\/dashboard/,
  /\/chamados/,
  /\/meus-chamados/,
  /\/novo-chamado/,
  /\/chamado\/\d+/,
  /\/relatorios/,
  /\/notificacoes/,
  /\/perfil/
];

// ═══════════════════════════════════════════════════════════════
// INSTALAÇÃO
// ═══════════════════════════════════════════════════════════════
self.addEventListener('install', (event) => {
  console.log('[SW] Instalando...');

  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        // Usar allSettled para não falhar se um asset estiver indisponível
        return Promise.allSettled(
          PRECACHE_ASSETS.map(url => 
            cache.add(url).catch(err => {
              console.warn(`[SW] Falha ao precache: ${url}`, err);
              return null;
            })
          )
        );
      })
      .then(() => {
        console.log('[SW] Precache concluído');
        return self.skipWaiting();
      })
      .catch((err) => {
        console.error('[SW] Erro na instalação:', err);
      })
  );
});

// ═══════════════════════════════════════════════════════════════
// ATIVAÇÃO - Limpar caches antigos
// ═══════════════════════════════════════════════════════════════
self.addEventListener('activate', (event) => {
  console.log('[SW] Ativando...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => {
            return name.startsWith('static-') || 
                   name.startsWith('pages-') || 
                   name.startsWith('api-') || 
                   name.startsWith('images-');
          })
          .filter((name) => {
            return name !== STATIC_CACHE && 
                   name !== PAGES_CACHE && 
                   name !== API_CACHE && 
                   name !== IMAGES_CACHE;
          })
          .map((name) => {
            console.log(`[SW] Deletando cache antigo: ${name}`);
            return caches.delete(name);
          })
      );
    }).then(() => {
      console.log('[SW] Ativado e controlando clientes');
      return self.clients.claim();
    })
  );
});

// ═══════════════════════════════════════════════════════════════
// FETCH - Interceptar requisições
// ═══════════════════════════════════════════════════════════════
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorar requisições não-GET
  if (request.method !== 'GET') {
    return;
  }

  // Ignorar requisições de extensões do browser
  if (url.protocol === 'chrome-extension:' || url.protocol === 'moz-extension:') {
    return;
  }

  // NETWORK-ONLY: Auth, admin, uploads, APIs
  if (NETWORK_ONLY_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    return;
  }

  // CACHE-FIRST: Assets estáticos (CSS, JS, fontes, ícones)
  if (isStaticAsset(request)) {
    event.respondWith(cacheFirst(request, STATIC_CACHE));
    return;
  }

  // CACHE-FIRST: Imagens
  if (request.destination === 'image') {
    event.respondWith(cacheFirst(request, IMAGES_CACHE, { maxAge: 30 * 24 * 60 * 60 }));
    return;
  }

  // NETWORK-FIRST: Páginas HTML
  if (request.destination === 'document' || PAGES_PATTERNS.some(p => p.test(url.pathname))) {
    event.respondWith(networkFirst(request, PAGES_CACHE));
    return;
  }

  // STALE-WHILE-REVALIDATE: API JSON e dados dinâmicos
  if (url.pathname.includes('/api/') || request.headers.get('Accept')?.includes('application/json')) {
    event.respondWith(staleWhileRevalidate(request, API_CACHE));
    return;
  }

  // Fallback: Stale-While-Revalidate para tudo o mais
  event.respondWith(staleWhileRevalidate(request, API_CACHE));
});

// ═══════════════════════════════════════════════════════════════
// ESTRATÉGIAS DE CACHE
// ═══════════════════════════════════════════════════════════════

/** Cache-First: Serve do cache, busca na rede se não estiver */
async function cacheFirst(request, cacheName, options = {}) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  if (cached) {
    // Verificar se o cache expirou (se maxAge for definido)
    if (options.maxAge) {
      const dateHeader = cached.headers.get('sw-cache-date');
      if (dateHeader) {
        const age = (Date.now() - parseInt(dateHeader)) / 1000;
        if (age > options.maxAge) {
          // Cache expirado, buscar na rede em background
          fetchAndCache(request, cache);
          return cached; // Ainda retorna o cache antigo
        }
      }
    }
    return cached;
  }

  try {
    const response = await fetch(request);
    if (response.ok && response.type === 'basic') {
      const responseToCache = response.clone();
      const headers = new Headers(responseToCache.headers);
      headers.append('sw-cache-date', Date.now().toString());

      const modifiedResponse = new Response(responseToCache.body, {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers: headers
      });

      cache.put(request, modifiedResponse);
    }
    return response;
  } catch (error) {
    console.warn('[SW] Falha no cache-first:', error);
    throw error;
  }
}

/** Network-First: Tenta rede, cai para cache se offline */
async function networkFirst(request, cacheName, timeoutMs = 5000) {
  const cache = await caches.open(cacheName);

  try {
    // Race entre fetch e timeout
    const response = await Promise.race([
      fetch(request),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Timeout')), timeoutMs)
      )
    ]);

    if (response.ok) {
      const responseToCache = response.clone();
      cache.put(request, responseToCache);
    }
    return response;
  } catch (error) {
    // Rede falhou ou timeout - tentar cache
    const cached = await cache.match(request);
    if (cached) {
      console.log('[SW] Servindo do cache (offline):', request.url);
      return cached;
    }

    // Se for navegação, retornar página offline
    if (request.destination === 'document') {
      const offlinePage = await caches.match('/offline');
      if (offlinePage) return offlinePage;
    }

    throw error;
  }
}

/** Stale-While-Revalidate: Retorna cache imediatamente, atualiza em background */
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);

  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok && response.type === 'basic') {
        cache.put(request, response.clone());
      }
      return response;
    })
    .catch((err) => {
      console.warn('[SW] SWR fetch falhou:', err);
      return undefined;
    });

  // Retorna cache imediatamente, ou espera rede se não houver cache
  return cached || fetchPromise || new Response('Offline', { 
    status: 503, 
    statusText: 'Service Unavailable',
    headers: { 'Content-Type': 'text/plain' }
  });
}

/** Helper: Busca e cacheia em background */
async function fetchAndCache(request, cache) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response);
    }
  } catch (err) {
    console.warn('[SW] Background fetch falhou:', err);
  }
}

/** Verifica se é asset estático */
function isStaticAsset(request) {
  const dest = request.destination;
  const url = request.url;

  return dest === 'style' || 
         dest === 'script' || 
         dest === 'font' ||
         url.includes('.css') ||
         url.includes('.js') ||
         url.includes('.woff') ||
         url.includes('.woff2') ||
         url.includes('font-awesome') ||
         url.includes('fonts.googleapis') ||
         url.includes('fonts.gstatic');
}

// ═══════════════════════════════════════════════════════════════
// BACKGROUND SYNC - Sincronizar quando voltar online
// ═══════════════════════════════════════════════════════════════
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-outbox') {
    event.waitUntil(syncOutbox());
  }
});

async function syncOutbox() {
  // Aqui você implementaria a sincronização de dados pendentes
  // Ex: enviar mensagens de chat, atualizações de status, etc.
  console.log('[SW] Background sync executado');

  // Notificar todos os clientes que estão online
  const clients = await self.clients.matchAll({ type: 'window' });
  clients.forEach(client => {
    client.postMessage({
      type: 'SYNC_COMPLETE',
      message: 'Sincronização concluída'
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// PUSH NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════
self.addEventListener('push', (event) => {
  if (!event.data) return;

  try {
    const data = event.data.json();
    const options = {
      body: data.body || 'Nova notificação',
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/badge-72x72.png',
      tag: data.tag || 'default',
      requireInteraction: data.requireInteraction || false,
      actions: data.actions || [],
      data: {
        url: data.url || '/',
        ...data
      }
    };

    event.waitUntil(
      self.registration.showNotification(
        data.title || 'Sistema de Chamados',
        options
      )
    );
  } catch (err) {
    console.error('[SW] Erro no push:', err);
  }
});

// Clique na notificação
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const url = event.notification.data?.url || '/';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Tentar focar em uma janela existente
        for (const client of clientList) {
          if (client.url === url && 'focus' in client) {
            return client.focus();
          }
        }
        // Abrir nova janela
        if (self.clients.openWindow) {
          return self.clients.openWindow(url);
        }
      })
  );
});

// ═══════════════════════════════════════════════════════════════
// MENSAGENS DO CLIENTE
// ═══════════════════════════════════════════════════════════════
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data?.type === 'GET_VERSION') {
    event.ports[0]?.postMessage({ version: CACHE_VERSION });
  }

  if (event.data?.type === 'CLEAR_CACHES') {
    event.waitUntil(
      caches.keys().then((names) => 
        Promise.all(names.map((name) => caches.delete(name)))
      ).then(() => {
        event.ports[0]?.postMessage({ cleared: true });
      })
    );
  }
});

// ═══════════════════════════════════════════════════════════════
// PERIODIC BACKGROUND SYNC (Chromium-only, PWA instalado)
// ═══════════════════════════════════════════════════════════════
self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'check-notifications') {
    event.waitUntil(checkNewNotifications());
  }
});

async function checkNewNotifications() {
  // Verificar novas notificações em background
  try {
    const response = await fetch('/api/notificacoes/pendentes');
    if (response.ok) {
      const data = await response.json();
      if (data.count > 0) {
        self.registration.showNotification(
          'Sistema de Chamados',
          {
            body: `Você tem ${data.count} notificação(ões) nova(s)`,
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/badge-72x72.png',
            tag: 'pending-notifications',
            data: { url: '/notificacoes' }
          }
        );
      }
    }
  } catch (err) {
    console.warn('[SW] Periodic sync falhou:', err);
  }
}

console.log('[SW] Service Worker carregado');
