self.addEventListener('install', (event) => {
	self.skipWaiting();
});

self.addEventListener('activate', (event) => {
	event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
	let payload = {};
	try {
		payload = event.data ? event.data.json() : {};
	} catch (_) {
		payload = { body: event.data ? event.data.text() : '' };
	}

	const title = payload.title || 'Datapus';
	const options = {
		body: payload.body || 'Nova atualizacao para o seu time.',
		icon: '/mockup.png',
		badge: '/avatar.png',
		data: {
			url: payload.url || '/'
		}
	};

	event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
	event.notification.close();

	const targetUrl = event.notification?.data?.url || '/';
	event.waitUntil(
		self.clients
			.matchAll({ type: 'window', includeUncontrolled: true })
			.then((clients) => {
				for (const client of clients) {
					if (client.url === targetUrl && 'focus' in client) {
						return client.focus();
					}
				}
				if (self.clients.openWindow) {
					return self.clients.openWindow(targetUrl);
				}
			})
	);
});
