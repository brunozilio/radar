self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("push", (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    payload = {
      title: "Monitoramento",
      body: event.data ? event.data.text() : "Há uma nova atualização.",
    };
  }

  const urgent = Boolean(payload.urgent);
  const baseTitle = payload.title || "Monitoramento";
  const titlePrefix =
    payload.ruleSeverity === "emergency"
      ? "🚨"
      : payload.ruleSeverity === "alert"
        ? "⚠️"
        : payload.ruleSeverity === "attention"
          ? "ℹ️"
          : urgent
            ? "🚨"
            : "";
  const title =
    titlePrefix && !baseTitle.startsWith(titlePrefix)
      ? `${titlePrefix} ${baseTitle}`
      : baseTitle;
  const options = {
    body: payload.body || "Há uma nova atualização.",
    icon: payload.icon || "/icon-192.png",
    badge: payload.badge || "/icon-192.png",
    tag: payload.tag || "monitoramento-rio-taquari",
    renotify: true,
    silent: payload.sound ? false : true,
    requireInteraction: urgent,
    ...(payload.sound
      ? { vibrate: [300, 150, 300, 150, 600] }
      : {}),
    data: {
      url: payload.url || "/",
      type: payload.type || "update",
      severity: payload.severity || null,
      ruleSeverity: payload.ruleSeverity || null,
    },
  };

  event.waitUntil(
    Promise.all([
      self.registration.showNotification(title, options),
      payload.sound
        ? self.clients
            .matchAll({ type: "window", includeUncontrolled: true })
            .then((clients) => {
              clients.forEach((client) =>
                client.postMessage({ type: "play-alert-sound" }),
              );
            })
        : Promise.resolve(),
    ]),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = new URL(
    event.notification.data?.url || "/",
    self.location.origin,
  ).href;

  event.waitUntil(
    self.clients
      .matchAll({ type: "window", includeUncontrolled: true })
      .then(async (clients) => {
        const sameOriginClient = clients.find(
          (client) => new URL(client.url).origin === self.location.origin,
        );
        if (sameOriginClient) {
          await sameOriginClient.focus();
          if ("navigate" in sameOriginClient) {
            await sameOriginClient.navigate(targetUrl);
          }
          return;
        }
        await self.clients.openWindow(targetUrl);
      }),
  );
});
