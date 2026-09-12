import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";

import { AppProviders } from "@/components/providers/app-providers";

import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Kozons", template: "%s · Kozons" },
  description: "Discussions privées et groupes sur Kozons.",
  applicationName: "Kozons",
  manifest: "/manifest.json",
  icons: {
    icon: "/branding/kozons-app-icon.png",
    apple: "/branding/kozons-app-icon.png",
  },
  appleWebApp: { capable: true, statusBarStyle: "default", title: "Kozons" },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#229ED9" },
    { media: "(prefers-color-scheme: dark)", color: "#172530" },
  ],
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="fr" suppressHydrationWarning>
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
