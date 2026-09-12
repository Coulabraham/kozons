declare module "next-pwa" {
  type RuntimeCaching = {
    urlPattern: RegExp;
    handler: string;
    method?: string;
    options?: Record<string, unknown>;
  };

  type PWAOptions = {
    dest: string;
    register?: boolean;
    skipWaiting?: boolean;
    disable?: boolean;
    runtimeCaching?: RuntimeCaching[];
    fallbacks?: { document?: string };
  };

  export default function withPWA(
    options: PWAOptions,
  ): (nextConfig: Record<string, unknown>) => Record<string, unknown>;
}
