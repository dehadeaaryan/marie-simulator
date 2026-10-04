export type Listing = { address: number; line: number; label: string | null; operation: string; word: number; source: string };
export type Machine = {
  id: string; source: string; status: 'ready' | 'running' | 'paused' | 'waiting_for_input' | 'halted' | 'failed';
  revision: number; steps: number; speed: number; error: string | null;
  registers: Record<string, number>; memory: number[]; output: number[]; input: number[];
  current_address: number; current_line: number | null; last_address: number | null; listing: Listing[];
  expires_in: number; limits: { instructions: number; output: number; run_seconds: number };
};
export class ApiError extends Error {
  constructor(public status: number, message: string, public line?: number, public kind?: string) { super(message); }
}
export async function request<T>(path: string, body?: unknown): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 8000);
  try {
    const response = await fetch(`/api${path}`, {
      method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', signal: controller.signal,
      headers: { 'Content-Type': 'application/json', 'X-Marie-Client': 'web' },
      body: body === undefined ? undefined : JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok) throw new ApiError(response.status, data.detail || 'Request failed.', data.line, data.kind);
    return data as T;
  } finally { clearTimeout(timer); }
}
