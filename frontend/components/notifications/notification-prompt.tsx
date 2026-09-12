"use client";

import { useEffect, useState } from "react";

import { CloseIcon } from "@/components/ui/icons";
import { usePushNotifications } from "@/lib/notifications/use-push-notifications";

export function NotificationPrompt() {
  const push = usePushNotifications();
  const [platform, setPlatform] = useState({ ready: false, ios: false, standalone: false });
  const [hidden, setHidden] = useState(() => typeof window !== "undefined" && window.localStorage.getItem("kozons-push-prompt") === "hidden");
  useEffect(() => {
    const navigatorWithStandalone = navigator as Navigator & { standalone?: boolean };
    const ios = /iPad|iPhone|iPod/.test(navigator.userAgent)
      || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    const standalone = Boolean(navigatorWithStandalone.standalone)
      || window.matchMedia("(display-mode: standalone)").matches;
    setPlatform({ ready: true, ios, standalone });
  }, []);
  if (hidden || !platform.ready) return null;
  const dismiss = () => { window.localStorage.setItem("kozons-push-prompt", "hidden"); setHidden(true); };
  if (platform.ios && !platform.standalone) {
    return (
      <div className="absolute left-1/2 top-20 z-20 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 rounded-2xl border border-line bg-surface p-4 shadow-soft" role="status">
        <div className="flex items-start justify-between gap-3"><div><strong className="text-sm">Installez Kozons sur votre iPhone</strong><p className="mt-1 text-xs text-muted">iOS autorise les notifications web uniquement depuis l’application ajoutée à l’écran d’accueil.</p></div><button type="button" aria-label="Plus tard" onClick={dismiss} className="p-1 text-muted"><CloseIcon size={17} /></button></div>
        <ol className="mt-4 grid grid-cols-2 gap-3 text-center text-xs font-semibold"><li className="rounded-xl bg-elevated p-3"><span className="mb-2 block text-2xl" aria-hidden="true">▣↑</span>1. Appuyez sur Partager</li><li className="rounded-xl bg-elevated p-3"><span className="mb-2 block text-2xl" aria-hidden="true">＋</span>2. Ajouter à l’écran d’accueil</li></ol>
        <p className="mt-3 text-xs text-muted">Ouvrez ensuite Kozons depuis son icône. Le bouton d’activation des notifications apparaîtra dans l’application installée.</p>
      </div>
    );
  }
  if (!process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || typeof Notification === "undefined" || Notification.permission !== "default") return null;
  return (
    <div className="absolute left-1/2 top-20 z-20 flex w-[calc(100%-2rem)] max-w-md -translate-x-1/2 items-start gap-3 rounded-2xl border border-line bg-surface p-4 shadow-soft" role="status">
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-lg">🔔</span><div className="min-w-0 flex-1"><strong className="text-sm">Restez au courant</strong><p className="mt-0.5 text-xs text-muted">Activez les notifications pour les nouveaux messages lorsque Kozons est fermé.</p><button type="button" onClick={() => push.mutate(undefined, { onSuccess: dismiss })} className="mt-2 text-sm font-bold text-brand-600 hover:underline">{push.isPending ? "Activation…" : "Activer les notifications"}</button>{push.isError && <p className="mt-1 text-xs text-danger">{push.error.message}</p>}</div><button type="button" aria-label="Plus tard" onClick={dismiss} className="p-1 text-muted"><CloseIcon size={17} /></button>
    </div>
  );
}
