import { useAuthStore } from "@/store/auth-store";
import { resolveServiceUrl } from "@/lib/network";

export const API_URL = resolveServiceUrl(process.env.NEXT_PUBLIC_API_URL, 8000);

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly details?: unknown,
  ) {
    super(message);
  }
}

async function request(url: string, init: RequestInit) {
  try {
    return await fetch(url, init);
  } catch (error) {
    throw new ApiError(
      "Impossible de joindre le serveur Kozons. Vérifiez qu’il est démarré.",
      0,
      error instanceof Error ? error.name : undefined,
    );
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const data = (await response.json().catch(() => null)) as T | null;
  if (!response.ok) {
    const details = data as { error?: { details?: unknown } } | null;
    throw new ApiError(
      response.status === 401 ? "Votre session a expiré." : "La requête a échoué.",
      response.status,
      details?.error?.details ?? data,
    );
  }
  return data as T;
}

export async function refreshAccessToken(): Promise<string> {
  const { setSession, clearSession } = useAuthStore.getState();
  const response = await request(`${API_URL}/api/auth/refresh/`, {
    method: "POST",
    credentials: "include",
  });
  try {
    const data = await parseResponse<{ access: string; user: import("../types").User }>(response);
    setSession(data.access, data.user);
    return data.access;
  } catch (error) {
    clearSession();
    throw error;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  canRefresh = true,
): Promise<T> {
  const token = useAuthStore.getState().accessToken;
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await request(path.startsWith("http") ? path : `${API_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
  if (response.status === 401 && token && canRefresh) {
    const access = await refreshAccessToken();
    headers.set("Authorization", `Bearer ${access}`);
    return parseResponse<T>(
      await request(path.startsWith("http") ? path : `${API_URL}${path}`, { ...init, headers, credentials: "include" }),
    );
  }
  return parseResponse<T>(response);
}
