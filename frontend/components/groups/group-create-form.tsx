"use client";

import { useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";

import { Avatar } from "@/components/ui/avatar";
import { ImageIcon } from "@/components/ui/icons";
import { useCreateConversation, useMediaUpload } from "@/lib/api/hooks";
import { useAuthStore } from "@/store/auth-store";
import { useChatStore } from "@/store/chat-store";

export function GroupCreateForm() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const contacts = useChatStore((state) => state.contacts);
  const openConversation = useChatStore((state) => state.openConversation);
  const createConversation = useCreateConversation();
  const mediaUpload = useMediaUpload();
  const [name, setName] = useState("");
  const [selected, setSelected] = useState<number[]>([]);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => () => {
    if (avatarPreview) URL.revokeObjectURL(avatarPreview);
  }, [avatarPreview]);

  const selectAvatar = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    if (!file) return;
    if (avatarPreview) URL.revokeObjectURL(avatarPreview);
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!user) {
      router.push("/chat");
      return;
    }
    try {
      const avatar = avatarFile
        ? await mediaUpload.mutateAsync({ file: avatarFile, type: "image" })
        : null;
      createConversation.mutate(
        { type: "groupe", nom: name, participant_ids: selected, ...(avatar ? { avatar_media_id: avatar.id } : {}) },
        { onSuccess: (conversation) => { openConversation(conversation.id); router.push("/chat"); } },
      );
    } catch {
      // React Query exposes the failure through mutation state for the alert below.
    }
  };

  return (
    <form onSubmit={submit} className="mx-auto max-w-2xl">
      <section className="rounded-[1.5rem] border border-line bg-surface p-5 shadow-soft">
        <div className="flex items-center gap-4">
          <input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" onChange={selectAvatar} className="sr-only" aria-label="Choisir une photo de groupe" />
          <button type="button" onClick={() => fileInput.current?.click()} aria-label="Ajouter une photo au groupe" className="grid h-20 w-20 shrink-0 place-items-center overflow-hidden rounded-full bg-brand-50 text-brand-600 hover:bg-brand-100">
            {avatarPreview ? <img src={avatarPreview} alt="Aperçu de la photo du groupe" className="h-full w-full object-cover" /> : <ImageIcon size={28} />}
          </button>
          <label className="min-w-0 flex-1 text-sm font-bold">Nom du groupe<input value={name} onChange={(event) => setName(event.target.value)} maxLength={150} required placeholder="Ex. Équipe produit" className="mt-2 h-12 w-full rounded-2xl border border-line bg-elevated px-4 text-base font-normal outline-none focus:border-brand-500" /></label>
        </div>
      </section>
      <section className="mt-5 overflow-hidden rounded-[1.5rem] border border-line bg-surface shadow-soft">
        <header className="flex items-center justify-between border-b border-line px-5 py-4"><h2 className="font-extrabold">Ajouter des membres</h2><span className="text-sm font-bold text-brand-600">{selected.length} sélectionné{selected.length > 1 ? "s" : ""}</span></header>
        {contacts.length ? contacts.map((contact) => {
          const checked = selected.includes(contact.id);
          return <label key={contact.id} className="flex cursor-pointer items-center gap-3 border-b border-line p-4 last:border-0 hover:bg-brand-50 dark:hover:bg-elevated"><input type="checkbox" checked={checked} onChange={() => setSelected((current) => checked ? current.filter((id) => id !== contact.id) : [...current, contact.id])} className="h-5 w-5 rounded border-line accent-brand-500" /><Avatar user={contact} size="sm" /><span className="font-semibold">{contact.nom_affichage}</span></label>;
        }) : <p className="p-8 text-center text-sm text-muted">Synchronisez d’abord vos contacts.</p>}
      </section>
      {(createConversation.isError || mediaUpload.isError) && <p role="alert" className="mt-4 text-sm text-danger">Le groupe n’a pas pu être créé.</p>}
      <button type="submit" disabled={!name.trim() || !selected.length || createConversation.isPending || mediaUpload.isPending} className="mt-6 h-12 w-full rounded-2xl bg-brand-500 font-bold text-white shadow-float disabled:opacity-50">
        {createConversation.isPending || mediaUpload.isPending ? "Création…" : `Créer le groupe (${selected.length + 1})`}
      </button>
    </form>
  );
}
