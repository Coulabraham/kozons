import type { InputHTMLAttributes } from "react";

export function Field({ label, hint, error, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string; hint?: string; error?: string }) {
  const id = props.id ?? props.name;
  return (
    <label className="block" htmlFor={id}>
      <span className="mb-2 block text-sm font-semibold text-ink">{label}</span>
      <input id={id} className="h-12 w-full rounded-2xl border border-line bg-elevated px-4 text-base text-ink outline-none transition focus:border-brand-500 focus:ring-4 focus:ring-brand-100 disabled:opacity-60" aria-invalid={Boolean(error)} {...props} />
      {(error || hint) && <span className={`mt-1.5 block text-xs ${error ? "text-danger" : "text-muted"}`}>{error ?? hint}</span>}
    </label>
  );
}
