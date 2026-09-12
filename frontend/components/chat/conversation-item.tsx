import { Avatar } from "@/components/ui/avatar";
import { CheckDoubleIcon, CheckIcon } from "@/components/ui/icons";
import { compactDate, conversationPeer, conversationTitle, previewText } from "@/lib/chat-format";
import type { Conversation } from "@/lib/types";

export function ConversationItem({ conversation, currentUserId, online, active, onClick }: { conversation: Conversation; currentUserId: number; online: boolean; active: boolean; onClick: () => void }) {
  const peer = conversationPeer(conversation, currentUserId);
  const last = conversation.last_message;
  const mine = last?.sender_id === currentUserId;
  const read = last?.receipts?.some((receipt) => receipt.statut === "lu");
  return (
    <button type="button" onClick={onClick} className={`group flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left transition duration-200 ease-calm ${active ? "bg-brand-500 text-white" : "hover:bg-brand-50 dark:hover:bg-elevated"}`} aria-pressed={active}>
      <Avatar user={peer ?? undefined} name={conversation.nom ?? undefined} src={conversation.avatar_url} online={online} />
      <span className="min-w-0 flex-1">
        <span className="flex items-baseline justify-between gap-2"><strong className="truncate text-[0.95rem]">{conversationTitle(conversation, currentUserId)}</strong><time className={`shrink-0 text-xs ${active ? "text-white/80" : "text-muted"}`}>{last ? compactDate(last.date_envoi) : ""}</time></span>
        <span className="mt-1 flex items-center gap-1.5"><span className={`flex min-w-0 flex-1 items-center gap-1 truncate text-sm ${active ? "text-white/80" : "text-muted"}`}>{mine && (read ? <CheckDoubleIcon size={16} className={active ? "text-white" : "text-brand-500"} /> : <CheckIcon size={16} />)}<span className="truncate">{previewText(last)}</span></span>{Boolean(conversation.unread_count) && <span className={`grid min-h-5 min-w-5 place-items-center rounded-full px-1.5 text-[11px] font-bold ${active ? "bg-white text-brand-600" : "bg-brand-500 text-white"}`}>{conversation.unread_count}</span>}</span>
      </span>
    </button>
  );
}
