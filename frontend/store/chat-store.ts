import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Conversation, Message, User } from "@/lib/types";

interface ChatState {
  conversations: Conversation[];
  messages: Record<number, Message[]>;
  contacts: User[];
  presence: Record<number, boolean>;
  typing: Record<number, number[]>;
  activeConversationId: number | null;
  mobileView: "list" | "conversation";
  infoPanelOpen: boolean;
  hydrated: boolean;
  setHydrated: (hydrated: boolean) => void;
  setConversations: (conversations: Conversation[]) => void;
  setMessages: (conversationId: number, messages: Message[]) => void;
  upsertMessage: (message: Message) => void;
  removeMessage: (conversationId: number, messageId: number) => void;
  updateReceipt: (conversationId: number, messageId: number, receipt: Message["receipts"][number]) => void;
  setContacts: (contacts: User[]) => void;
  setPresence: (userId: number, online: boolean) => void;
  setTyping: (conversationId: number, userId: number, isTyping: boolean) => void;
  openConversation: (conversationId: number) => void;
  showConversationList: () => void;
  toggleInfoPanel: () => void;
  removeConversation: (conversationId: number) => void;
  resetPrivateData: () => void;
}

const chronological = (messages: Message[]) =>
  [...messages].sort((a, b) =>
    a.date_envoi === b.date_envoi
      ? a.id - b.id
      : a.date_envoi.localeCompare(b.date_envoi),
  );

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      conversations: [],
      messages: {},
      contacts: [],
      presence: {},
      typing: {},
      activeConversationId: null,
      mobileView: "list",
      infoPanelOpen: false,
      hydrated: false,
      setHydrated: (hydrated) => set({ hydrated }),
      setConversations: (conversations) => set({ conversations }),
      setMessages: (conversationId, messages) =>
        set((state) => ({
          messages: { ...state.messages, [conversationId]: chronological(messages) },
        })),
      upsertMessage: (message) =>
        set((state) => {
          const current = state.messages[message.conversation_id] ?? [];
          const index = current.findIndex(
            (item) =>
              item.id === message.id ||
              (!!message.client_id && item.client_id === message.client_id),
          );
          const next = [...current];
          if (index >= 0) next[index] = message;
          else next.push(message);
          const conversations = state.conversations.map((conversation) =>
            conversation.id === message.conversation_id
              ? { ...conversation, last_message: message }
              : conversation,
          );
          return {
            messages: { ...state.messages, [message.conversation_id]: chronological(next) },
            conversations,
          };
        }),
      removeMessage: (conversationId, messageId) =>
        set((state) => ({
          messages: {
            ...state.messages,
            [conversationId]: (state.messages[conversationId] ?? []).filter(
              (message) => message.id !== messageId,
            ),
          },
        })),
      updateReceipt: (conversationId, messageId, receipt) =>
        set((state) => ({
          messages: {
            ...state.messages,
            [conversationId]: (state.messages[conversationId] ?? []).map((message) =>
              message.id === messageId
                ? {
                    ...message,
                    receipts: [
                      ...message.receipts.filter((item) => item.user_id !== receipt.user_id),
                      receipt,
                    ],
                  }
                : message,
            ),
          },
        })),
      setContacts: (contacts) => set({ contacts }),
      setPresence: (userId, online) =>
        set((state) => ({ presence: { ...state.presence, [userId]: online } })),
      setTyping: (conversationId, userId, isTyping) =>
        set((state) => {
          const current = state.typing[conversationId] ?? [];
          const next = isTyping
            ? Array.from(new Set([...current, userId]))
            : current.filter((id) => id !== userId);
          return { typing: { ...state.typing, [conversationId]: next } };
        }),
      openConversation: (activeConversationId) =>
        set({ activeConversationId, mobileView: "conversation" }),
      showConversationList: () => set({ mobileView: "list" }),
      toggleInfoPanel: () => set((state) => ({ infoPanelOpen: !state.infoPanelOpen })),
      removeConversation: (conversationId) =>
        set((state) => ({
          conversations: state.conversations.filter((item) => item.id !== conversationId),
          activeConversationId: state.activeConversationId === conversationId ? null : state.activeConversationId,
          mobileView: "list",
          infoPanelOpen: false,
        })),
      resetPrivateData: () => set({
        conversations: [], messages: {}, contacts: [], presence: {}, typing: {},
        activeConversationId: null, mobileView: "list", infoPanelOpen: false,
      }),
    }),
    {
      name: "kozons-chat-cache",
      version: 1,
      migrate: (persistedState) => ({
        ...(persistedState as ChatState),
        conversations: [],
        messages: {},
        contacts: [],
        activeConversationId: null,
      }),
      partialize: (state) => ({
        conversations: state.conversations,
        messages: state.messages,
        contacts: state.contacts,
        activeConversationId: state.activeConversationId,
      }),
      onRehydrateStorage: () => (state) => state?.setHydrated(true),
    },
  ),
);
