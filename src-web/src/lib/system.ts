// Librería cliente para ejecutar comandos de sistema y OpenCode
// Compatible con Tauri Rust invoke() y con el bridge local HTTP (127.0.0.1:3002)

export interface ShellExecutionResult {
  stdout: string;
  stderr: string;
  exit_code: number;
  ok: boolean;
  error?: string;
}

export async function executeSystemCommand(cmd: string): Promise<ShellExecutionResult> {
  // 0. Si estamos en el desktop Electron (ventana nativa, sin MSVC/Rust)
  if (typeof window !== "undefined" && (window as any).electronAPI) {
    try {
      const res = await (window as any).electronAPI.executeShell(cmd);
      return {
        stdout: res.stdout ?? "",
        stderr: res.stderr ?? "",
        exit_code: res.exitCode ?? 0,
        ok: !!res.ok,
      };
    } catch (err) {
      return { stdout: "", stderr: String(err), exit_code: 1, ok: false, error: String(err) };
    }
  }

  // 1. Si estamos dentro de Tauri nativo
  if (typeof window !== "undefined" && (window as any).__TAURI__) {
    try {
      const { invoke } = (window as any).__TAURI__.core || (window as any).__TAURI__;
      const stdout = await invoke("execute_shell", { cmd });
      return { stdout, stderr: "", exit_code: 0, ok: true };
    } catch (err) {
      return { stdout: "", stderr: String(err), exit_code: 1, ok: false, error: String(err) };
    }
  }

  // 2. Si estamos en navegador web de desarrollo, usar bridge server
  try {
    const res = await fetch("http://127.0.0.1:3002/api/shell", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cmd }),
    });
    if (res.ok) {
      return await res.json();
    }
    return { stdout: "", stderr: "Bridge HTTP error", exit_code: res.status, ok: false };
  } catch (e) {
    return {
      stdout: "",
      stderr: "No se pudo conectar al puente local (http://127.0.0.1:3002).",
      exit_code: 1,
      ok: false,
      error: (e as Error).message,
    };
  }
}

export async function runOpenCodeAgent(prompt: string): Promise<string> {
  // 0. Si estamos en el desktop Electron
  if (typeof window !== "undefined" && (window as any).electronAPI) {
    try {
      return await (window as any).electronAPI.runOpencode(prompt);
    } catch (err) {
      return `Error ejecutando OpenCode vía Electron: ${err}`;
    }
  }

  // 1. Si estamos en Tauri nativo
  if (typeof window !== "undefined" && (window as any).__TAURI__) {
    try {
      const { invoke } = (window as any).__TAURI__.core || (window as any).__TAURI__;
      const res = await invoke("run_opencode", { prompt });
      return res;
    } catch (err) {
      return `Error ejecutando OpenCode vía Tauri: ${err}`;
    }
  }

  // 2. Modo navegador web vía bridge
  try {
    const res = await fetch("http://127.0.0.1:3002/api/opencode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    if (res.ok) {
      const data = await res.json();
      return data.output || data.error || "OpenCode completado sin salida.";
    }
    return `Error HTTP ${res.status} comunicando con OpenCode`;
  } catch (e) {
    return `No se pudo conectar con el servidor bridge para OpenCode: ${(e as Error).message}`;
  }
}

export async function triggerSystemMode(mode: string): Promise<boolean> {
  // 0. Desktop Electron: IPC nativo (este era el P0 que faltaba en Tauri)
  if (typeof window !== "undefined" && (window as any).electronAPI) {
    try {
      const res = await (window as any).electronAPI.launchMode(mode);
      return !!res?.ok;
    } catch {
      return false;
    }
  }

  try {
    const res = await fetch("http://127.0.0.1:3002/api/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

// Detección de comandos destructivos que requieren confirmación explícita
export function isDangerousCommand(cmd: string): boolean {
  const dangerousPatterns = [
    /\brm\b/i,
    /\brmdir\b/i,
    /\bdel\b/i,
    /\berase\b/i,
    /\bkill\b/i,
    /\bpkill\b/i,
    /\bformat\b/i,
    /\bshred\b/i,
    /\bdd\b/i,
    /\bmkfs\b/i,
    /\bshutdown\b/i,
    /\breboot\b/i,
    /\bpoweroff\b/i,
    />\s*\/dev\//i,
    /:\(\)\s*\{/i, // fork bomb
  ];
  return dangerousPatterns.some((pattern) => pattern.test(cmd));
}
