"use client";

import { useState } from "react";
import NeuralCanvas from "@/components/NeuralCanvas";
import ChatPanel from "@/components/ChatPanel";
import NewsDrawer from "@/components/NewsDrawer";
import BottomDock from "@/components/BottomDock";
import JarvisLogo from "@/components/JarvisLogo";

export default function Home() {
  const [activeSideTab, setActiveSideTab] = useState<"chat" | "news" | null>("chat");
  const [activeMode, setActiveMode] = useState("trabajo");
  const [isThinking, setIsThinking] = useState(false);
  const [isGlitching, setIsGlitching] = useState(false);
  const [chatWidth, setChatWidth] = useState(420);

  const handleModeSelect = (modeId: string) => {
    if (modeId !== activeMode) {
      setActiveMode(modeId);
      setIsGlitching(true);
      setTimeout(() => setIsGlitching(false), 400);

      // Lanzar aplicaciones asociadas al modo en el sistema operativo
      import("@/lib/system").then(({ triggerSystemMode }) => {
        triggerSystemMode(modeId);
      });
    }
  };

  // Lógica para redimensionar el panel de chat arrastrando con el mouse
  const handleMouseDownResize = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = chatWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      // El panel está a la derecha, por lo que arrastrar a la izquierda agranda el panel
      const deltaX = startX - moveEvent.clientX;
      const newWidth = Math.max(300, Math.min(850, startWidth + deltaX));
      setChatWidth(newWidth);
    };

    const onMouseUp = () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      document.body.style.cursor = "default";
      document.body.style.userSelect = "auto";
    };

    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  };

  const toggleTab = (tab: "chat" | "news") => {
    if (document.startViewTransition) {
      document.startViewTransition(() => {
        setActiveSideTab((prev) => (prev === tab ? null : tab));
      });
    } else {
      setActiveSideTab((prev) => (prev === tab ? null : tab));
    }
  };

  const handleClose = () => {
    // Si estamos en Tauri se invoca el hide a la bandeja
    if (typeof window !== "undefined" && (window as any).__TAURI__) {
      (window as any).__TAURI__.window.getCurrentWindow().hide();
    }
  };

  return (
    <main className="relative flex h-screen w-screen overflow-hidden bg-[#000000] text-[#f4f4f5] font-sans select-none">
      {/* Zero-Header: Sin barra superior. Lienzo Central y Foco Total */}
      <div className="relative z-10 flex flex-1 flex-col h-full min-w-0">
        {/* Logo J.A.R.V.I.S. con SVG en esquina superior derecha del área principal */}
        <div className="absolute top-5 right-6 z-30 pointer-events-none">
          <JarvisLogo isThinking={isThinking} />
        </div>

        {/* Área Central: Red Neuronal Vectorial de 1px */}
        <div className="flex-1 flex flex-col items-center justify-center relative">
          {/* Canvas Vectorial de Precisión Matemática */}
          <div className="absolute inset-0 z-0">
            <NeuralCanvas isThinking={isThinking} />
          </div>

          {/* Estado sobrio central sin decoración de relleno con efecto glitch */}
          <div className="relative z-10 text-center pointer-events-none space-y-1">
            <div className="font-mono text-xs text-[#71717a] tracking-widest uppercase flex items-center justify-center gap-1.5">
              <span>modo activo:</span>
              <span
                className={`text-[#f4f4f5] font-semibold transition-colors duration-150 ${
                  isGlitching ? "glitch-active text-[#ffffff]" : ""
                }`}
              >
                {activeMode}
              </span>
            </div>
            <h1 className="text-xl font-light text-[#f4f4f5] tracking-tight">
              Brandon Carranza
            </h1>
          </div>
        </div>

        {/* Dock Inferior de Texto Plano 100% Clickeable */}
        <BottomDock
          activeMode={activeMode}
          onSelectMode={handleModeSelect}
          onOpenChat={() => toggleTab("chat")}
          onOpenNews={() => toggleTab("news")}
          activeSideTab={activeSideTab}
          onCloseApp={handleClose}
        />
      </div>

      {/* Dock Lateral Deslizable (Chat / Noticias) con Ancho Ajustable y Manija */}
      {activeSideTab && (
        <aside
          style={{ width: `${chatWidth}px` }}
          className="relative z-20 h-full flex-shrink-0 flex transition-all duration-75"
        >
          {/* Indicador de Arrastre / Resize Handle */}
          <div
            onMouseDown={handleMouseDownResize}
            className="group absolute -left-1.5 top-0 bottom-0 w-3 cursor-col-resize z-30 flex items-center justify-center hover:bg-white/5 transition-colors"
            title="Arrastra para redimensionar el panel"
          >
            {/* Barra táctil minimalista con puntos de agarre */}
            <div className="w-[2px] h-12 bg-[#27272a] group-hover:bg-[#f4f4f5] rounded-full transition-colors flex flex-col justify-between py-1 items-center">
              <div className="w-1 h-1 bg-[#71717a] group-hover:bg-[#ffffff] rounded-full" />
              <div className="w-1 h-1 bg-[#71717a] group-hover:bg-[#ffffff] rounded-full" />
              <div className="w-1 h-1 bg-[#71717a] group-hover:bg-[#ffffff] rounded-full" />
            </div>
          </div>

          <div className="w-full h-full flex-1">
            {activeSideTab === "chat" && (
              <ChatPanel
                onClose={() => setActiveSideTab(null)}
                isThinking={isThinking}
                setIsThinking={setIsThinking}
              />
            )}
            {activeSideTab === "news" && (
              <NewsDrawer onClose={() => setActiveSideTab(null)} />
            )}
          </div>
        </aside>
      )}
    </main>
  );
}
