"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";

interface AsciiOverlayProps {
  status: string;
}

export default function AsciiOverlay({ status }: AsciiOverlayProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const statusRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Animación de entrada GSAP con reveal tecnológico
    gsap.fromTo(
      containerRef.current,
      { opacity: 0, scale: 0.97, y: 15 },
      { opacity: 1, scale: 1, y: 0, duration: 0.8, ease: "power2.out" }
    );

    // Animación de pulso continuo en el status de telemetría
    if (statusRef.current) {
      gsap.to(statusRef.current, {
        opacity: 0.35,
        repeat: -1,
        yoyo: true,
        duration: 0.8,
        ease: "sine.inOut",
      });
    }
  }, [status]);

  return (
    <div
      ref={containerRef}
      className="flex flex-col items-center justify-center p-4 rounded-xl bg-[#161b22]/80 border border-amber-500/25 backdrop-blur-md shadow-[0_0_30px_rgba(245,158,11,0.06)]"
    >
      <div className="font-mono text-[11px] sm:text-[12px] text-amber-400 tracking-wider text-center select-none leading-tight drop-shadow-[0_0_8px_rgba(245,158,11,0.35)]">
        <p>╭─── [ H O L O G R A P H I C   N E U R A L   C O R E   2 . 5 D ] ─────────╮</p>
        <p>│  LAYER 0 [IN]    LAYER 1 [HID]   LAYER 2 [DENSE] LAYER 3 [ATTN]  OUTPUT│</p>
        <p>│  ────────────   ─────────────   ─────────────── ──────────────  ──────│</p>
        <p>│   [◈ 0.88] ━━►    [◉ 0.94] ━━►    [◈ 0.98] ━━►   [◉ 0.82] ━━►   [◈ 0.91]│</p>
        <p>│   [◉ 0.65] ───    [◈ 0.51] ───    [◉ 0.59] ───   [◈ 0.72] ───   [◉ 0.76]│</p>
        <p>│   [○ 0.32] ┄┄┄    [○ 0.24] ┄┄┄    [○ 0.29] ┄┄┄   [○ 0.38] ┄┄┄   [○ 0.40]│</p>
        <p>│  SPHERICAL TENSOR: [████████████░░░░░░░░░░]  PROJECTION: 2.5D MATRIX   │</p>
        <p>╰─────────────────────────────────────────────────────────────────────────╯</p>
      </div>

      <div className="mt-3 flex items-center gap-2 font-mono text-[10px] text-slate-400 tracking-widest uppercase">
        <span ref={statusRef} className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#10b981]" />
        <span className="text-amber-300">ESTADO: {status}</span>
        <span className="text-slate-600">|</span>
        <span className="text-emerald-400">FPS: 60 (WebGL)</span>
        <span className="text-slate-600">|</span>
        <span>MODO: TITANIO HUD</span>
      </div>
    </div>
  );
}
