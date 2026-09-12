"use client";

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

import { useAuthStore } from "@/store/auth-store";
import { useChatStore } from "@/store/chat-store";

import type { Conversation, CursorPage, GlobalSearchResults, Message, PresignResponse, ProcessedMedia, User } from "../types";
import { API_URL, apiFetch } from "./client";

export function useRegister() {
  const setPendingIdentifier = useAuthStore((state) => state.setPendingIdentifier);
  return useMutation({
    mutationFn: (body: { telephone?: string; email?: string; password: string; nom_affichage: string }) =>
      apiFetch<{ user: User; otp_required: boolean }>("/api/auth/register/", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => setPendingIdentifier(data.user.telephone ?? data.user.email),
  });
}

export function useVerifyOtp() {
  return useMutation({
    mutationFn: (body: { identifier: string; code: string }) =>
      apiFetch<{ user: User; verified: boolean }>("/api/auth/verify-otp/", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

export function useResendOtp() {
  return useMutation({
    mutationFn: (identifier: string) =>
      apiFetch<{ sent: boolean }>("/api/auth/resend-otp/", {
        method: "POST",
        body: JSON.stringify({ identifier }),
      }),
  });
}

export function useLogin() {
  const setSession = useAuthStore((state) => state.setSession);
  return useMutation({
    mutationFn: (body: { identifier: string; password: string }) =>
      apiFetch<{ access: string; user: User }>("/api/auth/login/", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => setSession(data.access, data.user),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<void>("/api/auth/logout/", { method: "POST" }, false),
    onSettled: async () => {
      useAuthStore.getState().clearSession();
      useChatStore.getState().resetPrivateData();
      queryClient.clear();
      if ("caches" in window) {
        const names = await caches.keys();
        await Promise.all(names.filter((name) => name.startsWith("kozons-")).map((name) => caches.delete(name)));
      }
    },
  });
}

export function useConversations() {
  const accessToken = useAuthStore((state) => state.accessToken);
  const setConversations = useChatStore((state) => state.setConversations);
  const query = useQuery({
    queryKey: ["conversations"],
    queryFn: () => apiFetch<Conversation[]>("/api/conversations/"),
    enabled: Boolean(accessToken),
  });
  useEffect(() => {
    if (query.data) setConversations(query.data);
  }, [query.data, setConversations]);
  return query;
}

export function useConversationMessages(conversationId: number | null) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const setMessages = useChatStore((state) => state.setMessages);
  const query = useInfiniteQuery({
    queryKey: ["messages", conversationId],
    initialPageParam: "",
    queryFn: ({ pageParam }) =>
      apiFetch<CursorPage<Message>>(
        `/api/conversations/${conversationId}/messages/${pageParam ? `?cursor=${encodeURIComponent(pageParam)}` : ""}`,
      ),
    getNextPageParam: (page) => {
      if (!page.next) return undefined;
      const base = API_URL || (typeof window === "undefined" ? "http://localhost" : window.location.origin);
      return new URL(page.next, base).searchParams.get("cursor") ?? undefined;
    },
    enabled: Boolean(accessToken && conversationId),
  });
  useEffect(() => {
    if (!conversationId || !query.data) return;
    const messages = query.data.pages.flatMap((page) => page.results);
    setMessages(conversationId, messages);
  }, [conversationId, query.data, setMessages]);
  return query;
}

export function useMessageSearch(conversationId: number | null, query: string) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const normalized = query.trim();
  return useQuery({
    queryKey: ["message-search", conversationId, normalized],
    queryFn: () => apiFetch<Message[]>(
      `/api/conversations/${conversationId}/messages/search/?q=${encodeURIComponent(normalized)}`,
    ),
    enabled: Boolean(accessToken && conversationId && normalized.length >= 2),
  });
}

export function useGlobalSearch(query: string) {
  const accessToken = useAuthStore((state) => state.accessToken);
  const normalized = query.trim();
  return useQuery({
    queryKey: ["global-search", normalized],
    queryFn: () => apiFetch<GlobalSearchResults>(
      `/api/conversations/search/?q=${encodeURIComponent(normalized)}`,
    ),
    enabled: Boolean(accessToken && normalized.length >= 2),
  });
}

export function useEditMessage() {
  const upsertMessage = useChatStore((state) => state.upsertMessage);
  return useMutation({
    mutationFn: ({ messageId, contenu }: { messageId: number; contenu: string }) =>
      apiFetch<Message>(`/api/messages/${messageId}/`, {
        method: "PATCH",
        body: JSON.stringify({ contenu }),
      }),
    onSuccess: upsertMessage,
  });
}

export function useDeleteMessage() {
  const upsertMessage = useChatStore((state) => state.upsertMessage);
  const removeMessage = useChatStore((state) => state.removeMessage);
  return useMutation({
    mutationFn: ({ message, mode }: { message: Message; mode: "me" | "everyone" }) =>
      apiFetch<Message | null>(`/api/messages/${message.id}/?mode=${mode}`, { method: "DELETE" }),
    onSuccess: (result, variables) => {
      if (variables.mode === "me") removeMessage(variables.message.conversation_id, variables.message.id);
      else if (result) upsertMessage(result);
    },
  });
}

export function useForwardMessage() {
  const upsertMessage = useChatStore((state) => state.upsertMessage);
  return useMutation({
    mutationFn: ({ messageId, conversationIds }: { messageId: number; conversationIds: number[] }) =>
      apiFetch<Message[]>(`/api/messages/${messageId}/forward/`, {
        method: "POST",
        body: JSON.stringify({ conversation_ids: conversationIds }),
      }),
    onSuccess: (messages) => messages.forEach(upsertMessage),
  });
}

export function useMessageReaction() {
  const upsertMessage = useChatStore((state) => state.upsertMessage);
  return useMutation({
    mutationFn: ({ messageId, emoji }: { messageId: number; emoji: string }) =>
      apiFetch<Message>(`/api/messages/${messageId}/reaction/`, {
        method: "POST",
        body: JSON.stringify({ emoji }),
      }),
    onSuccess: upsertMessage,
  });
}

export function useSyncContacts() {
  const setContacts = useChatStore((state) => state.setContacts);
  return useMutation({
    mutationFn: (telephones: string[]) =>
      apiFetch<{ registered_contacts: User[] }>("/api/contacts/sync/", {
        method: "POST",
        body: JSON.stringify({ telephones }),
      }),
    onSuccess: (data) => setContacts(data.registered_contacts),
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { type: "individuel" | "groupe"; participant_ids: number[]; nom?: string; avatar_media_id?: number }) =>
      apiFetch<Conversation>("/api/conversations/", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });
}

export function useUpdateProfile() {
  const updateUser = useAuthStore((state) => state.updateUser);
  return useMutation({
    mutationFn: (body: { nom_affichage: string; statut_personnalise?: string; avatar_media_id?: number }) =>
      apiFetch<User>("/api/profile/", { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: (user) => updateUser(user),
  });
}

export function useLeaveConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (conversationId: number) =>
      apiFetch<void>(`/api/conversations/${conversationId}/leave/`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });
}

export function useUpdateGroup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ conversationId, ...body }: { conversationId: number; nom?: string; avatar_media_id?: number | null; envoi_messages?: "tous" | "admins" }) =>
      apiFetch<Conversation>(`/api/conversations/${conversationId}/`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });
}

export function useRemoveGroupMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ conversationId, userId }: { conversationId: number; userId: number }) =>
      apiFetch<void>(`/api/conversations/${conversationId}/members/${userId}/`, { method: "DELETE" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });
}

export function useSetGroupMemberRole() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ conversationId, userId, role }: { conversationId: number; userId: number; role: "admin" | "membre" }) =>
      apiFetch<{ user_id: number; role: "admin" | "membre" }>(`/api/conversations/${conversationId}/members/${userId}/role/`, {
        method: "PATCH",
        body: JSON.stringify({ role }),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["conversations"] }),
  });
}

export function useMediaUpload() {
  return useMutation({
    mutationFn: async ({ file, conversationId, type }: { file: File; conversationId?: number; type: "image" | "video" | "note_vocale" }) => {
      const presign = await apiFetch<PresignResponse>("/api/media/presign/", {
        method: "POST",
        body: JSON.stringify({
          type,
          content_type: file.type,
          size: file.size,
          ...(conversationId ? { conversation_id: conversationId } : {}),
        }),
      });
      const form = new FormData();
      Object.entries(presign.upload.fields).forEach(([key, value]) => form.append(key, value));
      form.append("file", file);
      const upload = await fetch(presign.upload.url, { method: "POST", body: form });
      if (!upload.ok) throw new Error("L’upload du média a échoué.");
      let processed = await apiFetch<ProcessedMedia>(`/api/media/${presign.asset.id}/complete/`, { method: "POST" });
      for (let attempt = 0; processed.status !== "pret" && processed.status !== "echec" && attempt < 30; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        processed = await apiFetch<ProcessedMedia>(`/api/media/${presign.asset.id}/`);
      }
      if (processed.status !== "pret") throw new Error("Le traitement du média n’a pas abouti.");
      return { ...presign.asset, statut: processed.status, duree: processed.duration };
    },
  });
}
