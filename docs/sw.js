const CACHE_NAME = "muenchen-termine-v1";
const urlsToCache = [
	"/",
	"/index.html",
	"/manifest.json",
	"/reload.js",
	"/subscribeButton.js",
];

// Install event - cache essential files
self.addEventListener("install", (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => {
			console.log("Cache opened");
			return cache.addAll(urlsToCache);
		}),
	);
});

// Activate event - clean up old caches
self.addEventListener("activate", (event) => {
	event.waitUntil(
		caches.keys().then((cacheNames) => {
			return Promise.all(
				cacheNames
					.filter((name) => name !== CACHE_NAME)
					.map((name) => caches.delete(name)),
			);
		}),
	);
});

// Fetch event - serve from cache, fall back to network
self.addEventListener("fetch", (event) => {
	event.respondWith(
		caches
			.match(event.request)
			.then((response) => {
				// Return the cached response if found
				if (response) {
					return response;
				}

				// Otherwise fetch from network
				return fetch(event.request).then((response) => {
					// Don't cache responses that aren't successful or aren't GET requests
					if (
						!response ||
						response.status !== 200 ||
						event.request.method !== "GET"
					) {
						return response;
					}

					// Clone the response as it can only be consumed once
					const responseToCache = response.clone();

					caches.open(CACHE_NAME).then((cache) => {
						cache.put(event.request, responseToCache);
					});

					return response;
				});
			})
			.catch(() => {
				// Return a fallback if both cache and network fail
				if (event.request.mode === "navigate") {
					return caches.match("/index.html");
				}
			}),
	);
});

// Push notification event
self.addEventListener("push", (event) => {
	console.log("Received a push message", event);

	const data = event.data ? event.data.json() : {};
	const title = data.title || "Default Title";
	const options = {
		body: data.message || "Default message",
		icon: data.icon || "/default-icon.png",
		data: {
			url: data.url || "/",
		},
	};

	event.waitUntil(self.registration.showNotification(title, options));
});

// Notification click event
self.addEventListener("notificationclick", (event) => {
	event.notification.close();

	// Get the URL from the notification data or default to homepage
	const urlToOpen = event.notification.data?.url
		? event.notification.data.url
		: "/";

	event.waitUntil(clients.openWindow(urlToOpen));
});
