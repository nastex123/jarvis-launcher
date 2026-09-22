"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Copy, Check, X, History, Plus, Globe, Trash2, Terminal, AlertTriangle, ShieldCheck, Cpu } from "lucide-react";
import { searchWeb } from "@/lib/search";
import { executeSystemCommand, runOpenCodeAgent, isDangerousCommand } from "@/lib/system";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  isWebSearch?: boolean;
}

interface Conversation {
  id: string;
  title: string;
  timestamp: string;
  messages: Message[];
}

interface ChatPanelProps {
  onClose: () => void;
  isThinking: boolean;
  setIsThinking: (val: boolean) => void;
}

const STORAGE_KEY = "jarvis_chat_sessions_v1";

// Función global determinista para eliminar emojis de cualquier string
function stripEmojis(text: string): string {
  if (!text) return "";
  return text.replace(
    /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F1E6}-\u{1F1FF}]/gu,
    ""
  );
}

export default function ChatPanel({ onClose, isThinking, setIsThinking }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [thinkingSeconds, setThinkingSeconds] = useState(0);
  const [showHistory, setShowHistory] = useState(false);
  const [enableWebSearch, setEnableWebSearch] = useState(true);

  // Motor de IA: 'ollama' (qwen2.5) o 'opencode' (agente terminal autónomo)
  const [engineMode, setEngineMode] = useState<"ollama" | "opencode">("ollama");

  // Estado para confirmación destructiva interactiva
  const [pendingDanger, setPendingDanger] = useState<{
    cmd: string;
    description: string;
    resolve: (approved: boolean) => void;
  } | null>(null);

  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll instantáneo al fondo sin animación suave
  const scrollToBottomInstant = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  // Inicializar sesiones desde localStorage
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) return JSON.parse(saved);
      } catch (e) {
        console.warn("Error leyendo historial de chat:", e);
      }
    }
    return [
      {
        id: "default-1",
        title: "Sesión Principal",
        timestamp: "Hoy",
        messages: [
          {
            id: "1",
            role: "assistant",
            content:
              "Sistema listo. Inferencia local activa con `qwen2.5-coder:7b` y búsqueda web en tiempo real disponible.",
            timestamp: "10:30",
          },
        ],
      },
    ];
  });

  const [activeConvId, setActiveConvId] = useState<string>(() => conversations[0]?.id || "default-1");

  const currentConv = conversations.find((c) => c.id === activeConvId) || conversations[0];
  const messages = currentConv?.messages || [];

  // Autoscroll instantáneo al cambiar mensajes, al enviar o durante inferencia
  useEffect(() => {
    scrollToBottomInstant();
  }, [messages, isThinking, activeConvId]);

  // Guardar en localStorage ante cualquier cambio
  useEffect(() => {
    if (typeof window !== "undefined" && conversations.length > 0) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
      } catch (e) {
        console.warn("Error guardando historial:", e);
      }
    }
  }, [conversations]);

  const createNewSession = () => {
    const newId = Date.now().toString();
    const newConv: Conversation = {
      id: newId,
      title: `Consulta #${conversations.length + 1}`,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      messages: [
        {
          id: Date.now().toString(),
          role: "assistant",
          content: "Nueva sesión iniciada. Ingresa tu directiva o consulta técnica.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ],
    };
    setConversations((prev) => [newConv, ...prev]);
    setActiveConvId(newId);
    setShowHistory(false);
  };

  const deleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (conversations.length <= 1) return;
    const filtered = conversations.filter((c) => c.id !== id);
    setConversations(filtered);
    if (activeConvId === id) {
      setActiveConvId(filtered[0]?.id || "");
    }
  };

  const updateCurrentMessages = (updater: (prev: Message[]) => Message[]) => {
    setConversations((prev) =>
      prev.map((conv) => {
        if (conv.id === activeConvId) {
          const newMsgs = updater(conv.messages);
          // Si el título es el genérico y hay mensaje del usuario, actualizar título
          let newTitle = conv.title;
          const firstUserMsg = newMsgs.find((m) => m.role === "user");
          if (firstUserMsg && conv.title.startsWith("Consulta #")) {
            newTitle = firstUserMsg.content.slice(0, 26) + (firstUserMsg.content.length > 26 ? "..." : "");
          }
          return { ...conv, messages: newMsgs, title: newTitle };
        }
        return conv;
      })
    );
  };

  const copyTable = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSend = async (textToSend?: string) => {
    const text = (textToSend ?? input).trim();
    if (!text || isThinking) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    updateCurrentMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsThinking(true);
    setThinkingSeconds(0);

    const timer = setInterval(() => {
      setThinkingSeconds((s) => Number((s + 0.1).toFixed(1)));
    }, 100);

    const botMsgId = (Date.now() + 1).toString();
    const botTimestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Mensaje inicial del bot
    updateCurrentMessages((prev) => [
      ...prev,
      {
        id: botMsgId,
        role: "assistant",
        content: "",
        timestamp: botTimestamp,
      },
    ]);

    // 1. Manejo con OpenCode autónomo si el motor activo es OpenCode
    if (engineMode === "opencode") {
      try {
        const strictPrompt = `${text}\n(Nota estricta: No uses emojis bajo ninguna circunstancia)`;
        const rawOutput = await runOpenCodeAgent(strictPrompt);
        
        // Separar metadatos técnicos / telemetría de consola (ANSI codes, logs de búsqueda web)
        const ansiRegex = /\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])/g;
        const cleanRaw = stripEmojis(rawOutput.replace(ansiRegex, "").replace(/\[\d+m/g, ""));

        // Detectar líneas de telemetría de búsqueda web o logs de ejecución
        const lines = cleanRaw.split("\n");
        const telemetryLines: string[] = [];
        const contentLines: string[] = [];

        for (const line of lines) {
          const trimmed = line.trim();
          if (
            trimmed.startsWith("Web Search") ||
            trimmed.startsWith("Parallel Web Search") ||
            trimmed.startsWith("build ·") ||
            trimmed.startsWith("[0m") ||
            trimmed.includes("Web Search \"") ||
            trimmed.includes("behavior biology") ||
            trimmed.startsWith("Searching ")
          ) {
            telemetryLines.push(trimmed);
          } else {
            contentLines.push(line);
          }
        }

        let mainContent = contentLines.join("\n").trim();
        const telemetryContent = telemetryLines.join("\n").trim();

        // Formatear viñetas si están aglomeradas sin salto
        mainContent = mainContent.replace(/\n([A-Z0-9][^—\n]+)—/g, "\n\n- **$1**: ");

        let formattedMsg = mainContent || "Directiva completada.";
        if (telemetryContent) {
          formattedMsg += `\n\n<details><summary className="cursor-pointer text-[#71717a] hover:text-[#f4f4f5] text-[11px] font-mono">[+] Telemetría y registros de ejecución</summary>\n\n\`\`\`text\n${telemetryContent}\n\`\`\`\n</details>`;
        }

        formattedMsg = stripEmojis(formattedMsg);

        updateCurrentMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgId
              ? {
                  ...msg,
                  content: formattedMsg,
                }
              : msg
          )
        );
      } catch (err) {
        updateCurrentMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgId
              ? { ...msg, content: `Error ejecutando directiva en OpenCode: ${(err as Error).message}` }
              : msg
          )
        );
      } finally {
        clearInterval(timer);
        setIsThinking(false);
      }
      return;
    }

    // 2. Detección directa de comando de terminal / apertura de aplicaciones
    const lower = text.toLowerCase();
    const isTerminalCmd =
      lower.startsWith("ejecuta:") ||
      lower.startsWith("terminal:") ||
      lower.startsWith("run:") ||
      lower.startsWith("bash:") ||
      lower.startsWith("cmd:");

    const isOpenAppCmd = lower.startsWith("abre ") || lower.startsWith("abrir ") || lower.startsWith("lanzar ");

    if (isTerminalCmd || isOpenAppCmd) {
      let rawCmd = "";
      if (isTerminalCmd) {
        rawCmd = text.replace(/^(ejecuta|terminal|run|bash|cmd)\s*:?/i, "").trim();
      } else {
        const appName = text.replace(/^(abre|abrir|lanzar)\s+/i, "").trim();
        rawCmd = `${appName.toLowerCase()} &`;
      }

      // Comprobar política de seguridad y confirmación destructiva
      if (isDangerousCommand(rawCmd)) {
        setIsThinking(false);
        clearInterval(timer);

        const approved = await new Promise<boolean>((resolve) => {
          setPendingDanger({
            cmd: rawCmd,
            description: `Se detectó una instrucción que altera o elimina recursos del sistema: \`${rawCmd}\``,
            resolve: (val) => {
              setPendingDanger(null);
              resolve(val);
            },
          });
        });

        if (!approved) {
          updateCurrentMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMsgId
                ? {
                    ...msg,
                    content: `[CANCELADO] **Acción destructiva cancelada**: El comando \`${rawCmd}\` no fue autorizado por el usuario.`,
                  }
                : msg
            )
          );
          return;
        }

        setIsThinking(true);
      }

      // Ejecutar comando a través del puente de sistema (Tauri o Bridge)
      const result = await executeSystemCommand(rawCmd);
      clearInterval(timer);
      setIsThinking(false);

      let terminalReport = `**Control de Sistema**: \`${rawCmd}\`\n\n`;
      if (result.ok) {
        terminalReport += `[OK] **Ejecución exitosa** (código 0)\n\`\`\`bash\n${result.stdout || "[Comando ejecutado en segundo plano sin salida]"}\n\`\`\``;
      } else {
        terminalReport += `[FAIL] **Fallo de ejecución** (código ${result.exit_code})\n\`\`\`bash\n${result.stderr || result.error || "Error desconocido"}\n\`\`\``;
      }

      updateCurrentMessages((prev) =>
        prev.map((msg) => (msg.id === botMsgId ? { ...msg, content: terminalReport } : msg))
      );
      return;
    }

    // 3. Flujo normal con Ollama (qwen2.5-coder:7b) + Búsqueda Web
    const needsSearch =
      enableWebSearch &&
      (lower.startsWith("busca") ||
        lower.startsWith("search") ||
        lower.includes("noticias") ||
        lower.includes("precio") ||
        lower.includes("hoy") ||
        lower.includes("actual") ||
        lower.includes("quien es") ||
        lower.includes("que es") ||
        lower.includes("clima") ||
        lower.includes("versión actual"));

    let webContextPrompt = "";
    if (needsSearch) {
      try {
        const query = text.replace(/^(busca|search|consulta|investiga)\s*:?/i, "").trim();
        const searchResults = await searchWeb(query || text);
        if (searchResults.length > 0) {
          webContextPrompt =
            `\n\n[CONTEXTO WEB EN TIEMPO REAL]:\n` +
            searchResults.map((r, i) => `${i + 1}. [${r.title}](${r.url}): ${r.snippet}`).join("\n");
        }
      } catch (err) {
        console.warn("Fallo en búsqueda web:", err);
      }
    }

    try {
      const response = await fetch("http://localhost:11434/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "qwen2.5-coder:7b",
          messages: [
            {
              role: "system",
              content:
                "Eres el asistente de comando J.A.R.V.I.S. Launcher. Tienes control de la PC para abrir aplicaciones y ejecutar terminal. Responde de forma concisa, técnica y directa en español. REGLA ESTRICTA E INMUTABLE: NO uses emojis bajo ningún contexto ni circunstancia; exprésate con lenguaje técnico sobrio, tipografía pura y viñetas estándar. ESTRUCTURA VISUAL: Organiza siempre tu información de forma altamente legible con encabezados claros (## Sección), viñetas separadas (- **Concepto**: Detalle conciso), bloques de código formateados y párrafos breves. Si dispones de contexto web, úsalo para fundamentar tu respuesta y cita las fuentes con enlaces Markdown [nombre](url). Si comparas tecnologías, métricas o componentes, usa SIEMPRE tablas comparativas formateadas en Markdown estándar.",
            },
            ...messages.map((m) => ({ role: m.role, content: m.content })),
            { role: "user", content: text + webContextPrompt },
          ],
          stream: true,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let fullContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter((l) => l.trim() !== "");

        for (const line of lines) {
          try {
            const parsed = JSON.parse(line);
            if (parsed.message?.content) {
              // Filtrado exhaustivo por regex para eliminar emojis de forma determinista
              const cleanChunk = parsed.message.content.replace(
                /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F1E6}-\u{1F1FF}]/gu,
                ""
              );
              fullContent += cleanChunk;
              updateCurrentMessages((prev) =>
                prev.map((msg) =>
                  msg.id === botMsgId ? { ...msg, content: fullContent } : msg
                )
              );
            }
          } catch {
            // Chunk parcial JSON
          }
        }
      }
    } catch (err) {
      console.warn("Fallo conectando a Ollama directo, conmutando a OpenCode de contingencia:", err);
      // Conmutación automática de contingencia a OpenCode
      try {
        const strictFallbackPrompt = `${text}\n(Nota estricta: No uses emojis bajo ninguna circunstancia)`;
        const rawRes = await runOpenCodeAgent(strictFallbackPrompt);
        const ansiRegex = /\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])/g;
        const cleanRaw = stripEmojis(rawRes.replace(ansiRegex, "").replace(/\[\d+m/g, ""));

        const lines = cleanRaw.split("\n");
        const telemetryLines: string[] = [];
        const contentLines: string[] = [];

        for (const line of lines) {
          const trimmed = line.trim();
          if (
            trimmed.startsWith("Web Search") ||
            trimmed.startsWith("Parallel Web Search") ||
            trimmed.startsWith("build ·") ||
            trimmed.startsWith("[0m") ||
            trimmed.includes("Web Search \"") ||
            trimmed.includes("behavior biology") ||
            trimmed.startsWith("Searching ")
          ) {
            telemetryLines.push(trimmed);
          } else {
            contentLines.push(line);
          }
        }

        let mainContent = contentLines.join("\n").trim();
        const telemetryContent = telemetryLines.join("\n").trim();
        mainContent = mainContent.replace(/\n([A-Z0-9][^—\n]+)—/g, "\n\n- **$1**: ");

        let formattedMsg = `*(Ollama local no disponible — Respuesta generada vía OpenCode)*\n\n${mainContent || "Directiva completada."}`;
        if (telemetryContent) {
          formattedMsg += `\n\n<details><summary className="cursor-pointer text-[#71717a] hover:text-[#f4f4f5] text-[11px] font-mono">[+] Telemetría y registros de ejecución</summary>\n\n\`\`\`text\n${telemetryContent}\n\`\`\`\n</details>`;
        }

        formattedMsg = stripEmojis(formattedMsg);

        updateCurrentMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgId
              ? {
                  ...msg,
                  content: formattedMsg,
                }
              : msg
          )
        );
      } catch (opencodeErr) {
        updateCurrentMessages((prev) =>
          prev.map((msg) =>
            msg.id === botMsgId
              ? {
                  ...msg,
                  content: `[ERROR] No se pudo comunicar con Ollama ni OpenCode.\n\n_Detalle: ${(err as Error).message}_`,
                }
              : msg
          )
        );
      }
    } finally {
      clearInterval(timer);
      setIsThinking(false);
    }
  };

  return (
    <div className="relative flex flex-col h-full bg-[#000000] border-l border-[#27272a] overflow-hidden">
      {/* Modal / Banner de Confirmación de Acción Destructiva */}
      {pendingDanger && (
        <div className="absolute inset-0 z-40 bg-black/85 backdrop-blur-sm flex items-center justify-center p-6 animate-in fade-in duration-150">
          <div className="w-full max-w-md bg-[#09090b] border border-amber-600/60 rounded p-4 space-y-3 font-mono">
            <div className="flex items-center gap-2 text-amber-500 font-semibold text-xs tracking-wider uppercase">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span>Acción Destructiva / Permiso Crítico</span>
            </div>
            <p className="text-xs text-[#d4d4d8] leading-relaxed">
              {pendingDanger.description}
            </p>
            <div className="p-2 bg-[#18181b] border border-[#27272a] rounded text-[11px] text-amber-300 break-all select-all">
              $ {pendingDanger.cmd}
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => pendingDanger.resolve(false)}
                className="px-3 py-1.5 bg-[#18181b] hover:bg-[#27272a] text-[#a1a1aa] hover:text-[#ffffff] border border-[#27272a] rounded text-xs transition cursor-pointer"
              >
                [CANCELAR]
              </button>
              <button
                onClick={() => pendingDanger.resolve(true)}
                className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-black font-semibold rounded text-xs transition cursor-pointer flex items-center gap-1.5"
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>[CONFIRMAR Y EJECUTAR]</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Drawer Deslizable de Historial de Conversaciones */}
      {showHistory && (
        <div className="absolute inset-0 z-30 bg-[#09090b]/95 backdrop-blur-md flex flex-col p-4 border-l border-[#27272a] animate-in fade-in duration-150">
          <div className="flex items-center justify-between pb-3 border-b border-[#27272a]">
            <span className="font-mono text-xs uppercase tracking-wider text-[#a1a1aa] flex items-center gap-1.5">
              <History className="w-3.5 h-3.5 text-[#ffffff]" />
              historial de sesiones
            </span>
            <button
              onClick={() => setShowHistory(false)}
              className="text-[#71717a] hover:text-[#ffffff] p-1 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            onClick={createNewSession}
            className="my-3 w-full py-2 px-3 bg-[#18181b] hover:bg-[#27272a] border border-[#27272a] rounded text-xs font-mono text-[#f4f4f5] flex items-center justify-center gap-2 transition cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5 text-[#ffffff]" />
            <span>[+ NUEVA SESIÓN]</span>
          </button>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => {
                  setActiveConvId(conv.id);
                  setShowHistory(false);
                }}
                className={`group flex items-center justify-between p-2.5 rounded text-xs font-mono cursor-pointer border transition ${
                  conv.id === activeConvId
                    ? "bg-[#18181b] border-[#52525b] text-[#ffffff]"
                    : "bg-transparent border-transparent hover:bg-[#18181b]/60 text-[#a1a1aa] hover:text-[#f4f4f5]"
                }`}
              >
                <div className="flex flex-col truncate pr-2">
                  <span className="truncate">{conv.title}</span>
                  <span className="text-[10px] text-[#52525b]">{conv.timestamp} · {conv.messages.length} msgs</span>
                </div>
                {conversations.length > 1 && (
                  <button
                    onClick={(e) => deleteSession(conv.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-[#71717a] hover:text-red-400 transition cursor-pointer"
                    title="Eliminar sesión"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cabecera Técnica con Toggle de Motor (Ollama vs OpenCode) */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#27272a]">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={`font-mono text-xs uppercase tracking-wider flex items-center gap-1.5 px-2 py-1 rounded border transition cursor-pointer ${
              showHistory
                ? "bg-[#27272a] text-[#ffffff] border-[#52525b]"
                : "bg-[#18181b] text-[#a1a1aa] hover:text-[#ffffff] border-[#27272a]"
            }`}
            title="Abrir historial de conversaciones"
          >
            <History className="w-3 h-3" />
            <span>historial ({conversations.length})</span>
          </button>

          {/* Toggle de Motor LLM vs OpenCode */}
          <button
            onClick={() => setEngineMode((m) => (m === "ollama" ? "opencode" : "ollama"))}
            className={`font-mono text-[10px] uppercase tracking-wider flex items-center gap-1 px-2 py-1 rounded border transition cursor-pointer ${
              engineMode === "opencode"
                ? "bg-amber-950/40 text-amber-300 border-amber-600/70"
                : "bg-[#18181b] text-[#a1a1aa] border-[#27272a] hover:text-[#ffffff]"
            }`}
            title="Conmutar entre Ollama local y OpenCode agent"
          >
            <Cpu className="w-3 h-3" />
            <span>motor: {engineMode}</span>
          </button>

          {isThinking && (
            <span className="font-mono text-[11px] text-[#ffffff] animate-pulse">
              · pensando... ({thinkingSeconds}s)
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Toggle de Búsqueda Web */}
          <button
            onClick={() => setEnableWebSearch(!enableWebSearch)}
            className={`px-2 py-1 font-mono text-[10px] uppercase rounded border transition cursor-pointer flex items-center gap-1 ${
              enableWebSearch
                ? "bg-[#18181b] text-[#ffffff] border-[#52525b]"
                : "bg-transparent text-[#52525b] border-transparent hover:text-[#71717a]"
            }`}
            title={enableWebSearch ? "Búsqueda web en vivo activa" : "Búsqueda web desactivada"}
          >
            <Globe className="w-3 h-3" />
            <span>web: {enableWebSearch ? "on" : "off"}</span>
          </button>

          <button
            onClick={onClose}
            className="text-[#71717a] hover:text-[#ffffff] transition cursor-pointer p-1"
            title="Cerrar panel"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Flujo de Mensajes */}
      <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth-none">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.role === "user" ? "items-end" : "items-start"
            }`}
          >
            <div className="font-mono text-[10px] text-[#52525b] mb-1">
              {msg.role === "user" ? "usuario" : "jarvis"} · {msg.timestamp}
            </div>

            <div
              className={`relative max-w-[95%] p-3 text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-[#18181b] text-[#f4f4f5] border border-[#27272a] rounded"
                  : "bg-[#09090b] text-[#e4e4e7] border border-[#27272a] rounded markdown-content"
              }`}
            >
              {msg.role === "assistant" && msg.content.includes("|") && (
                <button
                  onClick={() => copyTable(msg.content, msg.id)}
                  className="absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-mono text-[#71717a] hover:text-[#ffffff] bg-[#18181b] border border-[#27272a] rounded transition cursor-pointer flex items-center gap-1"
                >
                  {copiedId === msg.id ? (
                    <>
                      <Check className="w-3 h-3 text-[#ffffff]" />
                      <span>copiado</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>copiar</span>
                    </>
                  )}
                </button>
              )}

              {msg.role === "user" ? (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {stripEmojis(msg.content)}
                </ReactMarkdown>
              )}
            </div>
          </div>
        ))}

        {/* Indicador sutil de pensando */}
        {isThinking && (
          <div className="flex items-center gap-2 text-[#71717a] font-mono text-xs p-2">
            <span className="w-1.5 h-1.5 bg-[#ffffff] rounded-full animate-ping" />
            <span>pensando...</span>
          </div>
        )}

        {/* Elemento ancla para fin de mensajes */}
        <div ref={messagesEndRef} className="h-0" />
      </div>

      {/* Sugerencias Rápidas */}
      <div className="px-3 py-1.5 flex gap-2 border-t border-[#18181b] font-mono text-[10px] overflow-x-auto">
        {["busca: noticias de linux hoy", "tabla de arquitectura", "consumo de ram"].map((sug, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(sug)}
            disabled={isThinking}
            className="text-[#71717a] hover:text-[#ffffff] whitespace-nowrap transition cursor-pointer disabled:opacity-40"
          >
            [{sug}]
          </button>
        ))}
      </div>

      {/* Entrada */}
      <div className="p-3 border-t border-[#27272a]">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isThinking}
            placeholder={enableWebSearch ? "Directiva o 'busca: tema'..." : "Escribe una directiva..."}
            className="flex-1 bg-[#09090b] border border-[#27272a] rounded px-3 py-1.5 text-xs text-[#f4f4f5] placeholder-[#52525b] focus:outline-none focus:border-[#52525b] transition font-mono"
          />
          <button
            type="submit"
            disabled={isThinking || !input.trim()}
            className="px-3 py-1.5 bg-[#f4f4f5] hover:bg-[#ffffff] text-[#000000] text-xs font-mono font-medium rounded transition cursor-pointer disabled:opacity-30"
          >
            <Send className="w-3 h-3" />
          </button>
        </form>
      </div>
    </div>
  );
}
