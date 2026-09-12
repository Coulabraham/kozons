import type { User } from "@/lib/types";

const gradients = [
  "from-sky-400 to-blue-600",
  "from-violet-400 to-indigo-600",
  "from-emerald-400 to-teal-600",
  "from-amber-400 to-orange-600",
  "from-pink-400 to-rose-600",
];

export function Avatar({ user, name, src, size = "md", online = false }: { user?: User; name?: string; src?: string | null; size?: "sm" | "md" | "lg" | "xl"; online?: boolean }) {
  const label = name ?? user?.nom_affichage ?? "Kozons";
  const image = src ?? user?.avatar_url;
  const initials = label.split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase();
  const index = (user?.id ?? label.length) % gradients.length;
  const sizes = { sm: "h-9 w-9 text-xs", md: "h-12 w-12 text-sm", lg: "h-16 w-16 text-lg", xl: "h-24 w-24 text-2xl" };
  return (
    <span className={`relative inline-grid shrink-0 place-items-center overflow-visible rounded-full bg-gradient-to-br ${gradients[index]} ${sizes[size]} font-bold text-white`}>
      {image ? <img className="h-full w-full rounded-full object-cover" src={image} alt="" /> : initials}
      {online && <span className="absolute bottom-0 right-0 h-[25%] w-[25%] rounded-full border-2 border-surface bg-success" aria-label="En ligne" />}
    </span>
  );
}
