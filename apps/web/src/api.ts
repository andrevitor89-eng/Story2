import type { Book, Job, StorySummary, User, UserVoice, VoiceList } from "./types";

const TOKEN_KEY = "story2_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : "Erro na requisicao");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  register: (email: string, password: string, name: string) =>
    request<{ access_token: string }>("/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<User>("/v1/auth/me"),
  stories: (gender?: string) =>
    request<StorySummary[]>(`/v1/stories${gender ? `?gender=${gender}` : ""}`),
  createBook: (payload: { child_name: string; child_age: number; child_gender: string }) =>
    request<Book>("/v1/books", { method: "POST", body: JSON.stringify(payload) }),
  getBook: (id: string) => request<Book>(`/v1/books/${id}`),
  listBooks: () => request<Book[]>("/v1/books"),
  uploadPhoto: (id: string, file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<Book>(`/v1/books/${id}/photo`, { method: "POST", body: fd });
  },
  generate: (
    id: string,
    story_id: string,
    opts?: { age_band?: string; age_band_mode?: "auto" | "manual" },
  ) =>
    request<Job>(`/v1/books/${id}/generate`, {
      method: "POST",
      body: JSON.stringify({
        story_id,
        age_band: opts?.age_band,
        age_band_mode: opts?.age_band_mode ?? "auto",
      }),
    }),
  generateVideo: (id: string) =>
    request<Job>(`/v1/books/${id}/video`, { method: "POST", body: JSON.stringify({}) }),
  generateNarratedVideo: (id: string, opts?: { voice_id?: string | null }) =>
    request<Job>(`/v1/books/${id}/narrated-video`, {
      method: "POST",
      body: JSON.stringify({ voice_id: opts?.voice_id || null }),
    }),
  listVoices: () => request<VoiceList>("/v1/voices"),
  uploadVoice: (file: File, name: string, makeDefault = false) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("name", name);
    fd.append("make_default", makeDefault ? "true" : "false");
    return request<UserVoice>("/v1/voices", { method: "POST", body: fd });
  },
  setDefaultVoice: (id: string) =>
    request<UserVoice>(`/v1/voices/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ is_default: true }),
    }),
  deleteVoice: (id: string) => request<void>(`/v1/voices/${id}`, { method: "DELETE" }),
};