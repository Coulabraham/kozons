"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { resolveServiceUrl } from "@/lib/network";
import type { Message, MessageReceipt } from "@/lib/types";
import { useAuthStore } from "@/store/auth-store";
import { useChatStore } from "@/store/chat-store";

import { createUserRealtimeConnection } from "./transport";

const SOCKET_URL = resolveServiceUrl(process.env.NEXT_PUBLIC_SOCKET_URL, 8001);

export function useUserRealtime() {
  const token = useAuthStore((state) => state.accessToken);
  const userId = useAuthStore((state) => state.user?.id);
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!token || !userId) return;
    const socket = createUserRealtimeConnection(SOCKET_URL, token);
    const upsert = (message: Message) => useChatStore.getState().upsertMessage(message);
    socket.on("message.new", upsert);
    socket.on("message.updated", upsert);
    socket.on("message.deleted", upsert);
    socket.on("reaction.updated", upsert);
    socket.on("receipt.updated", (payload: { message_id: number; conversation_id: number; user_id: number; status: MessageReceipt["statut"]; date_maj: string }) => {
      useChatStore.getState().updateReceipt(payload.conversation_id, payload.message_id, {
        user_id: payload.user_id,
        statut: payload.status,
        date_maj: payload.date_maj,
      });
    });
    socket.on("message.hidden", (payload: { message_id: number; conversation_id: number; user_id: number }) => {
      if (payload.user_id === userId) {
        useChatStore.getState().removeMessage(payload.conversation_id, payload.message_id);
      }
    });
    socket.on("conversation.changed", (payload: { event: string; conversation_id: number; user_id?: number }) => {
      if (payload.event === "member.removed" && payload.user_id === userId) {
        useChatStore.getState().removeConversation(payload.conversation_id);
      }
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    });
    return () => socket.disconnect();
  }, [queryClient, token, userId]);
}
