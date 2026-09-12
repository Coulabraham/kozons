import { io } from "socket.io-client";

type Listener = (payload?: never) => void;

export interface RealtimeConnection {
  on: (event: string, listener: (payload: any) => void) => void;
  emit: (event: string, payload?: Record<string, unknown>) => void;
  disconnect: () => void;
}

function socketIoConnection(url: string, token: string, conversationId: number): RealtimeConnection {
  return io(url, {
    path: "/socket.io",
    transports: ["websocket"],
    auth: { token },
    query: { conversation_id: String(conversationId) },
    reconnectionDelay: 800,
    reconnectionDelayMax: 5000,
  });
}

function channelsConnection(url: string, token: string, conversationId: number): RealtimeConnection {
  const wsBase = url.replace(/^http/, "ws").replace(/\/$/, "");
  const socket = new WebSocket(
    `${wsBase}/ws/conversations/${conversationId}/`,
    ["kozons", `kozons.jwt.${token}`],
  );
  const listeners = new Map<string, Set<(payload: any) => void>>();
  const dispatch = (event: string, payload?: unknown) => listeners.get(event)?.forEach((listener) => listener(payload));
  socket.addEventListener("open", () => dispatch("connect"));
  socket.addEventListener("close", () => dispatch("disconnect"));
  socket.addEventListener("message", (message) => {
    try {
      const envelope = JSON.parse(String(message.data)) as { event: string; data?: unknown; error?: unknown };
      dispatch(envelope.event, envelope.data ?? envelope.error);
    } catch {
      dispatch("error", { detail: "Événement temps réel illisible." });
    }
  });
  return {
    on(event, listener) {
      const current = listeners.get(event) ?? new Set();
      current.add(listener);
      listeners.set(event, current);
    },
    emit(event, payload = {}) {
      if (event === "conversation.join" || event === "conversation.leave") return;
      if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ event, ...payload }));
    },
    disconnect() {
      socket.close(1000, "client disconnect");
      listeners.clear();
    },
  };
}

export function createRealtimeConnection(url: string, token: string, conversationId: number) {
  return process.env.NEXT_PUBLIC_REALTIME_TRANSPORT === "channels"
    ? channelsConnection(url, token, conversationId)
    : socketIoConnection(url, token, conversationId);
}

export function createUserRealtimeConnection(url: string, token: string): RealtimeConnection {
  if (process.env.NEXT_PUBLIC_REALTIME_TRANSPORT !== "channels") {
    return io(url, {
      path: "/socket.io",
      transports: ["websocket"],
      auth: { token },
      query: { scope: "user" },
    });
  }
  const wsBase = url.replace(/^http/, "ws").replace(/\/$/, "");
  const socket = new WebSocket(`${wsBase}/ws/users/me/`, ["kozons", `kozons.jwt.${token}`]);
  const listeners = new Map<string, Set<(payload: any) => void>>();
  const dispatch = (event: string, payload?: unknown) => listeners.get(event)?.forEach((listener) => listener(payload));
  socket.addEventListener("open", () => dispatch("connect"));
  socket.addEventListener("close", () => dispatch("disconnect"));
  socket.addEventListener("message", (message) => {
    try {
      const envelope = JSON.parse(String(message.data)) as { event: string; data?: unknown; error?: unknown };
      dispatch(envelope.event, envelope.data ?? envelope.error);
    } catch {
      dispatch("error", { detail: "Événement temps réel illisible." });
    }
  });
  return {
    on(event, listener) {
      const current = listeners.get(event) ?? new Set();
      current.add(listener);
      listeners.set(event, current);
    },
    emit() {},
    disconnect() {
      socket.close(1000, "client disconnect");
      listeners.clear();
    },
  };
}
