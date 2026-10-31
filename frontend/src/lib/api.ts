import type { Persona, RoastRequest, RoastResult } from "@/types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new Error("Can't reach the RoastScribe backend. Is `python run.py` running on port 8000?");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`);
  }
  return res.json();
}

export const fetchPersonas = () => request<Persona[]>("/api/personas");

export const createRoast = (payload: RoastRequest) =>
  request<RoastResult>("/api/roast", { method: "POST", body: JSON.stringify(payload) });
