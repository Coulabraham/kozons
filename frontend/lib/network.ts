const LOOPBACK_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);

export function resolveServiceUrl(configuredUrl: string | undefined, fallbackPort: number): string {
  const rawUrl = configuredUrl?.trim();

  if (typeof window === "undefined") {
    return (rawUrl ?? "").replace(/\/$/, "");
  }

  const candidate = rawUrl || `${window.location.protocol}//${window.location.hostname}:${fallbackPort}`;
  try {
    const url = new URL(candidate);
    if (LOOPBACK_HOSTS.has(url.hostname) && !LOOPBACK_HOSTS.has(window.location.hostname)) {
      url.hostname = window.location.hostname;
    }
    return url.toString().replace(/\/$/, "");
  } catch {
    return candidate.replace(/\/$/, "");
  }
}
