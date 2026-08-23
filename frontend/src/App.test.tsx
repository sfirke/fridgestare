import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';
import {
  jsonResponse,
  makePlan,
  makeSession,
  planSummary,
  stubBackend,
} from './test/fixtures';

const PLANNER_TAB = 'Planner Week view, chat, discovery, and email.';
const MEALS_TAB = 'Meals Library management and meal entry.';
const PREFERENCES_TAB = 'Preferences Guidance, email settings, and recurring rules.';

describe('App', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
    stubBackend({ routes: [() => jsonResponse({ detail: 'unauthorized' }, 401)] });
    Object.defineProperty(document, 'cookie', {
      configurable: true,
      get: () => '',
      set: () => true,
    });
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('renders the login form when not authenticated', async () => {
    render(<App />);

    expect(await screen.findByText('Sign in')).not.toBeNull();
    expect(screen.getByRole('button', { name: 'Enter the pantry' })).not.toBeNull();
  });

  it('renders the empty planner state when next week has no plan yet', async () => {
    stubBackend();

    render(<App />);

    const plannerTab = await screen.findByRole('tab', { name: PLANNER_TAB });
    expect(plannerTab.getAttribute('aria-selected')).toBe('true');
    expect(
      await screen.findByText('No weekly plan exists yet for this planning week.'),
    ).not.toBeNull();
    expect(screen.getByRole('button', { name: 'Generate week' })).not.toBeNull();
    expect(screen.getByRole('tab', { name: MEALS_TAB })).not.toBeNull();
    expect(screen.getByRole('tab', { name: PREFERENCES_TAB })).not.toBeNull();
    expect(screen.queryByText('Meal library')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Save preferences' })).toBeNull();
  });

  it('loads a saved week view with history navigation controls', async () => {
    window.history.replaceState({}, '', '/plans/2026-05-12');
    const latest = makePlan('2026-05-12', 'Latest Saved Plan');
    const older = makePlan('2026-05-05', 'Older Saved Plan');
    stubBackend({
      plans: [planSummary(latest), planSummary(older)],
      weekPlans: { '2026-05-12': latest, '2026-05-05': older },
    });

    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Latest Saved Plan' })).not.toBeNull();
    expect(
      screen.getByRole('button', { name: 'Newer saved week' }).getAttribute('disabled'),
    ).not.toBeNull();
    expect(
      screen.getByRole('button', { name: 'Older saved week' }).getAttribute('disabled'),
    ).toBeNull();
    expect(screen.getByText('Saved week 1 of 2.')).not.toBeNull();
  });

  it('shows planner actions only on the planner tab', async () => {
    window.history.replaceState({}, '', '/plans/2026-05-12');
    const latest = makePlan('2026-05-12', 'Latest Saved Plan');
    stubBackend({ plans: [planSummary(latest)], weekPlans: { '2026-05-12': latest } });

    render(<App />);

    expect(await screen.findByRole('heading', { name: 'Latest Saved Plan' })).not.toBeNull();
    expect(screen.getByRole('button', { name: 'Regenerate week' })).not.toBeNull();
    expect(screen.queryByRole('button', { name: 'Generate week' })).toBeNull();

    fireEvent.click(screen.getByRole('tab', { name: MEALS_TAB }));

    expect(screen.queryByRole('button', { name: 'Generate week' })).toBeNull();
    expect(screen.queryByRole('button', { name: 'Regenerate week' })).toBeNull();
    expect(screen.getByRole('button', { name: 'Log out' })).not.toBeNull();
  });

  it('regenerates an existing week from the planner toolbar', async () => {
    window.history.replaceState({}, '', '/plans/2026-05-12');
    const existing = makePlan('2026-05-12', 'Existing Plan');
    const regenerated = makePlan('2026-05-12', 'Regenerated Plan');
    const fetchMock = stubBackend({
      plans: [planSummary(existing)],
      weekPlans: { '2026-05-12': existing },
      routes: [
        ({ path, method }) =>
          path === '/plans/generate' && method === 'POST' ? jsonResponse(regenerated) : null,
      ],
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: 'Regenerate week' }));

    expect(await screen.findByText('Weekly plan regenerated.')).not.toBeNull();
    expect(await screen.findByRole('heading', { name: 'Regenerated Plan' })).not.toBeNull();

    const generateCall = fetchMock.mock.calls.find((call) => String(call[0]).endsWith('/generate'));
    expect(generateCall).toBeDefined();
    expect(JSON.parse(String(generateCall?.[1]?.body))).toEqual({
      week_start_date: '2026-05-12',
      force_regenerate: true,
    });
  });

  it('generates a missing week from the empty state', async () => {
    const fresh = makePlan('2026-05-18', 'Fresh Plan');
    const fetchMock = stubBackend({
      routes: [
        ({ path, method }) =>
          path === '/plans/generate' && method === 'POST' ? jsonResponse(fresh) : null,
      ],
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: 'Generate week' }));

    expect(await screen.findByText('Weekly plan generated.')).not.toBeNull();
    expect(await screen.findByRole('heading', { name: 'Fresh Plan' })).not.toBeNull();

    const generateCall = fetchMock.mock.calls.find((call) => String(call[0]).endsWith('/generate'));
    expect(generateCall).toBeDefined();
    expect(JSON.parse(String(generateCall?.[1]?.body))).toEqual({
      week_start_date: null,
      force_regenerate: false,
    });
  });

  it('focuses the first day of a loaded week without an extra render pass', async () => {
    window.history.replaceState({}, '', '/plans/2026-05-12');
    const plan = makePlan('2026-05-12', 'Focused Plan');
    stubBackend({ plans: [planSummary(plan)], weekPlans: { '2026-05-12': plan } });

    render(<App />);

    // The day-details panel is populated from the derived selection, so it names the
    // first day rather than sitting on the "choose a day" placeholder.
    expect(await screen.findByRole('heading', { name: 'Tuesday details' })).not.toBeNull();
    expect(screen.queryByRole('heading', { name: 'Choose a day' })).toBeNull();
  });

  it('offers planning timezones as a fixed list rather than free text', async () => {
    stubBackend({ session: makeSession({ timezone: 'America/Chicago' }) });

    render(<App />);
    fireEvent.click(await screen.findByRole('tab', { name: PREFERENCES_TAB }));

    const timezoneSelect = screen.getByLabelText('Planning timezone') as HTMLSelectElement;
    expect(timezoneSelect.tagName).toBe('SELECT');
    expect(timezoneSelect.value).toBe('America/Chicago');
    expect(
      Array.from(timezoneSelect.options).some((option) => option.value === 'America/New_York'),
    ).toBe(true);
  });

  it('keeps an account timezone that is not one of the presets selectable', async () => {
    stubBackend({ session: makeSession({ timezone: 'Asia/Tokyo' }) });

    render(<App />);
    fireEvent.click(await screen.findByRole('tab', { name: PREFERENCES_TAB }));

    const timezoneSelect = screen.getByLabelText('Planning timezone') as HTMLSelectElement;
    expect(timezoneSelect.value).toBe('Asia/Tokyo');
  });

  it('filters the meal library locally as you type', async () => {
    const meals = [
      {
        id: 1,
        title: 'Tomato Soup',
        notes: '',
        meal_type: 'dinner',
        complexity: 'simple',
        recurrence_tier: 'regular',
        seasonal_recurrence_overrides: [],
        dietary_exclusions: [],
        source_note: '',
        source_url: '',
        agent_sourced: false,
        is_archived: false,
        tags: [{ id: 1, name: 'soup' }],
        created_at: '2026-05-03T00:00:00Z',
        updated_at: '2026-05-03T00:00:00Z',
      },
      {
        id: 2,
        title: 'Tuesday Tacos',
        notes: '',
        meal_type: 'dinner',
        complexity: 'simple',
        recurrence_tier: 'regular',
        seasonal_recurrence_overrides: [],
        dietary_exclusions: [],
        source_note: '',
        source_url: '',
        agent_sourced: false,
        is_archived: false,
        tags: [{ id: 2, name: 'tacos' }],
        created_at: '2026-05-03T00:00:00Z',
        updated_at: '2026-05-03T00:00:00Z',
      },
    ];
    const fetchMock = stubBackend({ meals });

    render(<App />);
    fireEvent.click(await screen.findByRole('tab', { name: MEALS_TAB }));
    expect(await screen.findByRole('heading', { name: 'Tomato Soup' })).not.toBeNull();

    const callsBeforeFiltering = fetchMock.mock.calls.length;
    fireEvent.change(screen.getByLabelText('Filter by tag'), { target: { value: 'soup' } });

    expect(screen.getByRole('heading', { name: 'Tomato Soup' })).not.toBeNull();
    expect(screen.queryByRole('heading', { name: 'Tuesday Tacos' })).toBeNull();
    // Filtering must not cost a round-trip; the library is already loaded.
    expect(fetchMock.mock.calls.length).toBe(callsBeforeFiltering);
  });

  it('renders FastAPI validation errors as readable text', async () => {
    stubBackend({
      routes: [
        ({ path, method }) =>
          path === '/plans/generate' && method === 'POST'
            ? jsonResponse(
                { detail: [{ loc: ['body', 'week_start_date'], msg: 'invalid date format' }] },
                422,
              )
            : null,
      ],
    });

    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: 'Generate week' }));

    await waitFor(() => {
      expect(screen.getByRole('alert').textContent).toBe('week_start_date: invalid date format');
    });
  });
});
