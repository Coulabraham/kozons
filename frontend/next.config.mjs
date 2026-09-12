import withPWAInit from "next-pwa";

const withPWA = withPWAInit({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
  fallbacks: { document: "/offline.html" },
  runtimeCaching: [
    {
      urlPattern: /\.(?:js|css|woff2|svg|png|webp)$/i,
      handler: "StaleWhileRevalidate",
      method: "GET",
      options: {
        cacheName: "kozons-static",
        expiration: { maxEntries: 100, maxAgeSeconds: 2592000 },
      },
    },
  ],
});

export default withPWA({
  reactStrictMode: true,
  output: "export",
  images: { unoptimized: true },
});
