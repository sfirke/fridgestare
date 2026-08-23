import type {
  Meal,
  MealComplexity,
  MealSeasonalRecurrenceOverride,
  RecurrenceTier,
  SeasonName,
} from '../types/api';

export const seasonOptions: Array<{ id: SeasonName; label: string }> = [
  { id: 'winter', label: 'Winter' },
  { id: 'spring', label: 'Spring' },
  { id: 'summer', label: 'Summer' },
  { id: 'fall', label: 'Fall' },
];

export const recurrenceOptions: Array<{ value: RecurrenceTier; label: string }> = [
  { value: 'staple', label: 'Staple' },
  { value: 'regular', label: 'Regular' },
  { value: 'treat', label: 'Treat' },
  { value: 'none', label: 'None' },
];

export const complexityOptions: Array<{ value: MealComplexity; label: string }> = [
  { value: 'simple', label: 'Simple' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'complex', label: 'Complex' },
];

export type MealFormSeasonalOverrides = Record<SeasonName, '' | RecurrenceTier>;

export type MealForm = {
  title: string;
  notes: string;
  complexity: MealComplexity;
  recurrence_tier: RecurrenceTier;
  seasonal_recurrence_overrides: MealFormSeasonalOverrides;
  source_note: string;
  source_url: string;
  dietary_exclusions: string;
  tags: string;
};

export function createDefaultSeasonalRecurrenceOverrides(): MealFormSeasonalOverrides {
  return { winter: '', spring: '', summer: '', fall: '' };
}

export function createDefaultMealForm(): MealForm {
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

export function mealFormFromMeal(meal: Meal): MealForm {
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

function splitCommaList(value: string): string[] {
  return value
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function overridesFromForm(form: MealForm): MealSeasonalRecurrenceOverride[] {
  return seasonOptions.flatMap((season) => {
    const recurrenceTier = form.seasonal_recurrence_overrides[season.id];
    return recurrenceTier ? [{ season: season.id, recurrence_tier: recurrenceTier }] : [];
  });
}

export function mealPayloadFromForm(form: MealForm) {
  return {
    title: form.title,
    notes: form.notes,
    complexity: form.complexity,
    recurrence_tier: form.recurrence_tier,
    seasonal_recurrence_overrides: overridesFromForm(form),
    source_note: form.source_note,
    source_url: form.source_url,
    dietary_exclusions: splitCommaList(form.dietary_exclusions),
    tags: splitCommaList(form.tags),
  };
}

export function mealSeasonalOverrideSummary(meal: Meal): string | null {
  if (meal.seasonal_recurrence_overrides.length === 0) {
    return null;
  }
  const seasonLabels = new Map(seasonOptions.map((season) => [season.id, season.label]));
  return meal.seasonal_recurrence_overrides
    .map((override) => `${seasonLabels.get(override.season)}: ${override.recurrence_tier}`)
    .join(', ');
}
