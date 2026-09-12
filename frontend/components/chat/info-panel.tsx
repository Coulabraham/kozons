"use client";

import { Avatar } from "@/components/ui/avatar";
import { CloseIcon, ImageIcon, TrashIcon } from "@/components/ui/icons";
import { IconButton } from "@/components/ui/icon-button";
import { conversationPeer, conversationTitle } from "@/lib/chat-format";
import type { Conversation, Message } from "@/lib/types";

interface InfoPanelProps {
  conversation: Conversation;
  messages: Message[];
  currentUserId: number;
  leaving?: boolean;
  adminActionPending?: boolean;
  onClose: () => void;
  onLeave: () => void;
  onRename: (name: string) => void;
  onGroupPhoto: (file: File) => void;
  onSendPermission: (permission: "tous" | "admins") => void;
  onRoleChange: (userId: number, role: "admin" | "membre") => void;
  onRemoveMember: (userId: number) => void;
}

export function InfoPanel({ conversation, messages, currentUserId, leaving = false, adminActionPending = false, onClose, onLeave, onRename, onGroupPhoto, onSendPermission, onRoleChange, onRemoveMember }: InfoPanelProps) {
  const peer = conversationPeer(conversation, currentUserId);
  const media = messages.filter((message) => (message.type === "image" || message.type === "video") && !message.supprime_pour_tous_le).slice(-6);
  const currentMembership = conversation.membres.find((member) => member.utilisateur.id === currentUserId);
  const isAdmin = conversation.type === "groupe" && currentMembership?.role === "admin";
  const rename = () => {
    const name = window.prompt("Nouveau nom du groupe", conversation.nom ?? "")?.trim();
    if (name && name !== conversation.nom) onRename(name);
  };
  const removeMember = (userId: number, name: string) => {
    if (window.confirm(`Retirer ${name} du groupe ?`)) onRemoveMember(userId);
  };

  return (
    <aside className="fixed inset-0 z-40 flex w-full flex-col border-l border-line bg-surface sm:left-auto sm:w-[360px] xl:static xl:z-auto xl:w-[340px] xl:shrink-0">
      <header className="flex h-[72px] items-center justify-between border-b border-line px-5"><strong>Informations</strong><IconButton label="Fermer le panneau" onClick={onClose}><CloseIcon /></IconButton></header>
      <div className="scrollbar-subtle flex-1 overflow-y-auto p-5">
        <div className="flex flex-col items-center text-center"><Avatar user={peer ?? undefined} name={conversation.nom ?? undefined} src={conversation.avatar_url} size="xl" /><h2 className="mt-4 text-xl font-extrabold">{conversationTitle(conversation, currentUserId)}</h2><p className="text-sm text-muted">{conversation.type === "groupe" ? `${conversation.membres.length} membres` : peer?.telephone ?? peer?.email}</p></div>
        {isAdmin && <section className="mt-6 rounded-2xl bg-elevated p-4"><h3 className="text-sm font-bold">Administration du groupe</h3><div className="mt-3 grid gap-2"><button type="button" disabled={adminActionPending} onClick={rename} className="rounded-xl bg-surface px-3 py-2 text-left text-sm font-semibold hover:text-brand-600 disabled:opacity-50">Modifier le nom</button><label className="cursor-pointer rounded-xl bg-surface px-3 py-2 text-sm font-semibold hover:text-brand-600">Modifier la photo<input type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" onChange={(event) => { const file = event.target.files?.[0]; if (file) onGroupPhoto(file); event.currentTarget.value = ""; }} /></label><label className="text-xs font-semibold text-muted">Qui peut envoyer des messages ?<select value={conversation.envoi_messages} disabled={adminActionPending} onChange={(event) => onSendPermission(event.target.value as "tous" | "admins")} className="mt-1 w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink"><option value="tous">Tous les membres</option><option value="admins">Administrateurs uniquement</option></select></label></div></section>}
        <section className="mt-8"><div className="mb-3 flex items-center justify-between"><h3 className="text-sm font-bold">Médias partagés</h3><span className="text-xs text-muted">{media.length}</span></div>{media.length ? <div className="grid grid-cols-3 gap-1.5">{media.map((item) => <div key={item.id} className="grid aspect-square place-items-center rounded-xl bg-gradient-to-br from-brand-100 to-blue-300 text-brand-700 dark:from-brand-700 dark:to-slate-700"><ImageIcon size={19} /></div>)}</div> : <p className="rounded-2xl bg-elevated p-4 text-sm text-muted">Aucun média partagé.</p>}</section>
        {conversation.type === "groupe" && <section className="mt-8"><h3 className="mb-3 text-sm font-bold">Membres</h3><div className="space-y-1">{conversation.membres.map((member) => <div key={member.id} className="flex items-center gap-3 rounded-xl p-2 hover:bg-elevated"><Avatar user={member.utilisateur} size="sm" /><span className="min-w-0 flex-1"><strong className="block truncate text-sm">{member.utilisateur.nom_affichage}{member.utilisateur.id === currentUserId ? " (vous)" : ""}</strong><span className="text-xs text-muted">{member.role === "admin" ? "Administrateur" : "Membre"}</span></span>{isAdmin && member.utilisateur.id !== currentUserId && <span className="flex shrink-0 gap-1"><button type="button" disabled={adminActionPending} onClick={() => onRoleChange(member.utilisateur.id, member.role === "admin" ? "membre" : "admin")} className="rounded-lg px-2 py-1 text-[11px] font-bold text-brand-600 hover:bg-brand-50 disabled:opacity-40">{member.role === "admin" ? "Rétrograder" : "Promouvoir"}</button><button type="button" disabled={adminActionPending} onClick={() => removeMember(member.utilisateur.id, member.utilisateur.nom_affichage)} className="rounded-lg px-2 py-1 text-[11px] font-bold text-danger hover:bg-red-50 disabled:opacity-40">Retirer</button></span>}</div>)}</div></section>}
        <button type="button" disabled={leaving} onClick={onLeave} className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl border border-danger/30 px-4 py-3 text-sm font-bold text-danger hover:bg-red-50 disabled:opacity-50 dark:hover:bg-red-950/20"><TrashIcon size={18} />{leaving ? "Veuillez patienter…" : conversation.type === "groupe" ? "Quitter le groupe" : "Supprimer la discussion"}</button>
      </div>
    </aside>
  );
}
