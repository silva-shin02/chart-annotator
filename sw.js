/* sw.js — chart-annotator PWA Service Worker
   2026-04-23: CDN precache + app shell cache-first */
var CACHE_NAME='ca-pwa-v3';
var PRECACHE_URLS=[
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  'https://unpkg.com/react@18/umd/react.production.min.js',
  'https://unpkg.com/react-dom@18/umd/react-dom.production.min.js',
  'https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js',
  'https://www.gstatic.com/firebasejs/10.12.0/firebase-storage-compat.js'
];

self.addEventListener('install',function(e){
  e.waitUntil(
    caches.open(CACHE_NAME).then(function(cache){
      return cache.addAll(PRECACHE_URLS);
    }).then(function(){self.skipWaiting();})
  );
});

self.addEventListener('activate',function(e){
  e.waitUntil(
    caches.keys().then(function(names){
      return Promise.all(
        names.filter(function(n){return n!==CACHE_NAME;})
             .map(function(n){return caches.delete(n);})
      );
    }).then(function(){return self.clients.claim();})
  );
});

self.addEventListener('fetch',function(e){
  var url=e.request.url;
  /* Firebase API / Storage — ネットワーク優先、失敗は無視 */
  if(url.indexOf('firebaseio.com')>=0||
     url.indexOf('firebasestorage.googleapis.com')>=0||
     url.indexOf('googleapis.com/upload')>=0){
    e.respondWith(
      fetch(e.request).catch(function(){
        return new Response('{}',{status:503,headers:{'Content-Type':'application/json'}});
      })
    );
    return;
  }
  /* それ以外 — キャッシュ優先、なければネットワーク (取得後キャッシュ) */
  e.respondWith(
    caches.match(e.request).then(function(cached){
      if(cached)return cached;
      return fetch(e.request).then(function(resp){
        if(resp&&resp.status===200&&e.request.method==='GET'){
          var clone=resp.clone();
          caches.open(CACHE_NAME).then(function(cache){cache.put(e.request,clone);});
        }
        return resp;
      });
    }).catch(function(){
      /* 完全オフライン: index.html へフォールバック */
      if(e.request.mode==='navigate'){
        return caches.match('./index.html');
      }
    })
  );
});

/* SKIP_WAITING message from client */
self.addEventListener('message',function(e){
  if(e.data&&e.data.type==='SKIP_WAITING'){
    self.skipWaiting();
  }
});
