import { FormEvent, useState } from 'react';

import { api } from '../lib/api';
import type { Dashboard } from '../hooks/useDashboard';
import type { StatusMessages } from '../hooks/useStatusMessages';

type ChatEntry = {
  role: 'user' | 'planner';
  message: string;
};

export function PlannerChat({
  dashboard,
  messages,
}: {
  dashboard: Dashboard;
  messages: StatusMessages;
}) {
  const { plan, applyPlanUpdate } = dashboard;
  const [draft, setDraft] = useState('');
  const [history, setHistory] = useState<ChatEntry[]>([]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = draft.trim();
    if (!plan || !message) {
      return;
    }
    const response = await messages.run(() => api.chatPlan(plan.id, message), {
      failure: 'Unable to apply chat edit.',
    });
    if (!response) {
      return;
    }
    await applyPlanUpdate(async () => response.plan, 'Chat update applied.');
    setHistory((current) => [
      ...current,
      { role: 'user', message },
      { role: 'planner', message: response.explanation },
    ]);
    setDraft('');
  }

  return (
    <>
      <form className="stacked-form" onSubmit={handleSubmit}>
        <label>
          <span>Chat with the planner</span>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            rows={3}
            placeholder="Put a soup on Tuesday, swap Wednesday and Thursday, make Friday simpler..."
          />
        </label>
        <button type="submit" disabled={!plan || !draft.trim()}>
          Send chat edit
        </button>
      </form>
      <div className="chat-history">
        {history.map((entry, index) => (
          <article key={`${entry.role}-${index}`} className={`chat-bubble ${entry.role}`}>
            <strong>{entry.role === 'user' ? 'You' : 'Planner'}</strong>
            <p>{entry.message}</p>
          </article>
        ))}
      </div>
    </>
  );
}
