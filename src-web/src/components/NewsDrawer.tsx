"use client";

import { ExternalLink, X } from "lucide-react";

interface NewsItem {
  id: string;
  source: string;
  time: string;
  title: string;
  url: string;
}

interface NewsDrawerProps {
  onClose: () => void;
}

export default function NewsDrawer({ onClose }: NewsDrawerProps) {
  const newsItems: NewsItem[] = [
    {
      id: "1",
      source: "Hacker News",
      time: "12m",
      title: "Anthropic lanza nuevos modelos con capacidades agénticas avanzadas",
      url: "https://news.ycombinator.com",
    },
    {
      id: "2",
      source: "Ars Technica",
      time: "24m",
      title: "Linux Kernel 6.12 introduce mejoras clave de rendimiento para WebGPU",
      url: "https://arstechnica.com",
    },
    {
      id: "3",
      source: "The Verge",
      time: "45m",
      title: "Rust consolida su liderazgo en infraestructuras de escritorio livianas con Tauri v2",
      url: "https://theverge.com",
    },
    {
      id: "4",
      source: "GitHub Trending",
      time: "1h",
      title: "PixiJS v8 alcanza adopción masiva para simulaciones web interactivas",
      url: "https://github.com/trending",
    },
  ];

  return (
    <div className="flex flex-col h-full bg-[#000000] border-l border-[#27272a]">
      {/* Cabecera */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#27272a]">
        <span className="font-mono text-xs text-[#a1a1aa] uppercase tracking-wider">
          noticias · titulares rss
        </span>
        <button
          onClick={onClose}
          className="text-[#71717a] hover:text-[#ffffff] transition cursor-pointer p-1"
          title="Cerrar panel"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Lista tipográfica pura (sin tarjetas) */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {newsItems.map((item) => (
          <a
            key={item.id}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block group py-2 border-b border-[#18181b] hover:border-[#3f3f46] transition cursor-pointer"
          >
            <div className="flex items-center gap-2 font-mono text-[10px] text-[#71717a] mb-1">
              <span>{item.source}</span>
              <span>·</span>
              <span>{item.time}</span>
            </div>

            <h3 className="text-xs text-[#d4d4d8] group-hover:text-[#ffffff] transition leading-snug font-sans">
              {item.title}
            </h3>

            <div className="mt-1.5 flex items-center gap-1 text-[9px] font-mono text-[#52525b] group-hover:text-[#a1a1aa] transition">
              <span>LEER FUENTE ORIGINAL</span>
              <ExternalLink className="w-2.5 h-2.5" />
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
