export function Brand({ compact = false, fullLogo = false }: { compact?: boolean; fullLogo?: boolean }) {
  if (fullLogo) {
    return (
      <div className="relative h-[154px] w-[215px] overflow-hidden" aria-label="Kozons">
        <img
          src="/branding/kozons-logo.jfif"
          alt="Logo Kozons"
          width={1536}
          height={1024}
          className="absolute -left-[107px] -top-[38px] h-auto w-[439px] max-w-none"
        />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3" aria-label="Kozons">
      <img
        src="/branding/kozons-app-icon.png"
        alt=""
        width={44}
        height={44}
        className="h-11 w-11 shrink-0 rounded-[15px] bg-white object-cover shadow-float"
      />
      {!compact && <span className="text-xl font-extrabold tracking-[-0.03em] text-ink">Kozons</span>}
    </div>
  );
}
