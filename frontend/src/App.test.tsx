import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'unauthorized' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
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
});