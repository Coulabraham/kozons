import type { ButtonHTMLAttributes, ReactNode } from "react";

export function IconButton({ label, children, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; children: ReactNode }) {
  return (
    <button type="button" aria-label={label} title={label} className={`grid h-10 w-10 shrink-0 place-items-center rounded-full text-muted transition duration-200 ease-calm hover:bg-brand-50 hover:text-brand-600 disabled:opacity-40 dark:hover:bg-elevated ${className}`} {...props}>
      {children}
    </button>
  );
}
