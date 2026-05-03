export type User = {
  id: number;
  email: string;
  timezone: string;
  week_starts_on: number;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type UserPreferences = {
  novel_meal_ratio: number;
  takeout_frequency_per_week: number;
  allow_simple: boolean;
  allow_intermediate: boolean;
  allow_complex: boolean;
  planning_guidance_text: string;
  dietary_notes: string;
  email_enabled: boolean;
  email_day_of_week: number;
  email_local_time: string;
  updated_at: string;
};

export type RecurringRule = {
  id: number;
  day_of_week: number;
  rule_type: string;
  rule_payload: Record<string, unknown>;
  priority: number;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type MeResponse = {
  user: User;
  preferences: UserPreferences;
  recurring_rules: RecurringRule[];
};

export type LoginResponse = {
  me: MeResponse;
};

export type MealTag = {
  id: number;
  name: string;
};

export type Meal = {
  id: number;
  title: string;
  notes: string;
  meal_type: string;
  complexity: string;
  recurrence_tier: string;
  seasonality_mode: string;
  dietary_exclusions: string[];
  source_note: string;
  source_url: string;
  agent_sourced: boolean;
  is_archived: boolean;
  tags: MealTag[];
  created_at: string;
  updated_at: string;
};

export type PlanSlot = {
  id: number;
  slot_date: string;
  slot_order: number;
  slot_type: string;
  meal_id: number | null;
  discovered_candidate_id: number | null;
  title_snapshot: string;
  notes_snapshot: string;
  selection_reason: string;
  outcome_status: string | null;
  outcome_logged_at: string | null;
};

export type Plan = {
  id: number;
  week_start_date: string;
  status: string;
  generation_source: string;
  planner_explanation: string;
  slots: PlanSlot[];
};

export type DiscoveryCandidate = {
  id: number;
  title: string;
  summary: string;
  source_url: string;
  complexity: string;
  reasoning: string;
  accepted_meal_id: number | null;
  created_at: string;
};

export type ChatResponse = {
  plan: Plan;
  explanation: string;
};

export type EmailPreview = {
  subject: string;
  html: string;
  delivery_mode: string;
};

export type EmailSendResponse = {
  status: string;
  delivery_mode: string;
};
