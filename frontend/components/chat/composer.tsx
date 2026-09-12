"use client";

import { ChangeEvent, FormEvent, PointerEvent, useRef, useState } from "react";

import { ImageIcon, MicIcon, PaperclipIcon, SendIcon, SmileIcon, VideoIcon } from "@/components/ui/icons";
import { IconButton } from "@/components/ui/icon-button";

export function Composer({ disabled, uploading, onSendText, onTyping, onAttachment, onVoice }: { disabled?: boolean; uploading?: boolean; onSendText: (text: string) => void; onTyping: (typing: boolean) => void; onAttachment: (file: File, type: "image" | "video") => void; onVoice: (file: File, duration: number) => void }) {
  const [text, setText] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [recording, setRecording] = useState(false);
  const [canceling, setCanceling] = useState(false);
  const typingTimer = useRef<number | null>(null);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const recordStarted = useRef(0);
  const pointerStart = useRef(0);
  const canceled = useRef(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const selectedType = useRef<"image" | "video">("image");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const value = text.trim();
    if (!value) return;
    onSendText(value);
    onTyping(false);
    setText("");
  };
  const changeText = (event: ChangeEvent<HTMLInputElement>) => {
    setText(event.target.value);
    onTyping(true);
    if (typingTimer.current) window.clearTimeout(typingTimer.current);
    typingTimer.current = window.setTimeout(() => onTyping(false), 1200);
  };
  const chooseFile = (type: "image" | "video") => {
    selectedType.current = type;
    if (fileInput.current) fileInput.current.accept = type === "image" ? "image/*" : "video/*";
    fileInput.current?.click();
    setMenuOpen(false);
  };
  const startRecording = async (event: PointerEvent<HTMLButtonElement>) => {
    if (!navigator.mediaDevices?.getUserMedia) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    pointerStart.current = event.clientX;
    canceled.current = false;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const instance = new MediaRecorder(stream);
    recorder.current = instance;
    chunks.current = [];
    recordStarted.current = Date.now();
    instance.ondataavailable = (data) => data.data.size && chunks.current.push(data.data);
    instance.onstop = () => {
      stream.getTracks().forEach((track) => track.stop());
      if (!canceled.current && chunks.current.length) {
        const blob = new Blob(chunks.current, { type: instance.mimeType || "audio/webm" });
        onVoice(new File([blob], `voice-${Date.now()}.webm`, { type: blob.type }), Math.max(1, Math.round((Date.now() - recordStarted.current) / 1000)));
      }
      setRecording(false);
      setCanceling(false);
    };
    instance.start();
    setRecording(true);
  };
  const moveRecording = (event: PointerEvent<HTMLButtonElement>) => {
    if (!recording) return;
    const shouldCancel = pointerStart.current - event.clientX > 80;
    canceled.current = shouldCancel;
    setCanceling(shouldCancel);
  };
  const stopRecording = () => recorder.current?.state === "recording" && recorder.current.stop();

  return (
    <div className="safe-bottom relative shrink-0 border-t border-line bg-surface px-2 pt-2 sm:px-4">
      {recording && <div className={`absolute inset-x-4 -top-12 rounded-2xl px-4 py-2 text-center text-sm font-semibold shadow-soft ${canceling ? "bg-red-50 text-danger dark:bg-red-950" : "bg-surface text-muted"}`}><span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-danger" />{canceling ? "Relâchez pour annuler" : "Glissez vers la gauche pour annuler"}</div>}
      {menuOpen && <div className="absolute bottom-[5.5rem] left-3 z-10 w-48 rounded-2xl border border-line bg-surface p-2 shadow-soft"><button type="button" onClick={() => chooseFile("image")} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold hover:bg-brand-50"><ImageIcon className="text-brand-500" /> Photo</button><button type="button" onClick={() => chooseFile("video")} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold hover:bg-brand-50"><VideoIcon className="text-brand-500" /> Vidéo</button></div>}
      <input ref={fileInput} type="file" className="sr-only" onChange={(event) => { const file = event.target.files?.[0]; if (file) onAttachment(file, selectedType.current); event.target.value = ""; }} />
      <form className="flex items-center gap-1.5" onSubmit={submit}>
        <IconButton label="Joindre un fichier" onClick={() => setMenuOpen((value) => !value)} disabled={disabled || uploading}><PaperclipIcon /></IconButton>
        <label className="flex min-h-11 min-w-0 flex-1 items-center gap-1 rounded-2xl bg-elevated px-3"><span className="sr-only">Écrire un message</span><input value={text} onChange={changeText} disabled={disabled} className="min-w-0 flex-1 bg-transparent py-2 text-[0.95rem] text-ink outline-none placeholder:text-muted" placeholder={uploading ? "Traitement du média…" : "Écrire un message"} /><button type="button" aria-label="Ajouter un emoji" onClick={() => setText((value) => `${value}🙂`)} className="p-1 text-muted hover:text-brand-600"><SmileIcon /></button></label>
        {text.trim() ? <IconButton label="Envoyer le message" className="bg-brand-500 text-white hover:bg-brand-600 hover:text-white" disabled={disabled}><SendIcon size={18} /></IconButton> : <button type="button" aria-label="Maintenir pour enregistrer une note vocale" title="Maintenir pour enregistrer, glisser pour annuler" onPointerDown={startRecording} onPointerMove={moveRecording} onPointerUp={stopRecording} onPointerCancel={() => { canceled.current = true; stopRecording(); }} disabled={disabled || uploading} className={`grid h-11 w-11 shrink-0 touch-none place-items-center rounded-full transition ${recording ? canceling ? "translate-x-[-4rem] bg-danger text-white" : "scale-110 bg-danger text-white" : "bg-brand-500 text-white hover:bg-brand-600"}`}><MicIcon /></button>}
      </form>
    </div>
  );
}
