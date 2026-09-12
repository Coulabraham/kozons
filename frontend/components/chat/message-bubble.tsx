"use client";

import { useMemo, useRef, useState } from "react";

import { fullMessageTime } from "@/lib/chat-format";
import type { Message, User } from "@/lib/types";

import { ReceiptIcon } from "./receipt-icon";
import { VoicePlayer } from "./voice-player";

const QUICK_REACTIONS = ["👍", "❤️", "😂", "😮", "😢", "🙏"];

function HighlightedText({ text, query }: { text: string; query?: string }) {
  const parts = useMemo(() => {
    const normalized = query?.trim();
    if (!normalized) return [text];
    return text.split(new RegExp(`(${normalized.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi"));
  }, [query, text]);
  return <>{parts.map((part, index) => part.toLowerCase() === query?.trim().toLowerCase() ? <mark key={index} className="rounded bg-yellow-300 px-0.5 text-slate-950">{part}</mark> : part)}</>;
}

export function MessageBubble({
  message,
  mine,
  sender,
  currentUserId,
  searchTerm,
  activeSearchResult = false,
  onOpenMedia,
  onEdit,
  onDelete,
  onForward,
  onReact,
}: {
  message: Message;
  mine: boolean;
  sender?: User;
  currentUserId: number;
  searchTerm?: string;
  activeSearchResult?: boolean;
  onOpenMedia: () => void;
  onEdit: (contenu: string) => void;
  onDelete: (mode: "me" | "everyone") => void;
  onForward: () => void;
  onReact: (emoji: string) => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const longPressTimer = useRef<number | null>(null);
  const reactionCounts = useMemo(() => {
    const counts = new Map<string, { count: number; mine: boolean }>();
    for (const reaction of message.reactions ?? []) {
      const current = counts.get(reaction.emoji) ?? { count: 0, mine: false };
      counts.set(reaction.emoji, { count: current.count + 1, mine: current.mine || reaction.user_id === currentUserId });
    }
    return Array.from(counts.entries());
  }, [currentUserId, message.reactions]);
  const clearLongPress = () => {
    if (longPressTimer.current !== null) window.clearTimeout(longPressTimer.current);
    longPressTimer.current = null;
  };
  const edit = () => {
    setMenuOpen(false);
    const contenu = window.prompt("Modifier le message", message.contenu ?? "")?.trim();
    if (contenu && contenu !== message.contenu) onEdit(contenu);
  };
  const remove = (mode: "me" | "everyone") => {
    setMenuOpen(false);
    const label = mode === "everyone" ? "tout le monde" : "vous";
    if (window.confirm(`Supprimer ce message pour ${label} ?`)) onDelete(mode);
  };

  return (
    <article
      id={`message-${message.id}`}
      className={`group relative flex animate-fade-up ${mine ? "justify-end" : "justify-start"}`}
      onContextMenu={(event) => { event.preventDefault(); setMenuOpen(true); }}
      onPointerDown={(event) => {
        if (event.pointerType === "mouse") return;
        clearLongPress();
        longPressTimer.current = window.setTimeout(() => setMenuOpen(true), 550);
      }}
      onPointerUp={clearLongPress}
      onPointerCancel={clearLongPress}
      onPointerLeave={clearLongPress}
    >
      {menuOpen && <button type="button" aria-label="Fermer le menu du message" className="fixed inset-0 z-20 cursor-default" onClick={() => setMenuOpen(false)} />}
      <div className={`relative max-w-[86%] rounded-[1.25rem] px-3.5 py-2 shadow-sm transition sm:max-w-[72%] ${mine ? "rounded-br-md bg-bubble-outgoing" : "rounded-bl-md bg-bubble-incoming"} ${activeSearchResult ? "ring-4 ring-yellow-300" : ""}`}>
        {!message.supprime_pour_tous_le && <div className={`absolute -top-9 z-10 hidden rounded-full border border-line bg-surface px-1 py-0.5 shadow-soft group-hover:flex ${mine ? "right-0" : "left-0"}`}>{QUICK_REACTIONS.map((emoji) => <button key={emoji} type="button" aria-label={`Réagir avec ${emoji}`} onClick={() => onReact(emoji)} className="rounded-full p-1 text-base hover:bg-elevated">{emoji}</button>)}</div>}
        {menuOpen && <div className={`absolute top-full z-30 mt-1 min-w-48 rounded-2xl border border-line bg-surface p-2 text-sm text-ink shadow-soft ${mine ? "right-0" : "left-0"}`} role="menu"><div className="mb-2 flex border-b border-line pb-2">{QUICK_REACTIONS.map((emoji) => <button key={emoji} type="button" onClick={() => { onReact(emoji); setMenuOpen(false); }} className="rounded-full p-1 hover:bg-elevated">{emoji}</button>)}</div>{mine && message.type === "texte" && !message.supprime_pour_tous_le && <button type="button" role="menuitem" onClick={edit} className="block w-full rounded-lg px-3 py-2 text-left hover:bg-elevated">Modifier</button>}<button type="button" role="menuitem" onClick={() => { setMenuOpen(false); onForward(); }} disabled={Boolean(message.supprime_pour_tous_le)} className="block w-full rounded-lg px-3 py-2 text-left hover:bg-elevated disabled:opacity-40">Transférer</button>{mine && <><button type="button" role="menuitem" onClick={() => remove("me")} className="block w-full rounded-lg px-3 py-2 text-left text-danger hover:bg-red-50 dark:hover:bg-red-950/20">Supprimer pour moi</button><button type="button" role="menuitem" onClick={() => remove("everyone")} className="block w-full rounded-lg px-3 py-2 text-left text-danger hover:bg-red-50 dark:hover:bg-red-950/20">Supprimer pour tous</button></>}</div>}
        {!mine && sender && <p className="mb-1 text-xs font-bold text-brand-600">{sender.nom_affichage}</p>}
        {message.transfere && !message.supprime_pour_tous_le && <p className="mb-1 text-[11px] font-semibold italic text-muted">Transféré</p>}
        {message.supprime_pour_tous_le ? <p className="italic text-muted">Message supprimé</p> : <>
          {message.type === "note_vocale" && <VoicePlayer duration={message.duree} />}
          {(message.type === "image" || message.type === "video") && (
            <button type="button" onClick={onOpenMedia} className="relative mb-1 block aspect-[4/3] w-[min(68vw,320px)] overflow-hidden rounded-2xl bg-gradient-to-br from-brand-100 via-cyan-100 to-blue-300 text-left dark:from-brand-700 dark:via-slate-700 dark:to-sky-900" aria-label={message.type === "image" ? "Ouvrir la photo" : "Lire la vidéo"}>
              <span className="absolute inset-0 grid place-items-center"><span className="rounded-full bg-black/35 px-4 py-2 text-sm font-bold text-white backdrop-blur">{message.type === "video" ? "▶ Vidéo" : "Voir la photo"}</span></span>
            </button>
          )}
          {message.contenu && <p className="whitespace-pre-wrap break-words text-[0.95rem] leading-relaxed"><HighlightedText text={message.contenu} query={searchTerm} /></p>}
        </>}
        {reactionCounts.length > 0 && <div className="mt-1 flex flex-wrap gap-1">{reactionCounts.map(([emoji, value]) => <button key={emoji} type="button" onClick={() => onReact(emoji)} className={`rounded-full border px-1.5 py-0.5 text-xs ${value.mine ? "border-brand-500 bg-brand-50 text-brand-700" : "border-line bg-surface/70"}`}>{emoji} {value.count}</button>)}</div>}
        <footer className="mt-0.5 flex items-center justify-end gap-1 text-[11px] text-muted"><time>{fullMessageTime(message.date_envoi)}</time>{message.modifie_le && <span>· modifié</span>}{mine && <ReceiptIcon receipts={message.receipts} pending={message.pending} />}</footer>
      </div>
    </article>
  );
}
