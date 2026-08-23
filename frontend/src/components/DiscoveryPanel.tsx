import { useState } from 'react';

import { api } from '../lib/api';
import { slotCardTitle, slotLabel } from '../lib/slots';
import type { Dashboard } from '../hooks/useDashboard';
import type { StatusMessages } from '../hooks/useStatusMessages';
import type { DiscoveryCandidate, PlanSlot } from '../types/api';

type DiscoveryPanelProps = {
  dashboard: Dashboard;
  messages: StatusMessages;
  selectedSlot: PlanSlot | null;
};

export function DiscoveryPanel({ dashboard, messages, selectedSlot }: DiscoveryPanelProps) {
  const { plan, refreshMeals, refreshPlan } = dashboard;
  const [query, setQuery] = useState('');
  const [candidates, setCandidates] = useState<DiscoveryCandidate[]>([]);

  async function handleSuggest() {
    const found = await messages.run(() => api.suggestDiscovery(selectedSlot?.id ?? null, query), {
      failure: 'Unable to fetch discovery suggestions.',
    });
    if (found) {
      setCandidates(found);
      messages.setStatus(
        `Found ${found.length} discovery suggestion${found.length === 1 ? '' : 's'}.`,
      );
    }
  }

  async function handleAccept(candidateId: number) {
    if (!plan || !selectedSlot) {
      return;
    }
    await messages.run(
      async () => {
        await api.acceptDiscovery(candidateId, {
          plan_id: plan.id,
          slot_id: selectedSlot.id,
          apply_to_plan: true,
        });
        await Promise.all([refreshMeals(), refreshPlan()]);
      },
      {
        success: 'Discovered recipe accepted into your library and plan.',
        failure: 'Unable to accept discovery suggestion.',
      },
    );
  }

  return (
    <div className="panel-subsection">
      <div className="section-header-inline">
        <h3>{selectedSlot ? `Discovery for ${slotLabel(selectedSlot)}` : 'Discovery'}</h3>
        <span className="subtle-copy">
          {selectedSlot ? slotCardTitle(selectedSlot) : 'Select a slot to target discovery'}
        </span>
      </div>
      <label>
        <span>Discovery prompt</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="easy vegetarian soup"
          disabled={!selectedSlot}
        />
      </label>
      <button type="button" onClick={() => void handleSuggest()} disabled={!selectedSlot}>
        Suggest discovered meals
      </button>
      <div className="discovery-list">
        {candidates.map((candidate) => (
          <article key={candidate.id} className="discovery-card">
            <div>
              <h3>{candidate.title}</h3>
              <p>{candidate.summary}</p>
              <p className="slot-meta">
                {candidate.complexity} ·{' '}
                <a href={candidate.source_url} target="_blank" rel="noreferrer">
                  source
                </a>
              </p>
              <p className="slot-reason">{candidate.reasoning}</p>
            </div>
            <button type="button" onClick={() => void handleAccept(candidate.id)}>
              Accept into library and slot
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}
