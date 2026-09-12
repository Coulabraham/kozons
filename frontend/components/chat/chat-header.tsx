"use client";

import { Avatar } from "@/components/ui/avatar";
import { ArrowLeftIcon, CloseIcon, InfoIcon, SearchIcon } from "@/components/ui/icons";
import { IconButton } from "@/components/ui/icon-button";
import { conversationPeer, conversationSubtitle, conversationTitle } from "@/lib/chat-format";
import type { Conversation } from "@/lib/types";

interface ChatHeaderProps {
  conversation: Conversation;
  currentUserId: number;
  presence: Record<number, boolean>;
  connected: boolean;
  searchQuery: string;
  searchOpen: boolean;
  resultCount: number;
  resultIndex: number;
  onSearchOpen: (open: boolean) => void;
  onSearchChange: (query: string) => void;
  onPreviousResult: () => void;
  onNextResult: () => void;
  onBack: () => void;
  onInfo: () => void;
}

export function ChatHeader({ conversation, currentUserId, presence, connected, searchQuery, searchOpen, resultCount, resultIndex, onSearchOpen, onSearchChange, onPreviousResult, onNextResult, onBack, onInfo }: ChatHeaderProps) {
  const peer = conversationPeer(conversation, currentUserId);
  const online = peer ? Boolean(presence[peer.id]) : false;
  return (
    <header className="flex min-h-[72px] shrink-0 items-center gap-2 border-b border-line bg-surface/95 px-3 backdrop-blur sm:px-5">
      <IconButton label="Retour aux discussions" className="lg:hidden" onClick={onBack}><ArrowLeftIcon /></IconButton>
      {searchOpen ? (
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <label className="flex h-10 min-w-0 flex-1 items-center gap-2 rounded-xl bg-elevated px-3 focus-within:ring-2 focus-within:ring-brand-400/40"><SearchIcon size={18} /><span className="sr-only">Rechercher dans la conversation</span><input autoFocus value={searchQuery} onChange={(event) => onSearchChange(event.target.value)} className="min-w-0 flex-1 bg-transparent text-sm outline-none" placeholder="Rechercher dans les messages" /></label>
          {searchQuery.trim().length >= 2 && <span className="shrink-0 text-xs text-muted">{resultCount ? `${resultIndex + 1}/${resultCount}` : "0 résultat"}</span>}
          <button type="button" disabled={!resultCount} onClick={onPreviousResult} aria-label="Résultat précédent" className="rounded-lg px-2 py-1 text-sm font-bold text-brand-600 disabled:opacity-35">↑</button>
          <button type="button" disabled={!resultCount} onClick={onNextResult} aria-label="Résultat suivant" className="rounded-lg px-2 py-1 text-sm font-bold text-brand-600 disabled:opacity-35">↓</button>
          <IconButton label="Fermer la recherche" onClick={() => { onSearchOpen(false); onSearchChange(""); }}><CloseIcon /></IconButton>
        </div>
      ) : (
        <>
          <Avatar user={peer ?? undefined} name={conversation.nom ?? undefined} src={conversation.avatar_url} online={online} size="sm" />
          <button type="button" onClick={onInfo} className="min-w-0 flex-1 text-left"><strong className="block truncate text-[0.95rem]">{conversationTitle(conversation, currentUserId)}</strong><span className={`block text-xs ${online ? "text-success" : "text-muted"}`}>{conversationSubtitle(conversation, currentUserId, presence)}{connected ? "" : " · reconnexion…"}</span></button>
          <IconButton label="Rechercher dans la conversation" onClick={() => onSearchOpen(true)}><SearchIcon /></IconButton>
          <IconButton label="Informations sur la conversation" onClick={onInfo}><InfoIcon /></IconButton>
        </>
      )}
    </header>
  );
}
