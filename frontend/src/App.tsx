import { FormEvent, useEffect, useMemo, useState } from 'react';

import { api } from './lib/api';
import type {
  ChatResponse,
  DiscoveryCandidate,
  EmailPreview,
  Meal,
  MealSeasonalRecurrenceOverride,
  MeResponse,
  Plan,
  PlanSlot,
  PlanSummary,
  RecurrenceTier,
  RecurringRule,
  SeasonName,
  UserPreferences,
} from './types/api';
import './styles.css';

type RuleDraft = {
  day_of_week: number;
  rule_type: string;
  rule_payload: Record<string, unknown>;
  priority: number;
  active: boolean;
};

type LeftoverOption = {
  mealId: number;
  label: string;
};

type DashboardView = 'planner' | 'meals' | 'preferences';

const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const shortDayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

const dashboardViews: Array<{ id: DashboardView; label: string; description: string }> = [
  { id: 'planner', label: 'Planner', description: 'Week view, chat, discovery, and email.' },
  { id: 'meals', label: 'Meals', description: 'Library management and meal entry.' },
  { id: 'preferences', label: 'Preferences', description: 'Guidance, email settings, and recurring rules.' },
];

const seasonOptions: Array<{ id: SeasonName; label: string }> = [
  { id: 'winter', label: 'Winter' },
  { id: 'spring', label: 'Spring' },
  { id: 'summer', label: 'Summer' },
  { id: 'fall', label: 'Fall' },
];

const recurrenceOptions: Array<{ value: RecurrenceTier; label: string }> = [
  { value: 'staple', label: 'Staple' },
  { value: 'regular', label: 'Regular' },
  { value: 'treat', label: 'Treat' },
  { value: 'none', label: 'None' },
];

type MealFormSeasonalOverrides = Record<SeasonName, '' | RecurrenceTier>;

type MealForm = {
  title: string;
  notes: string;
  complexity: string;
  recurrence_tier: RecurrenceTier;
  seasonal_recurrence_overrides: MealFormSeasonalOverrides;
  source_note: string;
  source_url: string;
  dietary_exclusions: string;
  tags: string;
};


function createDefaultSeasonalRecurrenceOverrides(): MealFormSeasonalOverrides {
  return {
    winter: '',
    spring: '',
    summer: '',
    fall: '',
  };
}

const defaultPreferences: UserPreferences = {
  novel_meal_ratio: 0.15,
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

function createDefaultMealForm(): MealForm {
  return {
    title: '',
    notes: '',
    complexity: 'intermediate',
    recurrence_tier: 'regular',
    seasonal_recurrence_overrides: createDefaultSeasonalRecurrenceOverrides(),
    source_note: '',
    source_url: '',
    dietary_exclusions: '',
    tags: '',
  };
}

function parseWeekFromPath(): string | null {
  const match = window.location.pathname.match(/^\/plans\/(\d{4}-\d{2}-\d{2})$/);
  return match?.[1] ?? null;
}

function parseCalendarDate(dateString: string): Date {
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    const [year, month, day] = dateString.split('-').map(Number);
    return new Date(year, month - 1, day);
  }

  return new Date(dateString);
}

function formatCalendarDateKey(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function shiftCalendarDate(dateString: string, dayOffset: number): string {
  const shifted = parseCalendarDate(dateString);
  shifted.setDate(shifted.getDate() + dayOffset);
  return formatCalendarDateKey(shifted);
}

function syncBrowserWeekPath(weekStart: string | null, mode: 'push' | 'replace' = 'push') {
  const nextPath = weekStart ? `/plans/${weekStart}` : '/';
  if (window.location.pathname === nextPath && !window.location.search) {
    return;
  }
  window.history[mode === 'replace' ? 'replaceState' : 'pushState']({}, '', nextPath);
}

function formatDate(dateString: string): string {
  return parseCalendarDate(dateString).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
}

function formatShortDate(dateString: string): string {
  return parseCalendarDate(dateString).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function formatMonthLabel(dateString: string): string {
  return parseCalendarDate(dateString).toLocaleDateString(undefined, { month: 'short' });
}

function formatDayNumber(dateString: string): string {
  return parseCalendarDate(dateString).toLocaleDateString(undefined, { day: 'numeric' });
}

function formatWeekRange(weekStart: string): string {
  const start = parseCalendarDate(weekStart);
  const end = parseCalendarDate(weekStart);
  end.setDate(end.getDate() + 6);
  return `${formatShortDate(formatCalendarDateKey(start))} - ${formatShortDate(formatCalendarDateKey(end))}`;
}

function slotLabel(slot: PlanSlot): string {
  const dayIndex = parseCalendarDate(slot.slot_date).getDay();
  return `${dayNames[dayIndex === 0 ? 6 : dayIndex - 1]}`;
}

function slotCalendarLabel(slot: PlanSlot): string {
  const dayIndex = parseCalendarDate(slot.slot_date).getDay();
  return `${shortDayNames[dayIndex === 0 ? 6 : dayIndex - 1]}`;
}

function slotCardTitle(slot: PlanSlot): string {
  if (slot.slot_type === 'empty') {
    return 'Open slot';
  }
  if (slot.slot_type === 'takeout') {
    return 'Takeout';
  }
  if (slot.slot_type === 'leftover') {
    return `Leftovers: ${slot.title_snapshot}`;
  }
  return slot.title_snapshot;
}

function slotBadgeLabel(slot: PlanSlot): string {
  if (slot.slot_type === 'empty') {
    return 'Open';
  }
  if (slot.slot_type === 'takeout') {
    return 'Takeout';
  }
  if (slot.slot_type === 'leftover') {
    return 'Leftovers';
  }
  return 'Meal';
}

function slotInspectorSummary(slot: PlanSlot): string {
  if (slot.slot_type === 'empty') {
    return 'Choose a meal, reroll this day, or use discovery to fill it.';
  }
  if (slot.slot_type === 'takeout') {
    return 'This day is marked for takeout. Replace it with a meal or clear it.';
  }
  if (slot.slot_type === 'leftover') {
    return 'This day is currently using leftovers. You can choose a different source, replace it with a meal, or clear it.';
  }
  return 'Swap the meal, reroll the day, or record what happened after dinner.';
}

function mealOverridesFromForm(form: MealForm): MealSeasonalRecurrenceOverride[] {
  return seasonOptions.flatMap((season) => {
    const recurrenceTier = form.seasonal_recurrence_overrides[season.id];
    if (!recurrenceTier) {
      return [];
    }
    return [{ season: season.id, recurrence_tier: recurrenceTier }];
  });
}


function mealFormFromMeal(meal: Meal): MealForm {
  const seasonalOverrides = createDefaultSeasonalRecurrenceOverrides();
  for (const override of meal.seasonal_recurrence_overrides) {
    seasonalOverrides[override.season] = override.recurrence_tier;
  }
  return {
    title: meal.title,
    notes: meal.notes,
    complexity: meal.complexity,
    recurrence_tier: meal.recurrence_tier,
    seasonal_recurrence_overrides: seasonalOverrides,
    source_note: meal.source_note,
    source_url: meal.source_url,
    dietary_exclusions: meal.dietary_exclusions.join(', '),
    tags: meal.tags.map((tag) => tag.name).join(', '),
  };
}


function mealSeasonalOverrideSummary(meal: Meal): string | null {
  if (meal.seasonal_recurrence_overrides.length === 0) {
    return null;
  }
  const seasonLabels = Object.fromEntries(seasonOptions.map((season) => [season.id, season.label])) as Record<SeasonName, string>;
  return meal.seasonal_recurrence_overrides
    .map((override) => `${seasonLabels[override.season]}: ${override.recurrence_tier}`)
    .join(', ');
}


function mealPayloadFromForm(form: MealForm) {
  return {
    title: form.title,
    notes: form.notes,
    complexity: form.complexity,
    recurrence_tier: form.recurrence_tier,
    seasonal_recurrence_overrides: mealOverridesFromForm(form),
    source_note: form.source_note,
    source_url: form.source_url,
    dietary_exclusions: form.dietary_exclusions
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean),
    tags: form.tags
      .split(',')
      .map((value) => value.trim())
      .filter(Boolean),
  };
}

export function App() {
  const [authState, setAuthState] = useState<'loading' | 'anonymous' | 'authenticated'>('loading');
  const [activeView, setActiveView] = useState<DashboardView>('planner');
  const [session, setSession] = useState<MeResponse | null>(null);
  const [preferencesDraft, setPreferencesDraft] = useState<UserPreferences>(defaultPreferences);
  const [rulesDraft, setRulesDraft] = useState<RuleDraft[]>([]);
  const [meals, setMeals] = useState<Meal[]>([]);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [planHistory, setPlanHistory] = useState<PlanSummary[]>([]);
  const [previousPlan, setPreviousPlan] = useState<Plan | null>(null);
  const [tagSuggestions, setTagSuggestions] = useState<string[]>([]);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [mealForm, setMealForm] = useState<MealForm>(createDefaultMealForm);
  const [selectedMealId, setSelectedMealId] = useState<number | null>(null);
  const [bulkText, setBulkText] = useState('');
  const [mealFilter, setMealFilter] = useState({ complexity: '', tag: '' });
  const [draggedSlotId, setDraggedSlotId] = useState<number | null>(null);
  const [selectedSlotId, setSelectedSlotId] = useState<number | null>(null);
  const [selectedMealForSlot, setSelectedMealForSlot] = useState<Record<number, number | ''>>({});
  const [selectedLeftoverMealForSlot, setSelectedLeftoverMealForSlot] = useState<Record<number, number | ''>>({});
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'system'; message: string }>>([]);
  const [discoveryQuery, setDiscoveryQuery] = useState('');
  const [discoveryCandidates, setDiscoveryCandidates] = useState<DiscoveryCandidate[]>([]);
  const [emailPreview, setEmailPreview] = useState<EmailPreview | null>(null);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [viewedWeek, setViewedWeek] = useState<string | null>(() => parseWeekFromPath());
  const [timezoneDraft, setTimezoneDraft] = useState('UTC');

  async function syncPlanContext(nextPlan: Plan | null) {
    setPlan(nextPlan);
    if (!nextPlan) {
      setPreviousPlan(null);
      return;
    }
    try {
      const priorPlan = await api.getWeekPlan(shiftCalendarDate(nextPlan.week_start_date, -7));
      setPreviousPlan(priorPlan);
    } catch {
      setPreviousPlan(null);
    }
  }

  async function loadPlanView(targetWeek: string | null) {
    try {
      const planResponse = targetWeek ? await api.getWeekPlan(targetWeek) : await api.getCurrentPlan();
      await syncPlanContext(planResponse);
    } catch {
      setPlan(null);
      setPreviousPlan(null);
    }
  }

  async function loadDashboard(targetWeek: string | null) {
    const me = await api.getMe();
    const [mealsResponse, tags, history] = await Promise.all([api.listMeals(), api.getTagSuggestions(), api.listPlans()]);
    await loadPlanView(targetWeek);
    setSession(me);
    setTimezoneDraft(me.user.timezone ?? 'UTC');
    setPreferencesDraft(me.preferences);
    setRulesDraft(
      me.recurring_rules.map((rule) => ({
        day_of_week: rule.day_of_week,
        rule_type: rule.rule_type,
        rule_payload: rule.rule_payload,
        priority: rule.priority,
        active: rule.active,
      })),
    );
    setMeals(mealsResponse);
    setPlanHistory(history);
    setTagSuggestions(tags.map((tag) => tag.name));
    setAuthState('authenticated');
  }

  useEffect(() => {
    let active = true;
    api
      .authMe()
      .then(() => {
        if (!active) return;
        return loadDashboard(viewedWeek);
      })
      .catch(() => {
        if (!active) return;
        setAuthState('anonymous');
      });
    return () => {
      active = false;
    };
  }, []);

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
  }, [authState]);

  useEffect(() => {
    if (!plan) {
      if (selectedSlotId !== null) {
        setSelectedSlotId(null);
      }
      return;
    }

    const hasSelectedSlot = selectedSlotId !== null && plan.slots.some((slot) => slot.id === selectedSlotId);
    if (!hasSelectedSlot && plan.slots.length > 0) {
      setSelectedSlotId(plan.slots[0].id);
    }
  }, [plan, selectedSlotId]);

  function resetMessages() {
    setErrorMessage('');
    setStatusMessage('');
  }

  async function refreshMeals() {
    const mealsResponse = await api.listMeals({
      complexity: mealFilter.complexity || undefined,
      tag: mealFilter.tag || undefined,
    });
    setMeals(mealsResponse);
  }

  async function refreshPlan() {
    if (!plan) {
      return;
    }
    const nextPlan = await api.getWeekPlan(plan.week_start_date);
    await syncPlanContext(nextPlan);
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    resetMessages();
    try {
      await api.login(loginForm.email, loginForm.password);
      await loadDashboard(viewedWeek);
      setStatusMessage('Logged in.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to log in.');
    }
  }

  async function handleLogout() {
    resetMessages();
    try {
      await api.logout();
      setAuthState('anonymous');
      setSession(null);
      setPlan(null);
      setPlanHistory([]);
      setPreviousPlan(null);
      setMeals([]);
      setTimezoneDraft('UTC');
      setViewedWeek(null);
      syncBrowserWeekPath(null, 'replace');
      setStatusMessage('Logged out.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to log out.');
    }
  }

  async function handlePreferencesSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    resetMessages();
    try {
      const updatedPreferences = await api.updatePreferences({
        novel_meal_ratio: preferencesDraft.novel_meal_ratio,
        takeout_frequency_per_week: preferencesDraft.takeout_frequency_per_week,
        leftovers_per_week: preferencesDraft.leftovers_per_week,
        allow_simple: preferencesDraft.allow_simple,
        allow_intermediate: preferencesDraft.allow_intermediate,
        allow_complex: preferencesDraft.allow_complex,
        planning_guidance_text: preferencesDraft.planning_guidance_text,
        dietary_notes: preferencesDraft.dietary_notes,
        email_enabled: preferencesDraft.email_enabled,
        email_day_of_week: preferencesDraft.email_day_of_week,
        email_local_time: preferencesDraft.email_local_time,
        timezone: timezoneDraft,
      });
      const updatedRules = await api.replaceRecurringRules(rulesDraft);
      if (session) {
        setSession({
          ...session,
          user: {
            ...session.user,
            timezone: timezoneDraft,
          },
          preferences: updatedPreferences,
          recurring_rules: updatedRules,
        });
      }
      if (viewedWeek === null) {
        await loadPlanView(null);
      }
      setStatusMessage('Preferences saved.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save preferences.');
    }
  }

  async function handleMealSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    resetMessages();
    try {
      if (selectedMealId) {
        await api.updateMeal(selectedMealId, mealPayloadFromForm(mealForm));
        setStatusMessage('Meal updated.');
      } else {
        await api.createMeal(mealPayloadFromForm(mealForm));
        setStatusMessage('Meal added.');
      }
      setMealForm(createDefaultMealForm());
      setSelectedMealId(null);
      await refreshMeals();
      const tags = await api.getTagSuggestions();
      setTagSuggestions(tags.map((tag) => tag.name));
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save meal.');
    }
  }

  async function handleBulkAdd() {
    resetMessages();
    try {
      await api.bulkFastAdd(bulkText);
      setBulkText('');
      await refreshMeals();
      setStatusMessage('Fast-add complete.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to fast-add meals.');
    }
  }

  async function handleArchiveMeal(mealId: number) {
    resetMessages();
    try {
      await api.archiveMeal(mealId);
      await refreshMeals();
      setStatusMessage('Meal archived.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to archive meal.');
    }
  }

  async function handleExportMeals() {
    resetMessages();
    try {
      const csv = await api.exportMealsCsv();
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'fridgestare-meals.csv';
      link.click();
      URL.revokeObjectURL(url);
      setStatusMessage('CSV export generated.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to export meals.');
    }
  }

  async function handleGeneratePlan(forceRegenerate = false) {
    resetMessages();
    try {
      const nextPlan = await api.generatePlan(viewedWeek ?? undefined, forceRegenerate);
      const history = await api.listPlans();
      await syncPlanContext(nextPlan);
      setPlanHistory(history);
      setViewedWeek(nextPlan.week_start_date);
      syncBrowserWeekPath(nextPlan.week_start_date, 'replace');
      setStatusMessage('Weekly plan generated.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to generate plan.');
    }
  }

  async function applyPlanUpdate(updater: () => Promise<Plan>, successMessage: string) {
    resetMessages();
    try {
      const updatedPlan = await updater();
      await syncPlanContext(updatedPlan);
      setStatusMessage(successMessage);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to update the plan.');
    }
  }

  async function handleDrop(targetSlotId: number) {
    if (!plan || !draggedSlotId || draggedSlotId === targetSlotId) return;
    await applyPlanUpdate(
      () => api.moveSlot(plan.id, draggedSlotId, targetSlotId),
      'Slots rearranged.',
    );
    setDraggedSlotId(null);
  }

  async function handleSelectMealForSlot(slotId: number) {
    if (!plan) return;
    const mealId = selectedMealForSlot[slotId];
    if (!mealId) return;
    await applyPlanUpdate(
      () => api.setSlot(plan.id, { slot_id: slotId, meal_id: Number(mealId), slot_type: 'meal' }),
      'Slot updated.',
    );
  }

  async function handleMarkLeftover(slotId: number) {
    if (!plan) return;
    const mealId = selectedLeftoverMealForSlot[slotId];
    if (!mealId) return;
    await applyPlanUpdate(
      () => api.setSlot(plan.id, { slot_id: slotId, meal_id: Number(mealId), slot_type: 'leftover' }),
      'Slot marked as leftovers.',
    );
  }

  async function handleDiscoverySuggest() {
    resetMessages();
    try {
      const candidates = await api.suggestDiscovery(selectedSlotId, discoveryQuery);
      setDiscoveryCandidates(candidates);
      setStatusMessage(`Found ${candidates.length} discovery suggestion${candidates.length === 1 ? '' : 's'}.`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to fetch discovery suggestions.');
    }
  }

  async function handleAcceptDiscovery(candidateId: number) {
    if (!plan || !selectedSlotId) return;
    resetMessages();
    try {
      await api.acceptDiscovery(candidateId, { plan_id: plan.id, slot_id: selectedSlotId, apply_to_plan: true });
      await Promise.all([refreshMeals(), refreshPlan()]);
      setStatusMessage('Discovered recipe accepted into your library and plan.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to accept discovery suggestion.');
    }
  }

  async function handleChatSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!plan || !chatMessage.trim()) return;
    resetMessages();
    try {
      const response: ChatResponse = await api.chatPlan(plan.id, chatMessage.trim());
      await syncPlanContext(response.plan);
      setChatHistory((current) => [
        ...current,
        { role: 'user', message: chatMessage.trim() },
        { role: 'system', message: response.explanation },
      ]);
      setChatMessage('');
      setStatusMessage('Chat update applied.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to apply chat edit.');
    }
  }

  async function handleEmailPreview() {
    if (!plan) return;
    resetMessages();
    try {
      const preview = await api.previewEmail(plan.id);
      setEmailPreview(preview);
      setStatusMessage('Email preview refreshed.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to preview email.');
    }
  }

  async function handleSendEmail() {
    if (!plan) return;
    resetMessages();
    try {
      const response = await api.sendEmail(plan.id);
      setStatusMessage(`Email queued via ${response.delivery_mode}.`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to send email.');
    }
  }

  async function handleOpenWeek(weekStart: string) {
    resetMessages();
    setViewedWeek(weekStart);
    syncBrowserWeekPath(weekStart);
    await loadPlanView(weekStart);
  }

  async function handleOpenCurrentWeek() {
    resetMessages();
    setViewedWeek(null);
    syncBrowserWeekPath(null);
    await loadPlanView(null);
  }

  const filteredMeals = meals.filter((meal) => {
    const complexityMatches = !mealFilter.complexity || meal.complexity === mealFilter.complexity;
    const tagMatches = !mealFilter.tag || meal.tags.some((tag) => tag.name.includes(mealFilter.tag.toLowerCase()));
    return complexityMatches && tagMatches;
  });
  const selectedSlot = plan?.slots.find((slot) => slot.id === selectedSlotId) ?? null;
  const activeHistoryWeek = plan?.week_start_date ?? viewedWeek;
  const activeHistoryIndex = activeHistoryWeek
    ? planHistory.findIndex((summary) => summary.week_start_date === activeHistoryWeek)
    : -1;
  const latestSavedPlan = planHistory[0] ?? null;
  const newerSavedPlan = activeHistoryIndex > 0 ? planHistory[activeHistoryIndex - 1] : null;
  const olderSavedPlan = activeHistoryIndex >= 0 && activeHistoryIndex < planHistory.length - 1
    ? planHistory[activeHistoryIndex + 1]
    : null;
  const displayedWeek = plan?.week_start_date ?? viewedWeek;
  const activeWeekRange = displayedWeek ? formatWeekRange(displayedWeek) : 'No week selected';
  const leftoverOptions = useMemo(() => {
    if (!selectedSlot || !plan) {
      return [] as LeftoverOption[];
    }

    const optionsByMealId = new Map<number, LeftoverOption>();
    const earlierSlots = plan.slots.filter(
      (slot) => slot.slot_order < selectedSlot.slot_order && slot.meal_id !== null && slot.slot_type !== 'takeout' && slot.slot_type !== 'empty',
    );
    for (const slot of earlierSlots) {
      if (!slot.meal_id || optionsByMealId.has(slot.meal_id)) {
        continue;
      }
      optionsByMealId.set(slot.meal_id, {
        mealId: slot.meal_id,
        label: `Earlier this week · ${slotLabel(slot)} · ${slot.title_snapshot}`,
      });
    }

    for (const slot of previousPlan?.slots ?? []) {
      if (!slot.meal_id || slot.slot_type === 'takeout' || slot.slot_type === 'empty' || optionsByMealId.has(slot.meal_id)) {
        continue;
      }
      optionsByMealId.set(slot.meal_id, {
        mealId: slot.meal_id,
        label: `Last week · ${slotLabel(slot)} · ${slot.title_snapshot}`,
      });
    }

    return Array.from(optionsByMealId.values());
  }, [plan, previousPlan, selectedSlot]);

  if (authState === 'loading') {
    return (
      <main className="app-shell loading-shell">
        <section className="hero-panel">
          <p className="eyebrow">Fridgestare</p>
          <h1>Loading the kitchen radar.</h1>
        </section>
      </main>
    );
  }

  if (authState === 'anonymous') {
    return (
      <main className="app-shell login-shell">
        <section className="hero-panel">
          <p className="eyebrow">Fridgestare</p>
          <h1>Dinners, remembered.</h1>
          <p className="lede">
            Plan a week, drag meals around, reroll a slot, ask for soup on Tuesday,
            and send yourself a tidy summary before the store run.
          </p>
        </section>
        <section className="status-panel auth-card">
          <h2>Sign in</h2>
          <form className="stacked-form" onSubmit={handleLogin}>
            <label>
              <span>Email</span>
              <input
                type="email"
                value={loginForm.email}
                onChange={(event) => setLoginForm((current) => ({ ...current, email: event.target.value }))}
                required
              />
            </label>
            <label>
              <span>Password</span>
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm((current) => ({ ...current, password: event.target.value }))}
                required
              />
            </label>
            <button type="submit">Enter the pantry</button>
          </form>
          {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Fridgestare</p>
          <h1>Weekly meal calendar</h1>
          <p className="subtle-copy">
            {session?.user.email} · {activeWeekRange}
          </p>
        </div>
        <div className="topbar-actions">
          <button onClick={() => void handleGeneratePlan(false)}>Generate week</button>
          <button className="secondary-button" onClick={() => void handleGeneratePlan(true)}>Regenerate</button>
          <button className="secondary-button" onClick={() => void handleLogout()}>Log out</button>
        </div>
      </header>

      {statusMessage ? <p className="status-banner">{statusMessage}</p> : null}
      {errorMessage ? <p className="error-banner">{errorMessage}</p> : null}

      <section className="dashboard-nav" role="tablist" aria-label="Workspace sections">
        {dashboardViews.map((view) => {
          const isActive = activeView === view.id;
          return (
            <button
              key={view.id}
              id={`${view.id}-tab`}
              className={`view-tab ${isActive ? 'is-active' : ''}`}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`${view.id}-panel`}
              onClick={() => setActiveView(view.id)}
            >
              <span>{view.label}</span>
              <small>{view.description}</small>
            </button>
          );
        })}
      </section>

      <section className="dashboard-content">
        {activeView === 'preferences' ? (
          <section className="single-panel-layout" role="tabpanel" id="preferences-panel" aria-labelledby="preferences-tab">
            <section className="panel preferences-panel">
          <div className="panel-header">
            <h2>Preferences</h2>
            <p>Set planning guidance, complexity limits, email timing, and recurring rules.</p>
          </div>
          <form className="stacked-form" onSubmit={handlePreferencesSave}>
            <label>
              <span>Guidance</span>
              <textarea
                value={preferencesDraft.planning_guidance_text}
                onChange={(event) =>
                  setPreferencesDraft((current) => ({ ...current, planning_guidance_text: event.target.value }))
                }
                rows={3}
              />
            </label>
            <label>
              <span>Dietary notes</span>
              <textarea
                value={preferencesDraft.dietary_notes}
                onChange={(event) => setPreferencesDraft((current) => ({ ...current, dietary_notes: event.target.value }))}
                rows={2}
              />
            </label>
            <div className="form-grid compact-grid">
              <label>
                <span>Novel meal ratio</span>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  value={preferencesDraft.novel_meal_ratio}
                  onChange={(event) =>
                    setPreferencesDraft((current) => ({ ...current, novel_meal_ratio: Number(event.target.value) }))
                  }
                />
              </label>
              <label>
                <span>Takeout per week</span>
                <input
                  type="number"
                  min="0"
                  max="7"
                  step="1"
                  value={preferencesDraft.takeout_frequency_per_week}
                  onChange={(event) =>
                    setPreferencesDraft((current) => ({ ...current, takeout_frequency_per_week: Number(event.target.value) }))
                  }
                />
              </label>
              <label>
                <span>Leftovers per week</span>
                <input
                  type="number"
                  min="0"
                  max="7"
                  step="1"
                  value={preferencesDraft.leftovers_per_week}
                  onChange={(event) =>
                    setPreferencesDraft((current) => ({ ...current, leftovers_per_week: Number(event.target.value) }))
                  }
                />
              </label>
              <label>
                <span>Planning timezone</span>
                <input
                  value={timezoneDraft}
                  onChange={(event) => setTimezoneDraft(event.target.value)}
                  placeholder="America/Los_Angeles"
                />
              </label>
              <label>
                <span>Email day</span>
                <select
                  value={preferencesDraft.email_day_of_week}
                  onChange={(event) =>
                    setPreferencesDraft((current) => ({ ...current, email_day_of_week: Number(event.target.value) }))
                  }
                >
                  {dayNames.map((day, index) => (
                    <option key={day} value={index}>
                      {day}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>Email time</span>
                <input
                  type="time"
                  value={preferencesDraft.email_local_time.slice(0, 5)}
                  onChange={(event) =>
                    setPreferencesDraft((current) => ({ ...current, email_local_time: `${event.target.value}:00` }))
                  }
                />
              </label>
            </div>
            <div className="checkbox-row">
              <label className="checkbox-option"><input type="checkbox" checked={preferencesDraft.allow_simple} onChange={(event) => setPreferencesDraft((current) => ({ ...current, allow_simple: event.target.checked }))} /><span>Simple meals</span></label>
              <label className="checkbox-option"><input type="checkbox" checked={preferencesDraft.allow_intermediate} onChange={(event) => setPreferencesDraft((current) => ({ ...current, allow_intermediate: event.target.checked }))} /><span>Intermediate meals</span></label>
              <label className="checkbox-option"><input type="checkbox" checked={preferencesDraft.allow_complex} onChange={(event) => setPreferencesDraft((current) => ({ ...current, allow_complex: event.target.checked }))} /><span>Complex meals</span></label>
              <label className="checkbox-option"><input type="checkbox" checked={preferencesDraft.email_enabled} onChange={(event) => setPreferencesDraft((current) => ({ ...current, email_enabled: event.target.checked }))} /><span>Weekly email summary</span></label>
            </div>

            <div className="panel-subsection">
              <div className="section-header-inline">
                <h3>Recurring rules</h3>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() =>
                    setRulesDraft((current) => [
                      ...current,
                      { day_of_week: 0, rule_type: 'prefer_tag', rule_payload: { tag: 'soup' }, priority: 100, active: true },
                    ])
                  }
                >
                  Add rule
                </button>
              </div>
              <div className="rule-stack">
                {rulesDraft.map((rule, index) => (
                  <div key={`${rule.rule_type}-${index}`} className="rule-card">
                    <select
                      value={rule.day_of_week}
                      onChange={(event) =>
                        setRulesDraft((current) =>
                          current.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, day_of_week: Number(event.target.value) } : item,
                          ),
                        )
                      }
                    >
                      {dayNames.map((day, dayIndex) => (
                        <option key={day} value={dayIndex}>
                          {day}
                        </option>
                      ))}
                    </select>
                    <select
                      value={rule.rule_type}
                      onChange={(event) =>
                        setRulesDraft((current) =>
                          current.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, rule_type: event.target.value } : item,
                          ),
                        )
                      }
                    >
                      <option value="prefer_tag">Prefer tag</option>
                      <option value="must_include_tag">Must include tag</option>
                      <option value="takeout">Takeout</option>
                      <option value="avoid_complex">Avoid complex</option>
                    </select>
                    <input
                      type="text"
                      value={String(rule.rule_payload.tag ?? '')}
                      placeholder="tag payload"
                      onChange={(event) =>
                        setRulesDraft((current) =>
                          current.map((item, itemIndex) =>
                            itemIndex === index
                              ? { ...item, rule_payload: event.target.value ? { tag: event.target.value } : {} }
                              : item,
                          ),
                        )
                      }
                      disabled={rule.rule_type === 'takeout' || rule.rule_type === 'avoid_complex'}
                    />
                    <button
                      className="ghost-button"
                      type="button"
                      onClick={() => setRulesDraft((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <button type="submit">Save preferences</button>
          </form>
            </section>
          </section>
        ) : null}

        {activeView === 'meals' ? (
          <section className="single-panel-layout" role="tabpanel" id="meals-panel" aria-labelledby="meals-tab">
            <section className="panel meals-panel">
          <div className="panel-header">
            <h2>Meal library</h2>
            <p>Add new dinners, edit metadata, fast-enter a backlog, and export CSV.</p>
          </div>
          <div className="form-grid compact-grid">
            <label>
              <span>Filter by complexity</span>
              <select
                value={mealFilter.complexity}
                onChange={(event) => setMealFilter((current) => ({ ...current, complexity: event.target.value }))}
              >
                <option value="">All</option>
                <option value="simple">Simple</option>
                <option value="intermediate">Intermediate</option>
                <option value="complex">Complex</option>
              </select>
            </label>
            <label>
              <span>Filter by tag</span>
              <input
                value={mealFilter.tag}
                onChange={(event) => setMealFilter((current) => ({ ...current, tag: event.target.value }))}
                placeholder="soup, tacos, cozy"
              />
            </label>
            <button className="secondary-button" type="button" onClick={() => void refreshMeals()}>
              Apply filters
            </button>
            <button className="secondary-button" type="button" onClick={() => void handleExportMeals()}>
              Export CSV
            </button>
          </div>

          <form className="stacked-form" onSubmit={handleMealSubmit}>
            <div className="section-header-inline">
              <h3>{selectedMealId ? 'Edit meal' : 'Add meal'}</h3>
              {selectedMealId ? (
                <button className="ghost-button" type="button" onClick={() => { setSelectedMealId(null); setMealForm(createDefaultMealForm()); }}>
                  Clear
                </button>
              ) : null}
            </div>
            <div className="form-grid">
              <label><span>Title</span><input value={mealForm.title} onChange={(event) => setMealForm((current) => ({ ...current, title: event.target.value }))} required /></label>
              <label><span>Complexity</span><select value={mealForm.complexity} onChange={(event) => setMealForm((current) => ({ ...current, complexity: event.target.value }))}><option value="simple">Simple</option><option value="intermediate">Intermediate</option><option value="complex">Complex</option></select></label>
              <label>
                <span>Base recurrence</span>
                <select value={mealForm.recurrence_tier} onChange={(event) => setMealForm((current) => ({ ...current, recurrence_tier: event.target.value as RecurrenceTier }))}>
                  {recurrenceOptions.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
              <label><span>Tags</span><input value={mealForm.tags} onChange={(event) => setMealForm((current) => ({ ...current, tags: event.target.value }))} placeholder={tagSuggestions.slice(0, 5).join(', ')} /></label>
              <label><span>Dietary exclusions</span><input value={mealForm.dietary_exclusions} onChange={(event) => setMealForm((current) => ({ ...current, dietary_exclusions: event.target.value }))} placeholder="mushrooms, gluten" /></label>
              <label><span>Source note</span><input value={mealForm.source_note} onChange={(event) => setMealForm((current) => ({ ...current, source_note: event.target.value }))} /></label>
              <label><span>Source URL</span><input value={mealForm.source_url} onChange={(event) => setMealForm((current) => ({ ...current, source_url: event.target.value }))} /></label>
            </div>
            <div className="form-grid compact-grid">
              {seasonOptions.map((season) => (
                <label key={season.id}>
                  <span>{season.label} override</span>
                  <select
                    value={mealForm.seasonal_recurrence_overrides[season.id]}
                    onChange={(event) => setMealForm((current) => ({
                      ...current,
                      seasonal_recurrence_overrides: {
                        ...current.seasonal_recurrence_overrides,
                        [season.id]: event.target.value as '' | RecurrenceTier,
                      },
                    }))}
                  >
                    <option value="">Use base</option>
                    {recurrenceOptions.map((option) => (
                      <option key={option.value} value={option.value}>{option.label}</option>
                    ))}
                  </select>
                </label>
              ))}
            </div>
            <label>
              <span>Notes</span>
              <textarea value={mealForm.notes} onChange={(event) => setMealForm((current) => ({ ...current, notes: event.target.value }))} rows={2} />
            </label>
            <button type="submit">{selectedMealId ? 'Update meal' : 'Add meal'}</button>
          </form>

          <div className="panel-subsection">
            <div className="section-header-inline">
              <h3>Bulk fast-add</h3>
              <button className="secondary-button" type="button" onClick={() => void handleBulkAdd()}>Fast-add list</button>
            </div>
            <textarea
              value={bulkText}
              onChange={(event) => setBulkText(event.target.value)}
              rows={4}
              placeholder="One meal title per line"
            />
          </div>

          <div className="meal-list">
            {filteredMeals.map((meal) => (
              <article key={meal.id} className="meal-card">
                <div>
                  <h3>{meal.title}</h3>
                  <p>{meal.notes || 'No notes yet.'}</p>
                  {mealSeasonalOverrideSummary(meal) ? <p>Seasonal overrides: {mealSeasonalOverrideSummary(meal)}</p> : null}
                  <div className="chip-row">
                    <span className="chip">{meal.complexity}</span>
                    <span className="chip">{meal.recurrence_tier}</span>
                    {meal.tags.map((tag) => (
                      <span key={tag.id} className="chip">{tag.name}</span>
                    ))}
                    {meal.agent_sourced ? <span className="chip accent-chip">agent sourced</span> : null}
                  </div>
                </div>
                <div className="card-actions">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => {
                      setSelectedMealId(meal.id);
                      setMealForm(mealFormFromMeal(meal));
                    }}
                  >
                    Edit
                  </button>
                  <button className="ghost-button" type="button" onClick={() => void handleArchiveMeal(meal.id)}>
                    Archive
                  </button>
                </div>
              </article>
            ))}
          </div>
            </section>
          </section>
        ) : null}

        {activeView === 'planner' ? (
          <section className="planner-layout" role="tabpanel" id="planner-panel" aria-labelledby="planner-tab">
            <section className="panel planner-panel">
              <div className="panel-header planner-header">
                <div>
                  <p className="section-kicker">Planner</p>
                  <h2>Week at a glance</h2>
                  <p className="planner-range">{activeWeekRange}</p>
                </div>
                {plan ? <span className="selection-pill">{plan.slots.length} days planned</span> : null}
              </div>

              <div className="planner-toolbar">
                <button className="secondary-button" type="button" onClick={() => void handleOpenCurrentWeek()} disabled={viewedWeek === null}>
                  Current week
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => {
                    if (newerSavedPlan) {
                      void handleOpenWeek(newerSavedPlan.week_start_date);
                    }
                  }}
                  disabled={!newerSavedPlan}
                >
                  Newer saved week
                </button>
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => {
                    if (olderSavedPlan) {
                      void handleOpenWeek(olderSavedPlan.week_start_date);
                    }
                  }}
                  disabled={!olderSavedPlan}
                >
                  Older saved week
                </button>
                <span className="subtle-copy">
                  {plan
                    ? `Saved week ${activeHistoryIndex + 1} of ${planHistory.length}.`
                    : planHistory.length
                      ? `${planHistory.length} saved week${planHistory.length === 1 ? '' : 's'} available.`
                      : 'No saved weeks yet.'}
                </span>
              </div>

              {plan ? (
                <>
                  <div className="planner-toolbar">
                    <button className="secondary-button" type="button" onClick={() => void applyPlanUpdate(() => api.undoPlan(plan.id), 'Last change undone.')}>Undo last action</button>
                    <button className="secondary-button" type="button" onClick={() => void handleEmailPreview()}>Preview email</button>
                    <button className="secondary-button" type="button" onClick={() => void handleSendEmail()}>Send email</button>
                  </div>
                  <div className="planner-board">
                    {plan.slots.map((slot) => (
                      <article
                        key={slot.id}
                        className={`slot-card slot-type-${slot.slot_type} ${selectedSlotId === slot.id ? 'slot-selected' : ''}`}
                        draggable
                        onClick={() => setSelectedSlotId(slot.id)}
                        onDragStart={() => setDraggedSlotId(slot.id)}
                        onDragOver={(event) => event.preventDefault()}
                        onDrop={() => void handleDrop(slot.id)}
                      >
                        <div className="slot-calendar-row">
                          <div className="slot-calendar-copy">
                            <p className="slot-day">{slotCalendarLabel(slot)}</p>
                            <p className="slot-date-inline">{formatMonthLabel(slot.slot_date)}</p>
                          </div>
                          <div className="slot-date-number">{formatDayNumber(slot.slot_date)}</div>
                        </div>
                        <div className="slot-body">
                          <h3>{slotCardTitle(slot)}</h3>
                          {slot.notes_snapshot ? <p className="slot-note">{slot.notes_snapshot}</p> : null}
                        </div>
                        <div className="slot-footer">
                          <span className="slot-type-pill">{slotBadgeLabel(slot)}</span>
                          {slot.outcome_status ? <span className="outcome-pill">{slot.outcome_status}</span> : null}
                          {selectedSlotId === slot.id ? <span className="slot-focus-pill">Selected</span> : null}
                        </div>
                      </article>
                    ))}
                  </div>
                </>
              ) : (
                <div className="empty-state">
                  <p>No weekly plan exists yet for this planning week.</p>
                  <button type="button" onClick={() => void handleGeneratePlan(false)}>Generate a plan</button>
                  {latestSavedPlan ? (
                    <button className="secondary-button" type="button" onClick={() => void handleOpenWeek(latestSavedPlan.week_start_date)}>
                      Open latest saved week
                    </button>
                  ) : null}
                </div>
              )}
            </section>

            <section className="panel side-panel">
              <div className="panel-header">
                <h2>Day details</h2>
                <p>Keep one day in focus while you swap meals, reroll, discover something new, or log the outcome.</p>
              </div>

              <div className="panel-subsection slot-inspector">
                <div className="section-header-inline">
                  <h3>{selectedSlot ? `${slotLabel(selectedSlot)} details` : 'Choose a day'}</h3>
                  {selectedSlot ? <span className="selection-pill">{slotCardTitle(selectedSlot)}</span> : null}
                </div>
                {plan && selectedSlot ? (
                  <>
                    <p className="slot-meta">{formatDate(selectedSlot.slot_date)}</p>
                    <p className="slot-reason">{slotInspectorSummary(selectedSlot)}</p>
                    <label>
                      <span>Replace with a library meal</span>
                      <div className="inline-select-row">
                        <select
                          value={selectedMealForSlot[selectedSlot.id] ?? ''}
                          onChange={(event) => setSelectedMealForSlot((current) => ({ ...current, [selectedSlot.id]: event.target.value ? Number(event.target.value) : '' }))}
                        >
                          <option value="">Choose a meal...</option>
                          {meals.map((meal) => (
                            <option key={meal.id} value={meal.id}>{meal.title}</option>
                          ))}
                        </select>
                        <button className="secondary-button" type="button" onClick={() => void handleSelectMealForSlot(selectedSlot.id)}>Set meal</button>
                      </div>
                    </label>
                    <label>
                      <span>Mark as leftovers from earlier this week or last week</span>
                      <div className="inline-select-row">
                        <select
                          value={selectedLeftoverMealForSlot[selectedSlot.id] ?? ''}
                          onChange={(event) =>
                            setSelectedLeftoverMealForSlot((current) => ({
                              ...current,
                              [selectedSlot.id]: event.target.value ? Number(event.target.value) : '',
                            }))
                          }
                          disabled={leftoverOptions.length === 0}
                        >
                          <option value="">{leftoverOptions.length ? 'Choose a leftover source...' : 'No earlier meals available yet'}</option>
                          {leftoverOptions.map((option) => (
                            <option key={option.mealId} value={option.mealId}>{option.label}</option>
                          ))}
                        </select>
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => void handleMarkLeftover(selectedSlot.id)}
                          disabled={leftoverOptions.length === 0}
                        >
                          Mark leftover
                        </button>
                      </div>
                    </label>
                    <div className="slot-actions inspector-actions">
                      <button className="secondary-button" type="button" onClick={() => void applyPlanUpdate(() => api.rerollSlot(plan.id, selectedSlot.id), 'Slot rerolled.')}>Reroll</button>
                      <button className="secondary-button" type="button" onClick={() => void applyPlanUpdate(() => api.setSlot(plan.id, { slot_id: selectedSlot.id, slot_type: 'takeout' }), 'Slot marked as takeout.')}>Takeout</button>
                      <button className="secondary-button" type="button" onClick={() => void applyPlanUpdate(() => api.setSlot(plan.id, { slot_id: selectedSlot.id, slot_type: 'empty' }), 'Slot cleared.')}>Clear slot</button>
                    </div>
                    <div className="slot-actions compact-row inspector-actions">
                      <button className="ghost-button" type="button" onClick={() => void applyPlanUpdate(() => api.updateOutcome(plan.id, selectedSlot.id, 'cooked'), 'Outcome marked cooked.')}>Cooked</button>
                      <button className="ghost-button" type="button" onClick={() => void applyPlanUpdate(() => api.updateOutcome(plan.id, selectedSlot.id, 'skipped'), 'Outcome marked skipped.')}>Skipped</button>
                      <button className="ghost-button" type="button" onClick={() => void applyPlanUpdate(() => api.updateOutcome(plan.id, selectedSlot.id, null), 'Outcome cleared.')}>Clear outcome</button>
                    </div>
                    {selectedSlot.outcome_status ? <p className="slot-outcome">Outcome: {selectedSlot.outcome_status}</p> : null}
                  </>
                ) : (
                  <p className="subtle-copy">Select a day in the planner to unlock meal replacement, discovery, and outcome controls.</p>
                )}
              </div>

              <div className="panel-subsection">
                <div className="section-header-inline">
                  <h3>{selectedSlot ? `Discovery for ${slotLabel(selectedSlot)}` : 'Discovery'}</h3>
                  <span className="subtle-copy">{selectedSlot ? slotCardTitle(selectedSlot) : 'Select a slot to target discovery'}</span>
                </div>
                <label>
                  <span>Discovery prompt</span>
                  <input
                    value={discoveryQuery}
                    onChange={(event) => setDiscoveryQuery(event.target.value)}
                    placeholder="easy vegetarian soup"
                    disabled={!selectedSlot}
                  />
                </label>
                <button type="button" onClick={() => void handleDiscoverySuggest()} disabled={!selectedSlotId}>
                  Suggest discovered meals
                </button>
                <div className="discovery-list">
                  {discoveryCandidates.map((candidate) => (
                    <article key={candidate.id} className="discovery-card">
                      <div>
                        <h3>{candidate.title}</h3>
                        <p>{candidate.summary}</p>
                        <p className="slot-meta">{candidate.complexity} · <a href={candidate.source_url} target="_blank" rel="noreferrer">source</a></p>
                        <p className="slot-reason">{candidate.reasoning}</p>
                      </div>
                      <button type="button" onClick={() => void handleAcceptDiscovery(candidate.id)}>Accept into library and slot</button>
                    </article>
                  ))}
                </div>
              </div>

              <form className="stacked-form" onSubmit={handleChatSubmit}>
                <label>
                  <span>Chat with the planner</span>
                  <textarea
                    value={chatMessage}
                    onChange={(event) => setChatMessage(event.target.value)}
                    rows={3}
                    placeholder="Put a soup on Tuesday, swap Wednesday and Thursday, make Friday simpler..."
                  />
                </label>
                <button type="submit" disabled={!plan}>Send chat edit</button>
              </form>
              <div className="chat-history">
                {chatHistory.map((entry, index) => (
                  <article key={`${entry.role}-${index}`} className={`chat-bubble ${entry.role}`}>
                    <strong>{entry.role === 'user' ? 'You' : 'Planner'}</strong>
                    <p>{entry.message}</p>
                  </article>
                ))}
              </div>

              <div className="panel-subsection">
                <div className="section-header-inline">
                  <h3>Email preview</h3>
                  {emailPreview ? <span className="subtle-copy">{emailPreview.delivery_mode}</span> : null}
                </div>
                {emailPreview ? (
                  <>
                    <p className="slot-meta">{emailPreview.subject}</p>
                    <div className="email-preview" dangerouslySetInnerHTML={{ __html: emailPreview.html }} />
                  </>
                ) : (
                  <p className="subtle-copy">Preview the weekly summary email from the planner panel.</p>
                )}
              </div>
            </section>
          </section>
        ) : null}
      </section>
    </main>
  );
}

export default App;
