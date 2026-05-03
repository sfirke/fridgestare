import type {
  ChatResponse,
  DiscoveryCandidate,
  EmailPreview,
  EmailSendResponse,
  LoginResponse,
  Meal,
  MeResponse,
  Plan,
  RecurringRule,
  UserPreferences,
} from '../types/api';

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  includeCsrf?: boolean;
  responseType?: 'json' | 'text';
};

function readCookie(name: string): string | null {
  const cookie = document.cookie
    .split('; ')
    .find((entry) => entry.startsWith(`${name}=`));
  return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : null;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers();
  if (options.includeCsrf) {
    const csrf = readCookie('fridgestare_csrf');
    if (csrf) {
      headers.set('X-CSRF-Token', csrf);
    }
  }
  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`/api${path}`, {
    method: options.method ?? 'GET',
    credentials: 'include',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const contentType = response.headers.get('content-type') ?? '';
    const detail = contentType.includes('application/json')
      ? (await response.json()).detail ?? response.statusText
      : await response.text();
    throw new Error(detail || response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  if (options.responseType === 'text') {
    return (await response.text()) as T;
  }
  return (await response.json()) as T;
}

export const api = {
  login(email: string, password: string) {
    return request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: { email, password },
    });
  },
  logout() {
    return request<{ status: string }>('/auth/logout', {
      method: 'POST',
      includeCsrf: true,
    });
  },
  authMe() {
    return request<LoginResponse>('/auth/me');
  },
  getMe() {
    return request<MeResponse>('/me');
  },
  updatePreferences(payload: Partial<UserPreferences>) {
    return request<UserPreferences>('/me/preferences', {
      method: 'PATCH',
      body: payload,
      includeCsrf: true,
    });
  },
  replaceRecurringRules(rules: Array<Omit<RecurringRule, 'id' | 'created_at' | 'updated_at'>>) {
    return request<RecurringRule[]>('/me/schedule-rules', {
      method: 'PATCH',
      body: { rules },
      includeCsrf: true,
    });
  },
  listMeals(params?: { includeArchived?: boolean; complexity?: string; recurrenceTier?: string; tag?: string }) {
    const search = new URLSearchParams();
    if (params?.includeArchived) search.set('include_archived', 'true');
    if (params?.complexity) search.set('complexity', params.complexity);
    if (params?.recurrenceTier) search.set('recurrence_tier', params.recurrenceTier);
    if (params?.tag) search.set('tag', params.tag);
    const suffix = search.size ? `?${search.toString()}` : '';
    return request<Meal[]>(`/meals${suffix}`);
  },
  createMeal(payload: Record<string, unknown>) {
    return request<Meal>('/meals', { method: 'POST', body: payload, includeCsrf: true });
  },
  updateMeal(mealId: number, payload: Record<string, unknown>) {
    return request<Meal>(`/meals/${mealId}`, { method: 'PATCH', body: payload, includeCsrf: true });
  },
  archiveMeal(mealId: number) {
    return request<void>(`/meals/${mealId}`, { method: 'DELETE', includeCsrf: true });
  },
  bulkFastAdd(text: string) {
    const meals = text
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)
      .map((title) => ({ title }));
    return request<Meal[]>('/meals/bulk-fast-add', {
      method: 'POST',
      body: { meals },
      includeCsrf: true,
    });
  },
  exportMealsCsv() {
    return request<string>('/meals/export.csv', { responseType: 'text' });
  },
  getTagSuggestions() {
    return request<Array<{ name: string }>>('/tags/suggestions');
  },
  getCurrentPlan() {
    return request<Plan>('/plans/current');
  },
  getWeekPlan(weekStart: string) {
    return request<Plan>(`/plans/week/${weekStart}`);
  },
  generatePlan(weekStartDate?: string, forceRegenerate = false) {
    return request<Plan>('/plans/generate', {
      method: 'POST',
      body: { week_start_date: weekStartDate ?? null, force_regenerate: forceRegenerate },
      includeCsrf: true,
    });
  },
  rerollSlot(planId: number, slotId: number) {
    return request<Plan>(`/plans/${planId}/reroll-slot`, {
      method: 'POST',
      body: { slot_id: slotId },
      includeCsrf: true,
    });
  },
  moveSlot(planId: number, sourceSlotId: number, targetSlotId: number) {
    return request<Plan>(`/plans/${planId}/move-slot`, {
      method: 'POST',
      body: { source_slot_id: sourceSlotId, target_slot_id: targetSlotId },
      includeCsrf: true,
    });
  },
  setSlot(planId: number, payload: Record<string, unknown>) {
    return request<Plan>(`/plans/${planId}/set-slot`, {
      method: 'POST',
      body: payload,
      includeCsrf: true,
    });
  },
  undoPlan(planId: number) {
    return request<Plan>(`/plans/${planId}/undo`, { method: 'POST', includeCsrf: true });
  },
  updateOutcome(planId: number, slotId: number, outcomeStatus: string | null) {
    return request<Plan>(`/plans/${planId}/slots/${slotId}/outcome-status`, {
      method: 'POST',
      body: { outcome_status: outcomeStatus },
      includeCsrf: true,
    });
  },
  chatPlan(planId: number, message: string) {
    return request<ChatResponse>(`/plans/${planId}/chat`, {
      method: 'POST',
      body: { message },
      includeCsrf: true,
    });
  },
  suggestDiscovery(slotId: number | null, query: string) {
    return request<DiscoveryCandidate[]>('/discovery/suggest', {
      method: 'POST',
      body: { slot_id: slotId, query },
      includeCsrf: true,
    });
  },
  acceptDiscovery(candidateId: number, payload: Record<string, unknown>) {
    return request<{ candidate: DiscoveryCandidate; meal: Meal | null }>(`/discovery/${candidateId}/accept`, {
      method: 'POST',
      body: payload,
      includeCsrf: true,
    });
  },
  previewEmail(planId: number) {
    return request<EmailPreview>(`/plans/${planId}/email-preview`);
  },
  sendEmail(planId: number) {
    return request<EmailSendResponse>(`/plans/${planId}/send-email`, {
      method: 'POST',
      includeCsrf: true,
    });
  },
};
