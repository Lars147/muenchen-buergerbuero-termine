function updateSubscriptionButton(subscriptionButtonId) {
	const subscriptionButton = document.getElementById(subscriptionButtonId);

	// If available register the service worker
	if ("serviceWorker" in navigator) {
		navigator.serviceWorker
			.register("sw.js")
			.then((registration) => {
				console.log("Service Worker registered:", registration);
			})
			.catch((error) => {
				console.error("Service Worker registration failed:", error);
			});
		navigator.serviceWorker.ready
			.then((registration) => registration.pushManager.getSubscription())
			.then((subscription) => {
				if (subscription) {
					console.log("User is already subscribed:", subscription);
					subscriptionButton.textContent = "Manage Subscription";
				} else {
					console.log("No subscription found.");
					subscriptionButton.textContent = "Subscribe";
				}
			})
			.catch((error) => {
				console.error("Error fetching subscription status:", error);
			});
	} else {
		console.warn("Service workers are not supported in this browser.");

		// Disable the subscribe button if service workers are not supported
		subscriptionButton.disabled = true;
		subscriptionButton.style.backgroundColor = "#999";
		subscriptionButton.title =
			"Push notifications are not supported in this browser.";
	}
}

document.addEventListener("DOMContentLoaded", async () => {
	updateSubscriptionButton("subscribeButton");
});
