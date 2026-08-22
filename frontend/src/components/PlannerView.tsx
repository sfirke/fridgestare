import { useMemo, useState } from 'react';

import { api } from '../lib/api';
import { formatWeekRange } from '../lib/dates';
import { buildLeftoverOptions } from '../lib/slots';
import type { Dashboard } from '../hooks/useDashboard';
import type { StatusMessages } from '../hooks/useStatusMessages';
import type { EmailPreview } from '../types/api';
import { DiscoveryPanel } from './DiscoveryPanel';
import { EmailPreviewPanel } from './EmailPreviewPanel';
import { PlannerBoard } from './PlannerBoard';
import { PlannerChat } from './PlannerChat';
import { SlotInspector } from './SlotInspector';

type PlannerViewProps = {
  dashboard: Dashboard;
  messages: StatusMessages;
};

export function PlannerView({ dashboard, messages }: PlannerViewProps) {
  const { plan, previousPlan, planHistory, viewedWeek, applyPlanUpdate, generatePlan, openWeek } =
    dashboard;
  const [requestedSlotId, setRequestedSlotId] = useState<number | null>(null);
  const [emailPreview, setEmailPreview] = useState<EmailPreview | null>(null);

  // The focused day is derived rather than synced through an effect: when the week
  // changes or is regenerated the requested id simply stops matching, and the first
  // day of the new week takes focus without an extra render pass.
  const selectedSlot =
    plan?.slots.find((slot) => slot.id === requestedSlotId) ?? plan?.slots[0] ?? null;
  const selectedSlotId = selectedSlot?.id ?? null;
  const leftoverOptions = useMemo(
    () => buildLeftoverOptions(plan, previousPlan, selectedSlot),
    [plan, previousPlan, selectedSlot],
  );

  const activeWeek = plan?.week_start_date ?? viewedWeek;
  const activeWeekRange = activeWeek ? formatWeekRange(activeWeek) : 'No week selected';
  const activeHistoryIndex = activeWeek
    ? planHistory.findIndex((summary) => summary.week_start_date === activeWeek)
    : -1;
  const latestSavedPlan = planHistory[0] ?? null;
  const newerSavedPlan = activeHistoryIndex > 0 ? planHistory[activeHistoryIndex - 1] : null;
  const olderSavedPlan =
    activeHistoryIndex >= 0 && activeHistoryIndex < planHistory.length - 1
      ? planHistory[activeHistoryIndex + 1]
      : null;

  async function handleEmailPreview() {
    if (!plan) {
      return;
    }
    const preview = await messages.run(() => api.previewEmail(plan.id), {
      success: 'Email preview refreshed.',
      failure: 'Unable to preview email.',
    });
    if (preview) {
      setEmailPreview(preview);
    }
  }

  async function handleSendEmail() {
    if (!plan) {
      return;
    }
    const response = await messages.run(() => api.sendEmail(plan.id), {
      failure: 'Unable to send email.',
    });
    if (response) {
      messages.setStatus(`Email queued via ${response.delivery_mode}.`);
    }
  }

  return (
    <section
      className="planner-layout"
      role="tabpanel"
      id="planner-panel"
      aria-labelledby="planner-tab"
    >
      <section className="panel planner-panel">
        <div className="panel-header planner-header">
          <div>
            <p className="section-kicker">Planner</p>
            <h2>Week at a glance</h2>
            <p className="planner-range">{activeWeekRange}</p>
          </div>
          {plan ? <span className="selection-pill">{plan.slots.length} days planned</span> : null}
        </div>

        <div className="planner-toolbar">
          <button
            className="secondary-button"
            type="button"
            onClick={() => void openWeek(null)}
            disabled={viewedWeek === null}
          >
            Current week
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => newerSavedPlan && void openWeek(newerSavedPlan.week_start_date)}
            disabled={!newerSavedPlan}
          >
            Newer saved week
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => olderSavedPlan && void openWeek(olderSavedPlan.week_start_date)}
            disabled={!olderSavedPlan}
          >
            Older saved week
          </button>
          <span className="subtle-copy">
            {plan
              ? `Saved week ${activeHistoryIndex + 1} of ${planHistory.length}.`
              : planHistory.length
                ? `${planHistory.length} saved week${planHistory.length === 1 ? '' : 's'} available.`
                : 'No saved weeks yet.'}
          </span>
        </div>

        {plan ? (
          <>
            <div className="planner-toolbar">
              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  void applyPlanUpdate(() => api.undoPlan(plan.id), 'Last change undone.')
                }
              >
                Undo last action
              </button>
              <button
                className="secondary-button"
                type="button"
                onClick={() => void handleEmailPreview()}
              >
                Preview email
              </button>
              <button
                className="secondary-button"
                type="button"
                onClick={() => void handleSendEmail()}
              >
                Send email
              </button>
            </div>
            <PlannerBoard
              plan={plan}
              selectedSlotId={selectedSlotId}
              onSelectSlot={setRequestedSlotId}
              onMoveSlot={(sourceSlotId, targetSlotId) =>
                void applyPlanUpdate(
                  () => api.moveSlot(plan.id, sourceSlotId, targetSlotId),
                  'Slots rearranged.',
                )
              }
              onRerollSlot={(slotId) =>
                void applyPlanUpdate(() => api.rerollSlot(plan.id, slotId), 'Slot rerolled.')
              }
            />
          </>
        ) : (
          <div className="empty-state">
            <p>No weekly plan exists yet for this planning week.</p>
            <button type="button" onClick={() => void generatePlan()}>
              Generate week
            </button>
            {latestSavedPlan ? (
              <button
                className="secondary-button"
                type="button"
                onClick={() => void openWeek(latestSavedPlan.week_start_date)}
              >
                Open latest saved week
              </button>
            ) : null}
          </div>
        )}
      </section>

      <section className="panel side-panel">
        <div className="panel-header">
          <h2>Day details</h2>
          <p>
            Keep one day in focus while you swap meals, reroll, discover something new, or log
            the outcome.
          </p>
        </div>

        <SlotInspector
          dashboard={dashboard}
          selectedSlot={selectedSlot}
          leftoverOptions={leftoverOptions}
        />
        <DiscoveryPanel dashboard={dashboard} messages={messages} selectedSlot={selectedSlot} />
        <PlannerChat dashboard={dashboard} messages={messages} />
        <EmailPreviewPanel preview={emailPreview} />
      </section>
    </section>
  );
}
