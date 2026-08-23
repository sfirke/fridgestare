import type { Plan, PlanSlot } from '../types/api';
import { dayNames, shortDayNames, weekdayIndex } from './dates';

export type LeftoverOption = {
  mealId: number;
  label: string;
};

/** Slot types that can be reused as a leftover source. */
const REUSABLE_SLOT_TYPES = new Set(['meal', 'leftover']);

export function slotLabel(slot: PlanSlot): string {
  return dayNames[weekdayIndex(slot.slot_date)];
}

export function slotCalendarLabel(slot: PlanSlot): string {
  return shortDayNames[weekdayIndex(slot.slot_date)];
}

export function slotCardTitle(slot: PlanSlot): string {
  switch (slot.slot_type) {
    case 'empty':
      return 'Open slot';
    case 'takeout':
      return 'Takeout';
    case 'leftover':
      return `Leftovers: ${slot.title_snapshot}`;
    default:
      return slot.title_snapshot;
  }
}

export function slotBadgeLabel(slot: PlanSlot): string {
  switch (slot.slot_type) {
    case 'empty':
      return 'Open';
    case 'takeout':
      return 'Takeout';
    case 'leftover':
      return 'Leftovers';
    default:
      return 'Meal';
  }
}

export function slotInspectorSummary(slot: PlanSlot): string {
  switch (slot.slot_type) {
    case 'empty':
      return 'Choose a meal, reroll this day, or use discovery to fill it.';
    case 'takeout':
      return 'This day is marked for takeout. Replace it with a meal or clear it.';
    case 'leftover':
      return 'This day is currently using leftovers. You can choose a different source, replace it with a meal, or clear it.';
    default:
      return 'Swap the meal, reroll the day, or record what happened after dinner.';
  }
}

/**
 * Meals that could plausibly still be in the fridge for the selected day: anything
 * cooked earlier in the same week, then anything from the previous week.
 */
export function buildLeftoverOptions(
  plan: Plan | null,
  previousPlan: Plan | null,
  selectedSlot: PlanSlot | null,
): LeftoverOption[] {
  if (!plan || !selectedSlot) {
    return [];
  }

  const optionsByMealId = new Map<number, LeftoverOption>();

  const addOption = (slot: PlanSlot, prefix: string) => {
    if (slot.meal_id === null || !REUSABLE_SLOT_TYPES.has(slot.slot_type)) {
      return;
    }
    if (optionsByMealId.has(slot.meal_id)) {
      return;
    }
    optionsByMealId.set(slot.meal_id, {
      mealId: slot.meal_id,
      label: `${prefix} · ${slotLabel(slot)} · ${slot.title_snapshot}`,
    });
  };

  for (const slot of plan.slots) {
    if (slot.slot_order < selectedSlot.slot_order) {
      addOption(slot, 'Earlier this week');
    }
  }
  for (const slot of previousPlan?.slots ?? []) {
    addOption(slot, 'Last week');
  }

  return Array.from(optionsByMealId.values());
}
