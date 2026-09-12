"use client";

import { useEffect } from "react";

import type { Conversation } from "@/lib/types";

type SendText = (text: string) => void;

export function useChatTools(conversations: Conversation[], activeConversationId: number | null, sendText: SendText) {
  useEffect(() => {
    const context = document.modelContext;
    if (!context?.registerTool) return;
    const lifecycle = new AbortController();
    const options = { signal: lifecycle.signal };

    const reportRegistrationError = (error: unknown) => {
      if (process.env.NODE_ENV !== "production") console.warn("WebMCP registration failed", error);
    };

    try {
      void Promise.resolve(context.registerTool({
        name: "read_conversations",
        title: "Lire les discussions",
        description: "Retourne les conversations Kozons actuellement chargées, sans modifier l'application.",
        inputSchema: { type: "object", properties: {}, additionalProperties: false },
        annotations: { readOnlyHint: true, untrustedContentHint: true },
        execute: () => ({
          conversations: conversations.map((conversation) => ({
            id: conversation.id,
            name: conversation.nom ?? "Conversation individuelle",
            type: conversation.type,
            unreadCount: conversation.unread_count ?? 0,
          })),
        }),
      }, options)).catch(reportRegistrationError);

      void Promise.resolve(context.registerTool({
        name: "send_text_message",
        title: "Envoyer un message texte",
        description: "Envoie un message texte dans la conversation Kozons visible. Cette action modifie la discussion.",
        inputSchema: {
          type: "object",
          properties: { text: { type: "string", minLength: 1, maxLength: 10000 } },
          required: ["text"],
          additionalProperties: false,
        },
        annotations: { readOnlyHint: false, untrustedContentHint: false },
        execute: (input: unknown) => {
          if (!activeConversationId) throw new Error("Aucune conversation active.");
          if (!input || typeof input !== "object" || !("text" in input) || typeof input.text !== "string") {
            throw new TypeError("Le champ text est obligatoire.");
          }
          const text = input.text.trim();
          if (!text || text.length > 10000) throw new RangeError("Le message doit contenir entre 1 et 10 000 caractères.");
          sendText(text);
          return { accepted: true, conversationId: activeConversationId };
        },
      }, options)).catch(reportRegistrationError);
    } catch (error) {
      reportRegistrationError(error);
    }

    return () => lifecycle.abort();
  }, [activeConversationId, conversations, sendText]);
}
