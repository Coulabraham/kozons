"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { AuthShell } from "@/components/auth/auth-shell";
import { Field } from "@/components/auth/field";
import { SubmitButton } from "@/components/auth/submit-button";
import { errorMessage } from "@/lib/api/error-message";
import { useLogin } from "@/lib/api/hooks";
import { useAuthStore } from "@/store/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const login = useLogin();
  const accessToken = useAuthStore((state) => state.accessToken);
  const sessionChecked = useAuthStore((state) => state.sessionChecked);
  const setPendingIdentifier = useAuthStore((state) => state.setPendingIdentifier);
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (sessionChecked && accessToken) router.replace("/chat");
  }, [accessToken, router, sessionChecked]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    login.mutate({ identifier, password }, { onSuccess: () => router.replace("/chat") });
  };

  return (
    <AuthShell title="Bon retour" subtitle="Retrouvez vos conversations là où vous les avez laissées.">
      <form className="space-y-5" onSubmit={submit}>
        <Field name="identifier" label="Téléphone ou email" autoComplete="username" placeholder="+221 77 000 00 00" value={identifier} onChange={(event) => setIdentifier(event.target.value)} required />
        <Field name="password" label="Mot de passe" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        {login.isError && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-danger dark:bg-red-950/20">{errorMessage(login.error)}</p>}
        <SubmitButton pending={login.isPending}>Se connecter</SubmitButton>
      </form>
      <p className="mt-4 text-center text-sm">
        <Link
          className="font-bold text-brand-600 hover:underline"
          href="/auth/verify"
          onClick={() => setPendingIdentifier(identifier.trim() || null)}
        >
          Compte non vérifié ? Recevoir un nouveau code
        </Link>
      </p>
      <p className="mt-6 text-center text-sm text-muted">Nouveau sur Kozons ? <Link className="font-bold text-brand-600 hover:underline" href="/auth/register">Créer un compte</Link></p>
    </AuthShell>
  );
}
