import { format, isToday, isYesterday } from "date-fns";
import { fr } from "date-fns/locale";

import type { Conversation, Message, User } from "./types";

export function conversationPeer(conversation: Conversation, currentUserId: number): User | null {
  if (conversation.type === "groupe") return null;
  return conversation.membres.find((member) => member.utilisateur.id !== currentUserId)?.utilisateur ?? null;
}

export function conversationTitle(conversation: Conversation, currentUserId: number) {
  return conversation.nom ?? conversationPeer(conversation, currentUserId)?.nom_affichage ?? "Conversation";
}

export function conversationSubtitle(conversation: Conversation, currentUserId: number, presence: Record<number, boolean>) {
  if (conversation.type === "groupe") return `${conversation.membres.length} membres`;
  const peer = conversationPeer(conversation, currentUserId);
  return peer && presence[peer.id] ? "en ligne" : "vu récemment";
}

export function previewText(message?: Message | null) {
  if (!message) return "Nouvelle conversation";
  if (message.type === "note_vocale") return "🎙 Note vocale";
  if (message.type === "image") return `📷 ${message.contenu ?? "Photo"}`;
  if (message.type === "video") return `🎬 ${message.contenu ?? "Vidéo"}`;
  return message.contenu ?? "Message";
}

export function compactDate(value: string) {
  const date = new Date(value);
  if (isToday(date)) return format(date, "HH:mm", { locale: fr });
  if (isYesterday(date)) return "Hier";
  return format(date, "dd/MM", { locale: fr });
}

export function fullMessageTime(value: string) {
  return format(new Date(value), "HH:mm", { locale: fr });
}
