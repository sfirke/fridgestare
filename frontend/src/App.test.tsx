import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('App', () => {
  beforeEach(() => {
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
        .mockResolvedValueOnce(jsonResponse({ detail: 'No plan for next week' }, 404)),
    );

    render(<App />);

    const plannerTab = await screen.findByRole('tab', { name: 'Planner Week view, chat, discovery, and email.' });
    expect(plannerTab.getAttribute('aria-selected')).toBe('true');
    expect(await screen.findByText('No weekly plan exists yet for next week.')).not.toBeNull();
    expect(screen.getByRole('button', { name: 'Generate a plan' })).not.toBeNull();
    expect(screen.getByRole('tab', { name: 'Meals Library management and meal entry.' })).not.toBeNull();
    expect(screen.getByRole('tab', { name: 'Preferences Guidance, email settings, and recurring rules.' })).not.toBeNull();
    expect(screen.queryByText('Meal library')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Save preferences' })).toBeNull();
  });
});