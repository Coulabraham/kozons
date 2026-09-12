"use client";

import { useEffect, useMemo, useState } from "react";

import { PauseIcon, PlayIcon } from "@/components/ui/icons";
import { IconButton } from "@/components/ui/icon-button";

export function VoicePlayer({ duration = 0 }: { duration?: number | null }) {
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const bars = useMemo(() => Array.from({ length: 28 }, (_, index) => 7 + ((index * 13) % 22)), []);
  useEffect(() => {
    if (!playing || !duration) return;
    const timer = window.setInterval(() => setProgress((value) => {
      if (value >= 100) { setPlaying(false); return 0; }
      return Math.min(100, value + 100 / duration);
    }), 1000);
    return () => window.clearInterval(timer);
  }, [duration, playing]);
  const elapsed = Math.round((progress / 100) * (duration || 0));
  return <div className="flex min-w-[220px] items-center gap-2"><IconButton label={playing ? "Mettre en pause" : "Lire la note vocale"} className="bg-brand-500 text-white hover:bg-brand-600 hover:text-white" onClick={() => setPlaying((value) => !value)}>{playing ? <PauseIcon size={17} /> : <PlayIcon size={17} />}</IconButton><div className="min-w-0 flex-1"><button type="button" aria-label={`Progression ${elapsed} secondes sur ${duration}`} onClick={(event) => { const rect = event.currentTarget.getBoundingClientRect(); setProgress(((event.clientX - rect.left) / rect.width) * 100); }} className="flex h-9 w-full items-center gap-[2px]">{bars.map((height, index) => <span key={index} className={`w-[3px] rounded-full ${index / bars.length * 100 <= progress ? "bg-brand-600" : "bg-muted/35"}`} style={{ height }} />)}</button><span className="text-[11px] text-muted">0:{String(duration || 0).padStart(2, "0")}</span></div></div>;
}
