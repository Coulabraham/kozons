"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";

import { AuthShell } from "@/components/auth/auth-shell";
import { Field } from "@/components/auth/field";
import { SubmitButton } from "@/components/auth/submit-button";
import { errorMessage } from "@/lib/api/error-message";
import { useResendOtp, useVerifyOtp } from "@/lib/api/hooks";
import { useAuthStore } from "@/store/auth-store";

export default function VerifyPage() {
  const router = useRouter();
  const verify = useVerifyOtp();
  const resendOtp = useResendOtp();
  const identifier = useAuthStore((state) => state.pendingIdentifier);
  const setPendingIdentifier = useAuthStore((state) => state.setPendingIdentifier);
  const localOtpCode = process.env.NEXT_PUBLIC_LOCAL_OTP_CODE;
  const [manualIdentifier, setManualIdentifier] = useState("");
  const [digits, setDigits] = useState(["", "", "", "", "", ""]);
  const [seconds, setSeconds] = useState(45);
  const [resent, setResent] = useState(false);
  const refs = useRef<Array<HTMLInputElement | null>>([]);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = window.setInterval(() => setSeconds((value) => value - 1), 1000);
    return () => window.clearInterval(timer);
  }, [seconds]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!identifier) return;
    verify.mutate({ identifier, code: digits.join("") }, { onSuccess: () => router.replace("/auth/login") });
  };

  const resend = () => {
    if (!identifier || seconds > 0) return;
    resendOtp.mutate(identifier, {
      onSuccess: () => {
        setSeconds(45);
        setResent(true);
      },
    });
  };

  const recover = (event: FormEvent) => {
    event.preventDefault();
    const value = manualIdentifier.trim();
    if (!value) return;
    resendOtp.mutate(value, {
      onSuccess: () => {
        setPendingIdentifier(value);
        setSeconds(45);
        setResent(true);
      },
    });
  };

  return (
    <AuthShell
      title="Vérifiez votre compte"
      subtitle={identifier ? `Saisissez le code à 6 chiffres envoyé à ${identifier}.` : "Indiquez l’identifiant du compte à vérifier."}
    >
      {!identifier && (
        <form className="space-y-5" onSubmit={recover}>
          <Field
            name="identifier"
            label="Téléphone ou email"
            autoComplete="username"
            placeholder="vous@exemple.com ou +221 77 000 00 00"
            value={manualIdentifier}
            onChange={(event) => setManualIdentifier(event.target.value)}
            required
          />
          {resendOtp.isError && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-danger dark:bg-red-950/20">{errorMessage(resendOtp.error)}</p>}
          <SubmitButton pending={resendOtp.isPending}>Recevoir un nouveau code</SubmitButton>
        </form>
      )}
      {identifier && localOtpCode && (
        <div className="mb-5 rounded-2xl border border-brand-200 bg-brand-50 p-4 text-sm text-ink dark:border-brand-800 dark:bg-brand-950/30" role="status">
          <p><strong>Mode local :</strong> aucun e-mail ou SMS réel n’est envoyé.</p>
          <button
            type="button"
            disabled={resendOtp.isPending}
            className="mt-2 font-extrabold text-brand-600 hover:underline disabled:opacity-55"
            onClick={() => {
              if (resent) {
                setDigits(localOtpCode.slice(0, 6).split(""));
                return;
              }
              resendOtp.mutate(identifier, {
                onSuccess: () => {
                  setDigits(localOtpCode.slice(0, 6).split(""));
                  setSeconds(45);
                  setResent(true);
                },
              });
            }}
          >
            {resent ? "Utiliser" : "Générer et utiliser"} le code {localOtpCode}
          </button>
        </div>
      )}
      {identifier && <form onSubmit={submit}>
        <fieldset><legend className="sr-only">Code de vérification</legend><div className="grid grid-cols-6 gap-2">
          {digits.map((digit, index) => <input key={index} ref={(element) => { refs.current[index] = element; }} aria-label={`Chiffre ${index + 1}`} inputMode="numeric" autoComplete={index === 0 ? "one-time-code" : "off"} maxLength={1} value={digit} onChange={(event) => { const value = event.target.value.replace(/\D/g, "").slice(-1); setDigits((current) => current.map((item, itemIndex) => itemIndex === index ? value : item)); if (value) refs.current[index + 1]?.focus(); }} onKeyDown={(event) => { if (event.key === "Backspace" && !digit) refs.current[index - 1]?.focus(); }} className="h-14 min-w-0 rounded-2xl border border-line bg-elevated text-center text-xl font-extrabold text-ink focus:border-brand-500" />)}
        </div></fieldset>
        {verify.isError && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-danger dark:bg-red-950/20">{errorMessage(verify.error)}</p>}
        <div className="mt-6"><SubmitButton pending={verify.isPending} disabled={digits.some((digit) => !digit) || !identifier}>Vérifier</SubmitButton></div>
      </form>}
      {identifier && <div className="mt-5 text-center text-sm text-muted">{seconds > 0 ? `Renvoyer le code dans 0:${String(seconds).padStart(2, "0")}` : <button type="button" onClick={resend} disabled={resendOtp.isPending} className="font-bold text-brand-600 hover:underline disabled:opacity-55">Renvoyer le code</button>}{resent && <span className="ml-2 text-success">Code renvoyé</span>}{resendOtp.isError && <span role="alert" className="mt-2 block text-danger">{errorMessage(resendOtp.error)}</span>}</div>}
    </AuthShell>
  );
}
