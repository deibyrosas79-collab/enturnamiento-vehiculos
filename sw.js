self.addEventListener('push', function (event) {
    let data = {};
    try { data = event.data.json(); } catch (_) {}
    const title = data.title || 'Enturnamiento Vehículos';
    const options = {
        body: data.body || '',
        icon: '/assets/logo-logistica.png',
        badge: '/assets/logo-logistica.png',
        vibrate: [200, 100, 200],
        tag: 'ev-' + (data.tag || 'notif'),
        renotify: true,
        data: { url: data.url || '/' },
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    event.waitUntil(clients.openWindow(event.notification.data.url || '/'));
});
