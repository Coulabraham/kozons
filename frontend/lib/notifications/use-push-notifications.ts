"use client";

import { useMutation } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api/client";

function applicationServerKey(value: string) {
  const padding = "=".repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding).replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(base64), (character) => character.charCodeAt(0));
}

export function usePushNotifications() {
  return useMutation({
    mutationFn: async () => {
      if (!("Notification" in window) || !("serviceWorker" in navigator)) {
        throw new Error("Les notifications ne sont pas prises en charge sur cet appareil.");
      }
      const permission = await Notification.requestPermission();
      if (permission !== "granted") throw new Error("Permission de notification refusée.");
      const publicKey = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY;
      if (!publicKey) throw new Error("La clé VAPID publique n’est pas configurée.");
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey(publicKey),
      });
      const json = subscription.toJSON();
      return apiFetch("/api/notifications/subscriptions/", {
        method: "POST",
        body: JSON.stringify({
          endpoint: subscription.endpoint,
          p256dh: json.keys?.p256dh,
          auth: json.keys?.auth,
        }),
      });
    },
  });
}
