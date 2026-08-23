import { useCallback, useEffect, useState } from 'react';

import { api } from '../lib/api';
import { shiftCalendarDate } from '../lib/dates';
import { DEFAULT_TIMEZONE } from '../lib/timezones';
import type {
  Meal,
  MeResponse,
  Plan,
  PlanSummary,
  RecurringRule,
  UserPreferences,
} from '../types/api';
import type { StatusMessages } from './useStatusMessages';

export type AuthState = 'loading' | 'anonymous' | 'authenticated';

export type RuleDraft = Omit<RecurringRule, 'id' | 'created_at' | 'updated_at'>;

export const defaultPreferences: UserPreferences = {
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
  updated_at: '',
};

export function parseWeekFromPath(): string | null {
  const match = window.location.pathname.match(/^\/plans\/(\d{4}-\d{2}-\d{2})$/);
  return match?.[1] ?? null;
}

function syncBrowserWeekPath(weekStart: string | null, mode: 'push' | 'replace' = 'push') {
  const nextPath = weekStart ? `/plans/${weekStart}` : '/';
  if (window.location.pathname === nextPath && !window.location.search) {
    return;
  }
  window.history[mode === 'replace' ? 'replaceState' : 'pushState']({}, '', nextPath);
}

function toRuleDrafts(rules: RecurringRule[]): RuleDraft[] {
  return rules.map((rule) => ({
    day_of_week: rule.day_of_week,
    rule_type: rule.rule_type,
    rule_payload: rule.rule_payload,
    priority: rule.priority,
    active: rule.active,
  }));
}

/**
 * Session, meal library, and weekly plan state for the signed-in dashboard.
 *
 * The plan, the week being viewed, and the browser URL have to move together, so they
 * are owned here rather than by the individual views.
 */
export function useDashboard(messages: StatusMessages) {
  const [authState, setAuthState] = useState<AuthState>('loading');
  const [session, setSession] = useState<MeResponse | null>(null);
  const [meals, setMeals] = useState<Meal[]>([]);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [previousPlan, setPreviousPlan] = useState<Plan | null>(null);
  const [planHistory, setPlanHistory] = useState<PlanSummary[]>([]);
  const [tagSuggestions, setTagSuggestions] = useState<string[]>([]);
  const [viewedWeek, setViewedWeek] = useState<string | null>(() => parseWeekFromPath());

  const [preferencesDraft, setPreferencesDraft] = useState<UserPreferences>(defaultPreferences);
  const [rulesDraft, setRulesDraft] = useState<RuleDraft[]>([]);
  const [timezoneDraft, setTimezoneDraft] = useState(DEFAULT_TIMEZONE);
  const [weekStartsOnDraft, setWeekStartsOnDraft] = useState(0);

  const syncPlanContext = useCallback(async (nextPlan: Plan | null) => {
    setPlan(nextPlan);
    if (!nextPlan) {
      setPreviousPlan(null);
      return;
    }
    try {
      setPreviousPlan(await api.getWeekPlan(shiftCalendarDate(nextPlan.week_start_date, -7)));
    } catch {
      // A missing previous week just means no leftover sources from it.
      setPreviousPlan(null);
    }
  }, []);

  const loadPlanView = useCallback(
    async (targetWeek: string | null) => {
      try {
        const nextPlan = targetWeek
          ? await api.getWeekPlan(targetWeek)
          : await api.getCurrentPlan();
        await syncPlanContext(nextPlan);
      } catch {
        // No plan for this week yet; the planner renders its empty state.
        setPlan(null);
        setPreviousPlan(null);
      }
    },
    [syncPlanContext],
  );

  const loadDashboard = useCallback(
    async (targetWeek: string | null) => {
      const me = await api.getMe();
      const [mealsResponse, tags, history] = await Promise.all([
        api.listMeals(),
        api.getTagSuggestions(),
        api.listPlans(),
      ]);
      await loadPlanView(targetWeek);
      setSession(me);
      setTimezoneDraft(me.user.timezone || DEFAULT_TIMEZONE);
      setWeekStartsOnDraft(me.user.week_starts_on);
      setPreferencesDraft(me.preferences);
      setRulesDraft(toRuleDrafts(me.recurring_rules));
      setMeals(mealsResponse);
      setPlanHistory(history);
      setTagSuggestions(tags.map((tag) => tag.name));
      setAuthState('authenticated');
    },
    [loadPlanView],
  );

  useEffect(() => {
    let active = true;
    api
      .authMe()
      .then(() => (active ? loadDashboard(parseWeekFromPath()) : undefined))
      .catch(() => {
        if (active) {
          setAuthState('anonymous');
        }
      });
    return () => {
      active = false;
    };
  }, [loadDashboard]);

  useEffect(() => {
    function handlePopState() {
      const nextWeek = parseWeekFromPath();
      setViewedWeek(nextWeek);
      if (authState === 'authenticated') {
        void loadPlanView(nextWeek);
      }
    }

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, [authState, loadPlanView]);

  const refreshMeals = useCallback(async () => {
    setMeals(await api.listMeals());
  }, []);

  const refreshTagSuggestions = useCallback(async () => {
    const tags = await api.getTagSuggestions();
    setTagSuggestions(tags.map((tag) => tag.name));
  }, []);

  const refreshPlan = useCallback(async () => {
    if (plan) {
      await syncPlanContext(await api.getWeekPlan(plan.week_start_date));
    }
  }, [plan, syncPlanContext]);

  /** Apply a plan mutation and fold the returned plan back into view state. */
  const applyPlanUpdate = useCallback(
    (updater: () => Promise<Plan>, success: string) =>
      messages.run(
        async () => {
          await syncPlanContext(await updater());
        },
        { success, failure: 'Unable to update the plan.' },
      ),
    [messages, syncPlanContext],
  );

  const login = useCallback(
    (email: string, password: string) =>
      messages.run(
        async () => {
          await api.login(email, password);
          await loadDashboard(parseWeekFromPath());
        },
        { success: 'Logged in.', failure: 'Unable to log in.' },
      ),
    [loadDashboard, messages],
  );

  const logout = useCallback(
    () =>
      messages.run(
        async () => {
          await api.logout();
          setAuthState('anonymous');
          setSession(null);
          setPlan(null);
          setPreviousPlan(null);
          setPlanHistory([]);
          setMeals([]);
          setTimezoneDraft(DEFAULT_TIMEZONE);
          setWeekStartsOnDraft(0);
          setViewedWeek(null);
          syncBrowserWeekPath(null, 'replace');
        },
        { success: 'Logged out.', failure: 'Unable to log out.' },
      ),
    [messages],
  );

  const generatePlan = useCallback(() => {
    const shouldRegenerate = plan !== null;
    return messages.run(
      async () => {
        const nextPlan = await api.generatePlan(viewedWeek ?? undefined, shouldRegenerate);
        const history = await api.listPlans();
        await syncPlanContext(nextPlan);
        setPlanHistory(history);
        setViewedWeek(nextPlan.week_start_date);
        syncBrowserWeekPath(nextPlan.week_start_date, 'replace');
      },
      {
        success: shouldRegenerate ? 'Weekly plan regenerated.' : 'Weekly plan generated.',
        failure: 'Unable to generate plan.',
      },
    );
  }, [messages, plan, syncPlanContext, viewedWeek]);

  const openWeek = useCallback(
    async (weekStart: string | null) => {
      messages.reset();
      setViewedWeek(weekStart);
      syncBrowserWeekPath(weekStart);
      await loadPlanView(weekStart);
    },
    [loadPlanView, messages],
  );

  const savePreferences = useCallback(
    () =>
      messages.run(
        async () => {
          // updated_at is server-owned; everything else on the draft is editable.
          const { updated_at: _serverTimestamp, ...editable } = preferencesDraft;
          const updatedPreferences = await api.updatePreferences({
            ...editable,
            timezone: timezoneDraft,
            week_starts_on: weekStartsOnDraft,
          });
          const updatedRules = await api.replaceRecurringRules(rulesDraft);
          setSession((current) =>
            current
              ? {
                  ...current,
                  user: {
                    ...current.user,
                    timezone: timezoneDraft,
                    week_starts_on: weekStartsOnDraft,
                  },
                  preferences: updatedPreferences,
                  recurring_rules: updatedRules,
                }
              : current,
          );
          setPreferencesDraft(updatedPreferences);
          // The planning week itself can shift when the timezone or week start moves.
          await loadPlanView(viewedWeek);
        },
        { success: 'Preferences saved.', failure: 'Unable to save preferences.' },
      ),
    [
      loadPlanView,
      messages,
      preferencesDraft,
      rulesDraft,
      timezoneDraft,
      viewedWeek,
      weekStartsOnDraft,
    ],
  );

  return {
    authState,
    session,
    meals,
    plan,
    previousPlan,
    planHistory,
    tagSuggestions,
    viewedWeek,
    preferencesDraft,
    setPreferencesDraft,
    rulesDraft,
    setRulesDraft,
    timezoneDraft,
    setTimezoneDraft,
    weekStartsOnDraft,
    setWeekStartsOnDraft,
    applyPlanUpdate,
    generatePlan,
    login,
    logout,
    openWeek,
    refreshMeals,
    refreshPlan,
    refreshTagSuggestions,
    savePreferences,
  };
}

export type Dashboard = ReturnType<typeof useDashboard>;
