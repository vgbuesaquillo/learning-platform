/**
 * Cliente HTTP para comunicarse con el backend FastAPI.
 * Maneja autenticación JWT y errores de forma centralizada.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  const res = await fetch(`${API_BASE}/api/v1${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error desconocido" }));
    throw new ApiError(res.status, err.detail || "Error del servidor");
  }

  if (res.status === 204) return {} as T;
  return res.json();
}

// ── Auth ────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (body: { email: string; full_name: string; password: string }) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(body) }),

  login: async (email: string, password: string): Promise<{ access_token: string }> => {
    const data = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem("access_token", data.access_token);
    return data;
  },

  me: () => request<User>("/auth/me"),

  logout: () => {
    localStorage.removeItem("access_token");
  },
};

// ── Evidencias ──────────────────────────────────────────────────────────────

export const evidenceApi = {
  create: (body: { activity_id: string; content: string; reflection?: string; confidence_level?: number }) =>
    request<Evidence>("/evidence/", { method: "POST", body: JSON.stringify(body) }),

  submit: (evidenceId: string) =>
    request<Evidence>(`/evidence/${evidenceId}/submit`, { method: "POST" }),

  myEvidences: () => request<Evidence[]>("/evidence/my"),
};

// ── Progreso ────────────────────────────────────────────────────────────────

export const progressApi = {
  dashboard: (moduleId: string) =>
    request<LearningDashboard>(`/progress/dashboard/${moduleId}`),
};

// ── Tipos TypeScript ────────────────────────────────────────────────────────

export type DomainLevel = "novato" | "intermedio" | "competente" | "experto";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_instructor: boolean;
  created_at: string;
}

export interface Evidence {
  id: string;
  activity_id: string;
  content: string;
  reflection?: string;
  confidence_level?: number;
  status: "borrador" | "enviada" | "revisada" | "aprobada";
  score?: number;
  rubric_evaluation: Record<string, unknown>;
  qualitative_feedback?: string;
  created_at: string;
  submitted_at?: string;
}

export interface CompetencyProgress {
  competency_id: string;
  competency_name: string;
  current_level: DomainLevel;
  domain_score: number;
  consistency_score: number;
  evidence_count: number;
  last_evidence_at?: string;
  history: Array<{ date: string; score: number; domain_score: number; level: string }>;
}

export interface LearningDashboard {
  user_id: string;
  module_id: string;
  module_title: string;
  overall_domain_score: number;
  highest_level_achieved: DomainLevel;
  competencies_at_expert: number;
  total_evidences: number;
  approved_evidences: number;
  avg_confidence_vs_score: number;
  consistency_index: number;
  competency_breakdown: CompetencyProgress[];
}
