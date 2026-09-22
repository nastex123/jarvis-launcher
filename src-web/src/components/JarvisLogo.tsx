"use client";

import React from "react";

interface JarvisLogoProps {
  className?: string;
  isThinking?: boolean;
}

export default function JarvisLogo({ className = "", isThinking = false }: JarvisLogoProps) {
  return (
    <div
      className={`flex items-center gap-3 select-none pointer-events-auto transition-opacity duration-300 ${className}`}
    >
      {/* Insignia / Reactor Arc SVG Estilizado Minimalista */}
      <div className="relative w-8 h-8 flex items-center justify-center">
        <svg
          viewBox="0 0 100 100"
          className={`w-full h-full ${isThinking ? "animate-spin duration-3000" : ""}`}
          style={{ animationDuration: isThinking ? "4s" : "0s" }}
        >
          {/* Anillo exterior segmentado */}
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke="#27272a"
            strokeWidth="2"
          />
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke={isThinking ? "#f4f4f5" : "#71717a"}
            strokeWidth="2.5"
            strokeDasharray="25 15"
            className="transition-colors duration-300"
          />

          {/* Anillo concéntrico interior */}
          <circle
            cx="50"
            cy="50"
            r="32"
            fill="none"
            stroke="#18181b"
            strokeWidth="3"
          />
          <circle
            cx="50"
            cy="50"
            r="32"
            fill="none"
            stroke={isThinking ? "#ffffff" : "#52525b"}
            strokeWidth="1.5"
            strokeDasharray="10 12"
            className="transition-colors duration-300"
          />

          {/* 3 Radiadores triangulares / Rayos de reactor */}
          <path
            d="M 50 18 L 50 26 M 22.3 66 L 29.2 62 M 77.7 66 L 70.8 62"
            stroke={isThinking ? "#f4f4f5" : "#71717a"}
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          {/* Núcleo central del reactor */}
          <circle
            cx="50"
            cy="50"
            r="12"
            fill="none"
            stroke={isThinking ? "#ffffff" : "#a1a1aa"}
            strokeWidth="2"
          />
          <circle
            cx="50"
            cy="50"
            r="5"
            fill={isThinking ? "#ffffff" : "#71717a"}
            className="transition-colors duration-300"
          />
        </svg>
      </div>

      {/* Tipografía Monospaced Técnica 'J.A.R.V.I.S.' + Badge Telemetría */}
      <div className="flex flex-col">
        <div className="flex items-center gap-1.5">
          <span className="font-mono text-sm font-bold tracking-[0.25em] text-[#f4f4f5]">
            J.A.R.V.I.S.
          </span>
          <span className="font-mono text-[9px] px-1 py-0.2 bg-[#18181b] border border-[#27272a] text-[#71717a] rounded tracking-wider">
            v2.5
          </span>
        </div>
        <span className="font-mono text-[9px] text-[#52525b] tracking-widest uppercase">
          {isThinking ? "PROCESANDO TENSORES" : "NÚCLEO NEURONAL"}
        </span>
      </div>
    </div>
  );
}
