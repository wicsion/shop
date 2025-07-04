// Название кэша
const CACHE_NAME = 'my-cache-v2'; // Изменил версию для обновления
const OFFLINE_URL = '/offline/'; // Страница для оффлайн режима

// URL-адреса для предварительного кэширования (только критически важные)
const PRE_CACHE_URLS = [
  '/',
  '/static/css/styles.css',
  '/static/js/app.js',
  '/static/images/logo.png',
  OFFLINE_URL
];

// Установка Service Worker с обработкой ошибок
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Кэширование критических ресурсов');
        return cache.addAll(PRE_CACHE_URLS.map(url => new Request(url, {credentials: 'same-origin'})))
          .catch(error => {
            console.error('Ошибка при кэшировании:', error);
          });
      })
      .then(() => {
        console.log('Пропускаем ожидание активации');
        return self.skipWaiting();
      })
  );
});

// Активация (очистка старых кэшей)
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cache => {
          if (cache !== CACHE_NAME) {
            console.log('Удаляем старый кэш:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => {
      console.log('Активация завершена');
      return self.clients.claim();
    })
  );
});

// Улучшенный перехват запросов
self.addEventListener('fetch', event => {
  // Пропускаем POST-запросы и другие не-GET
  if (event.request.method !== 'GET') return;

  // Для навигационных запросов используем стратегию "сеть с fallback на кэш"
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  // Для остальных запросов: сначала кэш, потом сеть
  event.respondWith(
    caches.match(event.request)
      .then(cachedResponse => {
        return cachedResponse || fetch(event.request)
          .then(response => {
            // Кэшируем только успешные ответы и статические ресурсы
            if (response && response.status === 200 &&
                (event.request.url.startsWith('http') &&
                 !event.request.url.includes('/api/'))) {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME)
                .then(cache => cache.put(event.request, responseToCache));
            }
            return response;
          })
          .catch(error => {
            console.error('Fetch failed:', error);
            // Можно вернуть fallback-ресурс для определенных типов запросов
            if (event.request.headers.get('accept').includes('image')) {
              return caches.match('/static/images/placeholder.png');
            }
          });
      })
  );
});