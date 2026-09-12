"use client";

import { ChangeEvent, FormEvent, useEffect, useRef, useState } from "react";

import { Avatar } from "@/components/ui/avatar";
import { ImageIcon } from "@/components/ui/icons";
import { errorMessage } from "@/lib/api/error-message";
import { useMediaUpload, useUpdateProfile } from "@/lib/api/hooks";
import { useAuthStore } from "@/store/auth-store";
import { usePreferencesStore, type ThemePreference } from "@/store/preferences-store";

export function ProfileForm() {
  const authenticatedUser = useAuthStore((state) => state.user);
  const user = authenticatedUser ?? {
    id: 0,
    telephone: null,
    email: null,
    nom_affichage: "",
    avatar_url: null,
    statut: "inactif" as const,
  };
  const update = useUpdateProfile();
  const mediaUpload = useMediaUpload();
  const theme = usePreferencesStore((state) => state.theme);
  const setTheme = usePreferencesStore((state) => state.setTheme);
  const [name, setName] = useState(user.nom_affichage);
  const [status, setStatus] = useState(user.statut_personnalise ?? "Disponible sur Kozons");
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
    if (!authenticatedUser) return;
    try {
      const avatar = avatarFile
        ? await mediaUpload.mutateAsync({ file: avatarFile, type: "image" })
        : null;
      await update.mutateAsync({
        nom_affichage: name,
        statut_personnalise: status,
        ...(avatar ? { avatar_media_id: avatar.id } : {}),
      });
    } catch {
      // React Query exposes the failure through mutation state for the alert below.
    }
  };
  const pending = update.isPending || mediaUpload.isPending;

  return (
    <form onSubmit={submit} className="mx-auto max-w-2xl space-y-5">
      <section className="rounded-[1.5rem] border border-line bg-surface p-6 shadow-soft">
        <div className="flex flex-col items-center">
          <div className="relative">
            <Avatar user={{ ...user, nom_affichage: name }} src={avatarPreview} size="xl" />
            <input ref={fileInput} type="file" accept="image/jpeg,image/png,image/webp" onChange={selectAvatar} className="sr-only" aria-label="Choisir une photo de profil" />
            <button type="button" onClick={() => fileInput.current?.click()} aria-label="Changer la photo de profil" className="absolute -bottom-1 -right-1 grid h-9 w-9 place-items-center rounded-full border-2 border-surface bg-brand-500 text-white">
              <ImageIcon size={17} />
            </button>
          </div>
          <p className="mt-3 text-sm text-muted">{user.telephone ?? user.email}</p>
        </div>
        <div className="mt-6 space-y-4">
          <label className="block text-sm font-bold">Nom d’affichage<input className="mt-2 h-12 w-full rounded-2xl border border-line bg-elevated px-4 text-base font-normal outline-none focus:border-brand-500" value={name} onChange={(event) => setName(event.target.value)} required /></label>
          <label className="block text-sm font-bold">Statut<input className="mt-2 h-12 w-full rounded-2xl border border-line bg-elevated px-4 text-base font-normal outline-none focus:border-brand-500" value={status} onChange={(event) => setStatus(event.target.value)} maxLength={80} /></label>
        </div>
      </section>
      <section className="rounded-[1.5rem] border border-line bg-surface p-5 shadow-soft">
        <h2 className="font-extrabold">Apparence</h2>
        <div className="mt-4 grid grid-cols-3 gap-2">
          {(["system", "light", "dark"] as ThemePreference[]).map((value) => (
            <button key={value} type="button" onClick={() => setTheme(value)} className={`rounded-2xl border px-3 py-3 text-sm font-bold ${theme === value ? "border-brand-500 bg-brand-50 text-brand-600" : "border-line text-muted"}`}>
              {value === "system" ? "Système" : value === "light" ? "Clair" : "Sombre"}
            </button>
          ))}
        </div>
      </section>
      {(update.isError || mediaUpload.isError) && <p role="alert" className="text-sm text-danger">{errorMessage(update.error ?? mediaUpload.error)}</p>}
      <button type="submit" disabled={pending || !authenticatedUser} className="h-12 w-full rounded-2xl bg-brand-500 font-bold text-white shadow-float disabled:opacity-50">
        {pending ? "Enregistrement…" : "Enregistrer les modifications"}
      </button>
    </form>
  );
}
