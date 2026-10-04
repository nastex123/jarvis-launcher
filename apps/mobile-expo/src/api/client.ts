/* Cliente tipado del contrato docs/ESPEC-remoto.md v1. */
export type ModeApp = { name: string; command: string; args?: string };
export type ModeInfo = { id: string; name: string; color: string; description: string; apps: ModeApp[] };
export type ProposalCard = { id: string; tool: string; summary: string; risk: "read" | "write" | "shell"; args: Record<string, unknown>; diff?: string };

const j = async (r: Response) => {
  if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text()}`);
  return r.json();
};

export const api = (base: string, jwt = "") => {
  const h = () => ({ "Content-Type": "application/json", ...(jwt ? { Authorization: `Bearer ${jwt}` } : {}) });
  return {
    health: () => fetch(`${base}/health`).then(j),
    pairing: (): Promise<{ pairing_url: string; token: string; expires_in_s: number }> =>
      fetch(`${base}/api/pairing`).then(j),
    exchange: (token: string): Promise<{ jwt: string; expires_in_s: number }> =>
      fetch(`${base}/api/pairing/exchange`, { method: "POST", headers: h(), body: JSON.stringify({ token }) }).then(j),
    modes: (): Promise<{ modes: ModeInfo[] }> => fetch(`${base}/api/modes`, { headers: h() }).then(j),
    runMode: (mode_id: string, idempotency_key: string) =>
      fetch(`${base}/api/modes/run`, { method: "POST", headers: h(), body: JSON.stringify({ mode_id, idempotency_key }) }).then(j),
    chatTurn: (text: string, history: unknown[] = []) =>
      fetch(`${base}/api/chat/turn`, { method: "POST", headers: h(), body: JSON.stringify({ text, history }) }).then(j),
    decide: (proposal_id: string, decision: "approve" | "reject" | "edit", tool: string, args: Record<string, unknown>) =>
      fetch(`${base}/api/decide`, {
        method: "POST", headers: h(),
        body: JSON.stringify({ proposal_id, decision, new_args: { _tool: tool, ...args } }),
      }).then(j),
    rustdesk: (): Promise<{ hbbs: string; hbbr: string; device_id: string }> =>
      fetch(`${base}/api/rustdesk`, { headers: h() }).then(j),
  };
};
