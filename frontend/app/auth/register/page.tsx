"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AuthShell } from "@/components/auth/auth-shell";
import { Field } from "@/components/auth/field";
import { SubmitButton } from "@/components/auth/submit-button";
import { errorMessage } from "@/lib/api/error-message";
import { useRegister } from "@/lib/api/hooks";

export default function RegisterPage() {
  const router = useRouter();
  const register = useRegister();
  const [method, setMethod] = useState<"telephone" | "email">("telephone");
  const [identifier, setIdentifier] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    register.mutate(
      { [method]: identifier, password, nom_affichage: name },
      { onSuccess: () => router.push("/auth/verify") },
    );
  };

  return (
    <AuthShell title="Créer votre compte" subtitle="Un numéro ou une adresse email suffit pour commencer.">
      <div className="mb-6 grid grid-cols-2 rounded-2xl bg-elevated p-1" role="tablist" aria-label="Méthode d’inscription">
        {(["telephone", "email"] as const).map((item) => <button key={item} type="button" role="tab" aria-selected={method === item} onClick={() => { setMethod(item); setIdentifier(""); }} className={`rounded-xl px-3 py-2.5 text-sm font-bold transition ${method === item ? "bg-surface text-brand-600 shadow-sm" : "text-muted"}`}>{item === "telephone" ? "Téléphone" : "Email"}</button>)}
      </div>
      <form className="space-y-5" onSubmit={submit}>
        <Field name="name" label="Nom d’affichage" autoComplete="name" placeholder="Votre nom" value={name} onChange={(event) => setName(event.target.value)} required />
        <Field name="identifier" label={method === "telephone" ? "Numéro de téléphone" : "Adresse email"} type={method === "email" ? "email" : "tel"} autoComplete={method === "email" ? "email" : "tel"} placeholder={method === "email" ? "amina@exemple.com" : "+221 77 000 00 00"} value={identifier} onChange={(event) => setIdentifier(event.target.value)} required />
        <Field name="password" label="Mot de passe" hint="10 caractères minimum" type="password" autoComplete="new-password" minLength={10} value={password} onChange={(event) => setPassword(event.target.value)} required />
        {register.isError && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-danger dark:bg-red-950/20">{errorMessage(register.error)}</p>}
        <SubmitButton pending={register.isPending}>Continuer</SubmitButton>
      </form>
      <p className="mt-6 text-center text-sm text-muted">Déjà inscrit ? <Link className="font-bold text-brand-600 hover:underline" href="/auth/login">Se connecter</Link></p>
    </AuthShell>
  );
}
