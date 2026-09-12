"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { conversationTitle } from "@/lib/chat-format";
import type { Conversation, Message } from "@/lib/types";

import { MediaViewer } from "./media-viewer";
import { MessageBubble } from "./message-bubble";

interface MessageThreadProps {
  conversation: Conversation;
  conversations: Conversation[];
  messages: Message[];
  currentUserId: number;
  typingUserIds: number[];
  hasOlder: boolean;
  loadingOlder: boolean;
  searchTerm: string;
  activeSearchResultId: number | null;
  onLoadOlder: () => void;
  onEdit: (message: Message, contenu: string) => void;
  onDelete: (message: Message, mode: "me" | "everyone") => void;
  onForward: (message: Message, conversationIds: number[]) => void;
  onReact: (message: Message, emoji: string) => void;
}

export function MessageThread({
  conversation,
  conversations,
  messages,
  currentUserId,
  typingUserIds,
  hasOlder,
  loadingOlder,
  searchTerm,
  activeSearchResultId,
  onLoadOlder,
  onEdit,
  onDelete,
  onForward,
  onReact,
}: MessageThreadProps) {
  const endRef = useRef<HTMLDivElement>(null);
  const [viewerMessageId, setViewerMessageId] = useState<number | null>(null);
  const [forwardedMessage, setForwardedMessage] = useState<Message | null>(null);
  const [targetIds, setTargetIds] = useState<number[]>([]);
  const media = useMemo(
    () => messages.filter((message) => (message.type === "image" || message.type === "video") && !message.supprime_pour_tous_le),
    [messages],
  );

  useEffect(() => {
    if (activeSearchResultId) {
      document.getElementById(`message-${activeSearchResultId}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    endRef.current?.scrollIntoView({ block: "end" });
  }, [activeSearchResultId, messages.length]);

  const toggleTarget = (conversationId: number) => {
    setTargetIds((current) => current.includes(conversationId)
      ? current.filter((id) => id !== conversationId)
      : [...current, conversationId]);
  };
  const closeForward = () => {
    setForwardedMessage(null);
    setTargetIds([]);
  };

  return (
    <div className="chat-pattern scrollbar-subtle flex-1 overflow-y-auto px-3 py-5 sm:px-7" aria-live="polite">
      <div className="mx-auto flex min-h-full max-w-4xl flex-col justify-end gap-2">
        {hasOlder && <button type="button" disabled={loadingOlder} onClick={onLoadOlder} className="mx-auto mb-3 rounded-full bg-surface px-4 py-2 text-xs font-bold text-brand-600 shadow-sm disabled:opacity-50">{loadingOlder ? "Chargement…" : "Afficher les messages précédents"}</button>}
        <p className="mx-auto mb-3 rounded-full bg-surface/80 px-3 py-1 text-xs font-semibold text-muted shadow-sm backdrop-blur">Aujourd’hui</p>
        {messages.map((message) => {
          const sender = conversation.membres.find((member) => member.utilisateur.id === message.sender_id)?.utilisateur;
          return (
            <MessageBubble
              key={`${message.id}-${message.client_id ?? "server"}`}
              message={message}
              mine={message.sender_id === currentUserId}
              sender={sender}
              currentUserId={currentUserId}
              searchTerm={searchTerm}
              activeSearchResult={message.id === activeSearchResultId}
              onOpenMedia={() => setViewerMessageId(message.id)}
              onEdit={(contenu) => onEdit(message, contenu)}
              onDelete={(mode) => onDelete(message, mode)}
              onForward={() => setForwardedMessage(message)}
              onReact={(emoji) => onReact(message, emoji)}
            />
          );
        })}
        {typingUserIds.length > 0 && <div className="flex justify-start"><div className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-bubble-incoming px-4 py-3 shadow-sm" aria-label="En train d’écrire"><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted" /><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted [animation-delay:120ms]" /><span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted [animation-delay:240ms]" /></div></div>}
        <div ref={endRef} />
      </div>
      {viewerMessageId !== null && <MediaViewer media={media} initialId={viewerMessageId} onClose={() => setViewerMessageId(null)} />}
      {forwardedMessage && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/45 p-4" role="dialog" aria-modal="true" aria-labelledby="forward-title">
          <div className="flex max-h-[75vh] w-full max-w-md flex-col rounded-3xl bg-surface p-5 shadow-float">
            <h2 id="forward-title" className="text-lg font-extrabold">Transférer le message</h2>
            <p className="mt-1 text-sm text-muted">Choisissez une ou plusieurs conversations.</p>
            <div className="scrollbar-subtle mt-4 flex-1 space-y-1 overflow-y-auto">
              {conversations.map((item) => (
                <label key={item.id} className="flex cursor-pointer items-center gap-3 rounded-xl p-3 hover:bg-elevated">
                  <input type="checkbox" checked={targetIds.includes(item.id)} onChange={() => toggleTarget(item.id)} className="h-4 w-4 accent-brand-500" />
                  <span className="truncate text-sm font-semibold">{conversationTitle(item, currentUserId)}</span>
                </label>
              ))}
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={closeForward} className="rounded-xl px-4 py-2 text-sm font-bold text-muted hover:bg-elevated">Annuler</button>
              <button type="button" disabled={!targetIds.length} onClick={() => { onForward(forwardedMessage, targetIds); closeForward(); }} className="rounded-xl bg-brand-500 px-4 py-2 text-sm font-bold text-white disabled:opacity-40">Transférer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
