"use client";

interface BottomDockProps {
  activeMode: string;
  onSelectMode: (modeId: string) => void;
  onOpenChat: () => void;
  onOpenNews: () => void;
  activeSideTab: "chat" | "news" | null;
  onCloseApp: () => void;
}

export default function BottomDock({
  activeMode,
  onSelectMode,
  onOpenChat,
  onOpenNews,
  activeSideTab,
  onCloseApp,
}: BottomDockProps) {
  const modes = [
    { id: "gaming", label: "[1] GAMING" },
    { id: "trabajo", label: "[2] TRABAJO" },
    { id: "estudio", label: "[3] ESTUDIO" },
  ];

  return (
    <footer className="w-full flex items-center justify-between px-6 py-3 border-t border-[#18181b] bg-[#000000] text-xs font-mono select-none">
      {/* Selector de Modos en texto plano clickeable */}
      <div className="flex items-center gap-4">
        <span className="text-[#52525b]">MODOS:</span>
        {modes.map((m) => {
          const isSelected = activeMode === m.id;
          return (
            <button
              key={m.id}
              onClick={() => onSelectMode(m.id)}
              className={`transition cursor-pointer px-1 py-0.5 ${
                isSelected
                  ? "text-[#ffffff] border-b border-[#ffffff] font-semibold"
                  : "text-[#71717a] hover:text-[#d4d4d8]"
              }`}
            >
              {m.label}
            </button>
          );
        })}
      </div>

      {/* Acciones y Paneles directos por clic */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenChat}
          className={`transition cursor-pointer px-2 py-1 rounded border ${
            activeSideTab === "chat"
              ? "border-[#ffffff] text-[#ffffff] bg-[#18181b]"
              : "border-[#27272a] text-[#71717a] hover:text-[#ffffff] hover:border-[#3f3f46]"
          }`}
        >
          [ASISTENTE]
        </button>

        <button
          onClick={onOpenNews}
          className={`transition cursor-pointer px-2 py-1 rounded border ${
            activeSideTab === "news"
              ? "border-[#ffffff] text-[#ffffff] bg-[#18181b]"
              : "border-[#27272a] text-[#71717a] hover:text-[#ffffff] hover:border-[#3f3f46]"
          }`}
        >
          [NOTICIAS]
        </button>

        <button
          onClick={onCloseApp}
          className="text-[#71717a] hover:text-[#ffffff] px-2 py-1 border border-[#27272a] hover:border-[#3f3f46] rounded transition cursor-pointer"
          title="Ocultar a la bandeja"
        >
          [✕ SALIR]
        </button>
      </div>
    </footer>
  );
}
