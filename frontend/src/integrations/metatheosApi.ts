export interface PhaseDto {
  id: string;
  title: string;
  status: string;
  start_date?: string | null;
  target_date?: string | null;
  description?: string | null;
}

export interface DayDto {
  id: string;
  phase_id: string;
  day_type: string;
  created_at: string;
}

export interface TimelineItemDto {
  kind: "event" | "annotation";
  ts: string;
  id: string;
  summary: string;
  phase_id?: string | null;
  goal_id?: string | null;
  work_item_id?: string | null;
  day_id?: string | null;
}

export interface ContextOverviewDto {
  active_phase?: PhaseDto | null;
  current_day?: DayDto | null;
  counts: {
    phases: number;
    goals: number;
    work_items: number;
    events: number;
    annotations: number;
  };
  db: {
    path?: string | null;
    mode: string;
    healthy: boolean;
  };
}

interface ListResponse<T> {
  data: T;
}

const METATHEOS_API_BASE = import.meta.env.VITE_METATHEOS_API_URL || "/metatheos-api";

const buildUrl = (path: string) => {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${METATHEOS_API_BASE}${normalized}`;
};

const fetchJson = async <T,>(path: string, init: RequestInit = {}): Promise<T> => {
  const response = await fetch(buildUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
  });

  if (!response.ok) {
    let message = response.statusText || "Request failed";
    try {
      const data = await response.json();
      message = data?.message || data?.detail || message;
    } catch {
      // Ignore body parse errors.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
};

export const getContextOverview = () => fetchJson<ContextOverviewDto>("/api/context/overview");

export const listPhases = () => fetchJson<ListResponse<PhaseDto[]>>("/api/phases");

export const getTimeline = (options: { limit?: number; phaseId?: string; goalId?: string } = {}) => {
  const params = new URLSearchParams();
  if (options.limit) {
    params.set("limit", String(options.limit));
  }
  if (options.phaseId) {
    params.set("phase_id", options.phaseId);
  }
  if (options.goalId) {
    params.set("goal_id", options.goalId);
  }
  const query = params.toString();
  const path = query ? `/api/timeline?${query}` : "/api/timeline";
  return fetchJson<ListResponse<TimelineItemDto[]>>(path);
};

export const getToday = () => fetchJson<ListResponse<DayDto | null>>("/api/day/today");
