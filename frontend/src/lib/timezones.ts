/**
 * Planning timezones offered in preferences.
 *
 * A free-text field here was a footgun: a typo is only caught server-side, and the
 * value silently decides which calendar week "this week" means. The backend still
 * accepts any valid IANA zone, so an account configured elsewhere keeps working —
 * `timezoneOptionsFor` keeps such a value selectable rather than resetting it.
 */
export const DEFAULT_TIMEZONE = 'America/New_York';

export type TimezoneOption = {
  value: string;
  label: string;
};

export const timezoneOptions: TimezoneOption[] = [
  { value: 'America/New_York', label: 'US Eastern (New York)' },
  { value: 'America/Chicago', label: 'US Central (Chicago)' },
  { value: 'America/Denver', label: 'US Mountain (Denver)' },
  { value: 'America/Phoenix', label: 'US Mountain, no DST (Phoenix)' },
  { value: 'America/Los_Angeles', label: 'US Pacific (Los Angeles)' },
  { value: 'America/Anchorage', label: 'US Alaska (Anchorage)' },
  { value: 'Pacific/Honolulu', label: 'US Hawaii (Honolulu)' },
  { value: 'America/Toronto', label: 'Canada Eastern (Toronto)' },
  { value: 'America/Vancouver', label: 'Canada Pacific (Vancouver)' },
  { value: 'Europe/London', label: 'UK (London)' },
  { value: 'Europe/Dublin', label: 'Ireland (Dublin)' },
  { value: 'Europe/Paris', label: 'Central Europe (Paris)' },
  { value: 'Europe/Berlin', label: 'Central Europe (Berlin)' },
  { value: 'Australia/Sydney', label: 'Australia Eastern (Sydney)' },
  { value: 'Pacific/Auckland', label: 'New Zealand (Auckland)' },
  { value: 'UTC', label: 'UTC' },
];

/** The option list, plus the account's current zone if it is not one of the presets. */
export function timezoneOptionsFor(currentTimezone: string): TimezoneOption[] {
  if (!currentTimezone || timezoneOptions.some((option) => option.value === currentTimezone)) {
    return timezoneOptions;
  }
  return [...timezoneOptions, { value: currentTimezone, label: currentTimezone }];
}

export const weekStartOptions = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
];
