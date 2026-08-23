export const dayNames = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
];

export const shortDayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

/**
 * Parse a plain `YYYY-MM-DD` as a local calendar date.
 *
 * `new Date('2026-05-04')` parses as UTC midnight, which renders as the previous day
 * for anyone west of Greenwich, so date-only strings are split by hand.
 */
export function parseCalendarDate(dateString: string): Date {
  if (/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    const [year, month, day] = dateString.split('-').map(Number);
    return new Date(year, month - 1, day);
  }

  return new Date(dateString);
}

export function formatCalendarDateKey(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function shiftCalendarDate(dateString: string, dayOffset: number): string {
  const shifted = parseCalendarDate(dateString);
  shifted.setDate(shifted.getDate() + dayOffset);
  return formatCalendarDateKey(shifted);
}

/** Monday-first weekday index, matching `dayNames` and the backend's day_of_week. */
export function weekdayIndex(dateString: string): number {
  const sundayFirstIndex = parseCalendarDate(dateString).getDay();
  return sundayFirstIndex === 0 ? 6 : sundayFirstIndex - 1;
}

export function formatDate(dateString: string): string {
  return parseCalendarDate(dateString).toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

export function formatShortDate(dateString: string): string {
  return parseCalendarDate(dateString).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
  });
}

export function formatMonthLabel(dateString: string): string {
  return parseCalendarDate(dateString).toLocaleDateString(undefined, { month: 'short' });
}

export function formatDayNumber(dateString: string): string {
  return parseCalendarDate(dateString).toLocaleDateString(undefined, { day: 'numeric' });
}

export function formatWeekRange(weekStart: string): string {
  const end = parseCalendarDate(weekStart);
  end.setDate(end.getDate() + 6);
  return `${formatShortDate(weekStart)} - ${formatShortDate(formatCalendarDateKey(end))}`;
}
