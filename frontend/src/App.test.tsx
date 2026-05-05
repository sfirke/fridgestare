import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('App', () => {
  function makePlan(weekStartDate: string, label: string) {
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

  beforeEach(() => {
    window.history.replaceState({}, '', '/');
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse({ detail: 'unauthorized' }, 401)),
    );
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
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockResolvedValueOnce(
          jsonResponse({
            me: {
              user: { id: 1, email: 'sam@example.com', is_admin: true, created_at: '2026-05-03T00:00:00Z' },
              preferences: {
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
                updated_at: '2026-05-03T00:00:00Z',
              },
              recurring_rules: [],
            },
          }),
        )
        .mockResolvedValueOnce(
          jsonResponse({
            user: { id: 1, email: 'sam@example.com', is_admin: true, created_at: '2026-05-03T00:00:00Z' },
            preferences: {
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
              updated_at: '2026-05-03T00:00:00Z',
            },
            recurring_rules: [],
          }),
        )
        .mockResolvedValueOnce(jsonResponse([]))
        .mockResolvedValueOnce(jsonResponse([]))
        .mockResolvedValueOnce(jsonResponse([]))
        .mockResolvedValueOnce(jsonResponse({ detail: 'No plan for the active planning week' }, 404)),
    );

    render(<App />);

    const plannerTab = await screen.findByRole('tab', { name: 'Planner Week view, chat, discovery, and email.' });
    expect(plannerTab.getAttribute('aria-selected')).toBe('true');
    expect(await screen.findByText('No weekly plan exists yet for this planning week.')).not.toBeNull();
    expect(screen.getByRole('button', { name: 'Generate a plan' })).not.toBeNull();
    expect(screen.getByRole('tab', { name: 'Meals Library management and meal entry.' })).not.toBeNull();
    expect(screen.getByRole('tab', { name: 'Preferences Guidance, email settings, and recurring rules.' })).not.toBeNull();
    expect(screen.queryByText('Meal library')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Save preferences' })).toBeNull();
  });

  it('loads a saved week view with history navigation controls', async () => {
    window.history.replaceState({}, '', '/plans/2026-05-12');

    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockResolvedValueOnce(
          jsonResponse({
            me: {
              user: { id: 1, email: 'sam@example.com', is_admin: true, created_at: '2026-05-03T00:00:00Z' },
              preferences: {
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
                updated_at: '2026-05-03T00:00:00Z',
              },
              recurring_rules: [],
            },
          }),
        )
        .mockResolvedValueOnce(
          jsonResponse({
            user: { id: 1, email: 'sam@example.com', is_admin: true, created_at: '2026-05-03T00:00:00Z' },
            preferences: {
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
              updated_at: '2026-05-03T00:00:00Z',
            },
            recurring_rules: [],
          }),
        )
        .mockResolvedValueOnce(jsonResponse([]))
        .mockResolvedValueOnce(jsonResponse([]))
        .mockResolvedValueOnce(
          jsonResponse([
            { id: 2, week_start_date: '2026-05-12', status: 'draft', generation_source: 'manual' },
            { id: 1, week_start_date: '2026-05-05', status: 'draft', generation_source: 'manual' },
          ]),
        )
        .mockResolvedValueOnce(jsonResponse(makePlan('2026-05-12', 'Latest Saved Plan')))
        .mockResolvedValueOnce(jsonResponse({ detail: 'Plan not found' }, 404)),
    );

    render(<App />);

    expect(await screen.findByText('Latest Saved Plan')).not.toBeNull();
    expect(screen.getByRole('button', { name: 'Newer saved week' }).getAttribute('disabled')).not.toBeNull();
    expect(screen.getByRole('button', { name: 'Older saved week' }).getAttribute('disabled')).toBeNull();
    expect(screen.getByText('Saved week 1 of 2.')).not.toBeNull();
  });
});