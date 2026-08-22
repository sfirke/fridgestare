import { vi } from 'vitest';

import type { MeResponse, Plan, PlanSummary } from '../types/api';

export function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

export function makeSession(overrides: Partial<MeResponse['user']> = {}): MeResponse {
  return {
    user: {
      id: 1,
      email: 'sam@example.com',
      timezone: 'America/New_York',
      week_starts_on: 0,
      is_admin: true,
      is_active: true,
      created_at: '2026-05-03T00:00:00Z',
      updated_at: '2026-05-03T00:00:00Z',
      ...overrides,
    },
    preferences: {
      takeout_frequency_per_week: 1,
      leftovers_per_week: 0,
      allow_simple: true,
      allow_intermediate: true,
      allow_complex: true,
      planning_guidance_text: '',
      dietary_notes: '',
      email_enabled: false,
      email_day_of_week: 6,
      email_local_time: '09:00:00',
      updated_at: '2026-05-03T00:00:00Z',
    },
    recurring_rules: [],
  };
}

export function makePlan(weekStartDate: string, label: string): Plan {
  return {
    id: Number(weekStartDate.replaceAll('-', '')),
    week_start_date: weekStartDate,
    status: 'draft',
    generation_source: 'manual',
    planner_explanation: `${label} explanation`,
    slots: [
      {
        id: 101,
        slot_date: weekStartDate,
        slot_order: 0,
        slot_type: 'meal',
        meal_id: 1,
        discovered_candidate_id: null,
        title_snapshot: label,
        notes_snapshot: '',
        selection_reason: 'Planned for the week.',
        outcome_status: null,
        outcome_logged_at: null,
      },
    ],
  };
}

export function planSummary(plan: Plan): PlanSummary {
  return {
    id: plan.id,
    week_start_date: plan.week_start_date,
    status: plan.status,
    generation_source: plan.generation_source,
  };
}

export type Route = (request: {
  path: string;
  method: string;
  body: unknown;
}) => Response | null;

type BackendOptions = {
  session?: MeResponse;
  meals?: unknown[];
  tags?: Array<{ name: string }>;
  plans?: PlanSummary[];
  /** Week plans keyed by week_start_date; anything missing answers 404. */
  weekPlans?: Record<string, Plan>;
  currentPlan?: Plan | null;
  /** Extra handlers, tried before the defaults. */
  routes?: Route[];
};

/**
 * Install a fetch stub that answers by route rather than by call order.
 *
 * The suite previously chained mockResolvedValueOnce per request, which coupled every
 * test to the exact order the dashboard happens to fire its loads in.
 */
export function stubBackend(options: BackendOptions = {}) {
  const {
    session = makeSession(),
    meals = [],
    tags = [],
    plans = [],
    weekPlans = {},
    currentPlan = null,
    routes = [],
  } = options;

  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input).replace(/^\/api/, '');
    const method = init?.method ?? 'GET';
    const body = init?.body ? JSON.parse(String(init.body)) : undefined;

    for (const route of routes) {
      const response = route({ path, method, body });
      if (response) {
        return response;
      }
    }

    if (path === '/auth/me' || path === '/auth/login') {
      return jsonResponse({ me: session });
    }
    if (path === '/me') {
      return jsonResponse(session);
    }
    if (path.startsWith('/meals')) {
      return jsonResponse(meals);
    }
    if (path === '/tags/suggestions') {
      return jsonResponse(tags);
    }
    if (path === '/plans') {
      return jsonResponse(plans);
    }
    if (path === '/plans/current') {
      return currentPlan
        ? jsonResponse(currentPlan)
        : jsonResponse({ detail: 'No plan for the active planning week' }, 404);
    }
    const weekMatch = path.match(/^\/plans\/week\/(\d{4}-\d{2}-\d{2})$/);
    if (weekMatch) {
      const plan = weekPlans[weekMatch[1]];
      return plan ? jsonResponse(plan) : jsonResponse({ detail: 'Plan not found' }, 404);
    }
    return jsonResponse({ detail: `Unhandled route ${method} ${path}` }, 404);
  });

  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}
