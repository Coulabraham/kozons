"use client";

import { useEffect, useState } from "react";

import { ArrowLeftIcon, ChevronRightIcon, CloseIcon } from "@/components/ui/icons";
import { IconButton } from "@/components/ui/icon-button";
import type { Message } from "@/lib/types";

export function MediaViewer({ media, initialId, onClose }: { media: Message[]; initialId: number; onClose: () => void }) {
  const initial = Math.max(0, media.findIndex((item) => item.id === initialId));
  const [index, setIndex] = useState(initial);
  const [zoom, setZoom] = useState(1);
  const current = media[index];
  useEffect(() => {
    const close = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, [onClose]);
  if (!current) return null;
  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-slate-950/95 text-white backdrop-blur" role="dialog" aria-modal="true" aria-label="Visionneuse de médias">
      <header className="flex h-16 items-center justify-between px-4"><span className="text-sm font-semibold">{index + 1} / {media.length}</span><div className="flex items-center gap-3"><label className="hidden items-center gap-2 text-xs sm:flex">Zoom<input aria-label="Niveau de zoom" type="range" min="1" max="2.5" step="0.1" value={zoom} onChange={(event) => setZoom(Number(event.target.value))} /></label><IconButton label="Fermer" className="text-white hover:bg-white/10 hover:text-white" onClick={onClose}><CloseIcon /></IconButton></div></header>
      <div className="relative flex flex-1 items-center justify-center overflow-hidden p-8">
        <button type="button" aria-label="Média précédent" disabled={index === 0} onClick={() => { setIndex((value) => value - 1); setZoom(1); }} className="absolute left-3 z-10 grid h-12 w-12 place-items-center rounded-full bg-white/10 disabled:opacity-20"><ArrowLeftIcon /></button>
        <div className="flex aspect-video w-full max-w-5xl items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-br from-brand-600 via-slate-800 to-cyan-950 transition-transform duration-200" style={{ transform: `scale(${zoom})` }}><span className="text-lg font-bold">{current.type === "video" ? "▶ Lecture vidéo" : current.contenu ?? "Photo partagée"}</span></div>
        <button type="button" aria-label="Média suivant" disabled={index === media.length - 1} onClick={() => { setIndex((value) => value + 1); setZoom(1); }} className="absolute right-3 z-10 grid h-12 w-12 place-items-center rounded-full bg-white/10 disabled:opacity-20"><ChevronRightIcon /></button>
      </div>
    </div>
  );
}
