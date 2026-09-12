import type { ButtonHTMLAttributes } from "react";

export function SubmitButton({ children, pending = false, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { pending?: boolean }) {
  return <button type="submit" disabled={pending || props.disabled} className="flex h-12 w-full items-center justify-center rounded-2xl bg-brand-500 px-5 font-bold text-white shadow-float transition duration-200 ease-calm hover:bg-brand-600 active:scale-[.99] disabled:cursor-not-allowed disabled:opacity-55" {...props}>{pending ? "Veuillez patienter…" : children}</button>;
}
