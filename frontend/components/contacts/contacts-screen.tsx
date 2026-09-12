"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { Avatar } from "@/components/ui/avatar";
import { CloseIcon, ContactsIcon, SearchIcon, SendIcon } from "@/components/ui/icons";
import { useCreateConversation, useSyncContacts } from "@/lib/api/hooks";
import { useAuthStore } from "@/store/auth-store";
import { useChatStore } from "@/store/chat-store";

export function ContactsScreen() {
  const router = useRouter();
  const contacts = useChatStore((state) => state.contacts);
  const presence = useChatStore((state) => state.presence);
  const openConversation = useChatStore((state) => state.openConversation);
  const user = useAuthStore((state) => state.user);
  const sync = useSyncContacts();
  const createConversation = useCreateConversation();
  const [query, setQuery] = useState("");
  const [syncOpen, setSyncOpen] = useState(false);
  const [numbers, setNumbers] = useState("");
  const filtered = useMemo(() => contacts.filter((contact) => contact.nom_affichage.toLowerCase().includes(query.toLowerCase())), [contacts, query]);
  const synchronize = (event: FormEvent) => {
    event.preventDefault();
    sync.mutate(numbers.split(/[\n,;]/).map((value) => value.trim()).filter(Boolean), { onSuccess: () => setSyncOpen(false) });
  };
  const startChat = (contactId: number) => {
    if (!user) { router.push("/chat"); return; }
    createConversation.mutate({ type: "individuel", participant_ids: [contactId] }, { onSuccess: (conversation) => { openConversation(conversation.id); router.push("/chat"); } });
  };
  const share = () => navigator.share?.({ title: "Kozons", text: "Rejoins-moi sur Kozons pour discuter.", url: window.location.origin });
  return (
    <>
      <div className="mb-5 flex gap-3"><label className="flex h-12 flex-1 items-center gap-2 rounded-2xl border border-line bg-surface px-4 text-muted"><SearchIcon /><span className="sr-only">Rechercher un contact</span><input className="min-w-0 flex-1 bg-transparent text-sm text-ink outline-none" placeholder="Rechercher un contact" value={query} onChange={(event) => setQuery(event.target.value)} /></label><button type="button" onClick={() => setSyncOpen(true)} className="rounded-2xl bg-brand-500 px-5 text-sm font-bold text-white shadow-float hover:bg-brand-600">Synchroniser</button></div>
      {filtered.length ? <section className="overflow-hidden rounded-[1.5rem] border border-line bg-surface shadow-soft" aria-label="Contacts Kozons">{filtered.map((contact, index) => <button key={contact.id} type="button" onClick={() => startChat(contact.id)} className={`flex w-full items-center gap-3 p-4 text-left transition hover:bg-brand-50 dark:hover:bg-elevated ${index ? "border-t border-line" : ""}`}><Avatar user={contact} online={Boolean(presence[contact.id])} /><span className="min-w-0 flex-1"><strong className="block truncate">{contact.nom_affichage}</strong><span className={`text-sm ${presence[contact.id] ? "text-success" : "text-muted"}`}>{presence[contact.id] ? "en ligne" : contact.telephone ?? contact.email}</span></span><SendIcon className="text-brand-500" /></button>)}</section> : <section className="mx-auto mt-20 max-w-sm text-center"><span className="mx-auto grid h-20 w-20 place-items-center rounded-[1.75rem] bg-brand-50 text-brand-600"><ContactsIcon size={34} /></span><h2 className="mt-5 text-xl font-extrabold">Retrouvez vos proches</h2><p className="mt-2 text-sm text-muted">Synchronisez votre carnet ou invitez quelqu’un à rejoindre Kozons.</p><div className="mt-6 flex justify-center gap-3"><button type="button" onClick={() => setSyncOpen(true)} className="rounded-2xl bg-brand-500 px-5 py-3 text-sm font-bold text-white">Synchroniser</button><button type="button" onClick={share} className="rounded-2xl border border-line bg-surface px-5 py-3 text-sm font-bold">Inviter</button></div></section>}
      {syncOpen && <div className="fixed inset-0 z-50 grid place-items-end bg-slate-950/40 p-0 backdrop-blur-sm sm:place-items-center sm:p-4" role="dialog" aria-modal="true" aria-labelledby="sync-title"><form onSubmit={synchronize} className="w-full max-w-lg rounded-t-[2rem] bg-surface p-6 shadow-soft sm:rounded-[2rem]"><div className="flex items-center justify-between"><div><h2 id="sync-title" className="text-xl font-extrabold">Synchroniser le carnet</h2><p className="mt-1 text-sm text-muted">Un numéro par ligne, avec l’indicatif pays.</p></div><button type="button" aria-label="Fermer" onClick={() => setSyncOpen(false)} className="p-2 text-muted"><CloseIcon /></button></div><label className="mt-5 block text-sm font-bold">Numéros<textarea value={numbers} onChange={(event) => setNumbers(event.target.value)} rows={6} placeholder={"+221 77 000 00 00\n+225 07 00 00 00 00"} className="mt-2 w-full resize-none rounded-2xl border border-line bg-elevated p-4 font-mono text-sm outline-none focus:border-brand-500" /></label>{sync.isError && <p className="mt-2 text-sm text-danger">Impossible de synchroniser ces numéros.</p>}<button type="submit" disabled={sync.isPending || !numbers.trim()} className="mt-5 h-12 w-full rounded-2xl bg-brand-500 font-bold text-white disabled:opacity-50">{sync.isPending ? "Recherche…" : "Trouver mes contacts"}</button></form></div>}
    </>
  );
}
