"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Message, MessageType, ReceiptStatus } from "@/lib/types";
import { resolveServiceUrl } from "@/lib/network";
import { useAuthStore } from "@/store/auth-store";
import { useChatStore } from "@/store/chat-store";
import { createRealtimeConnection, type RealtimeConnection } from "./transport";

const SOCKET_URL = resolveServiceUrl(process.env.NEXT_PUBLIC_SOCKET_URL, 8001);

export function useConversationRealtime(conversationId: number | null) {
  const token = useAuthStore((state) => state.accessToken);
  const currentUser = useAuthStore((state) => state.user);
  const upsertMessage = useChatStore((state) => state.upsertMessage);
  const setPresence = useChatStore((state) => state.setPresence);
  const setTyping = useChatStore((state) => state.setTyping);
  const socketRef = useRef<RealtimeConnection | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!conversationId || !token) return;
    const socket = createRealtimeConnection(SOCKET_URL, token, conversationId);
    socketRef.current = socket;
    socket.on("connect", () => {
      setConnected(true);
      socket.emit("conversation.join", { conversation_id: conversationId });
    });
    socket.on("disconnect", () => setConnected(false));
    socket.on("message.new", (message: Message) => upsertMessage(message));
    socket.on("receipt.updated", (payload: { message_id: number; user_id: number; status: ReceiptStatus; date_maj: string }) => {
      const message = useChatStore
        .getState()
        .messages[conversationId]?.find((item) => item.id === payload.message_id);
      if (!message) return;
      const receipts = message.receipts.filter((receipt) => receipt.user_id !== payload.user_id);
      upsertMessage({ ...message, receipts: [...receipts, { user_id: payload.user_id, statut: payload.status, date_maj: payload.date_maj }] });
    });
    socket.on("presence.changed", (payload: { user_id: number; online: boolean }) => setPresence(payload.user_id, payload.online));
    socket.on("typing.changed", (payload: { user_id: number; is_typing: boolean }) => setTyping(conversationId, payload.user_id, payload.is_typing));
    return () => {
      socket.emit("conversation.leave", { conversation_id: conversationId });
      socket.disconnect();
      socketRef.current = null;
    };
  }, [conversationId, setPresence, setTyping, token, upsertMessage]);

  const sendMessage = useCallback(
    (payload: { messageType: MessageType; contenu?: string; mediaAssetId?: number; duree?: number }) => {
      if (!conversationId) return;
      if (!currentUser) return;
      const sender = currentUser;
      const clientId = crypto.randomUUID();
      const optimistic: Message = {
        id: -Date.now(),
        client_id: clientId,
        conversation_id: conversationId,
        sender_id: sender.id,
        type: payload.messageType,
        contenu: payload.contenu ?? null,
        media_url: null,
        duree: payload.duree ?? null,
        date_envoi: new Date().toISOString(),
        modifie_le: null,
        supprime_pour_tous_le: null,
        transfere: false,
        receipts: [],
        reactions: [],
        pending: true,
      };
      upsertMessage(optimistic);
      socketRef.current?.emit("message.send", {
        conversation_id: conversationId,
        client_id: clientId,
        message_type: payload.messageType,
        contenu: payload.contenu,
        media_asset_id: payload.mediaAssetId,
        duree: payload.duree,
      });
    },
    [conversationId, currentUser, upsertMessage],
  );

  const sendTyping = useCallback(
    (isTyping: boolean) => socketRef.current?.emit("typing", { conversation_id: conversationId, is_typing: isTyping }),
    [conversationId],
  );

  const sendReceipt = useCallback(
    (messageId: number, status: ReceiptStatus) => socketRef.current?.emit("receipt.update", { conversation_id: conversationId, message_id: messageId, status }),
    [conversationId],
  );

  return { connected, sendMessage, sendTyping, sendReceipt };
}
