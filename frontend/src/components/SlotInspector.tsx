import { useState } from 'react';

import { api } from '../lib/api';
import { formatDate } from '../lib/dates';
import { slotCardTitle, slotInspectorSummary, slotLabel, type LeftoverOption } from '../lib/slots';
import type { Dashboard } from '../hooks/useDashboard';
import type { PlanSlot } from '../types/api';

type SlotInspectorProps = {
  dashboard: Dashboard;
  selectedSlot: PlanSlot | null;
  leftoverOptions: LeftoverOption[];
};

export function SlotInspector({ dashboard, selectedSlot, leftoverOptions }: SlotInspectorProps) {
  const { plan, meals, applyPlanUpdate } = dashboard;
  const [mealChoice, setMealChoice] = useState<number | ''>('');
  const [leftoverChoice, setLeftoverChoice] = useState<number | ''>('');

  return (
    <div className="panel-subsection slot-inspector">
      <div className="section-header-inline">
        <h3>{selectedSlot ? `${slotLabel(selectedSlot)} details` : 'Choose a day'}</h3>
        {selectedSlot ? <span className="selection-pill">{slotCardTitle(selectedSlot)}</span> : null}
      </div>
      {plan && selectedSlot ? (
        <>
          <p className="slot-meta">{formatDate(selectedSlot.slot_date)}</p>
          <p className="slot-reason">{slotInspectorSummary(selectedSlot)}</p>
          <label>
            <span>Replace with a library meal</span>
            <div className="inline-select-row">
              <select
                value={mealChoice}
                onChange={(event) =>
                  setMealChoice(event.target.value ? Number(event.target.value) : '')
                }
              >
                <option value="">Choose a meal...</option>
                {meals.map((meal) => (
                  <option key={meal.id} value={meal.id}>
                    {meal.title}
                  </option>
                ))}
              </select>
              <button
                className="secondary-button"
                type="button"
                disabled={mealChoice === ''}
                onClick={() =>
                  void applyPlanUpdate(
                    () =>
                      api.setSlot(plan.id, {
                        slot_id: selectedSlot.id,
                        meal_id: Number(mealChoice),
                        slot_type: 'meal',
                      }),
                    'Slot updated.',
                  )
                }
              >
                Set meal
              </button>
            </div>
          </label>
          <label>
            <span>Mark as leftovers from earlier this week or last week</span>
            <div className="inline-select-row">
              <select
                value={leftoverChoice}
                onChange={(event) =>
                  setLeftoverChoice(event.target.value ? Number(event.target.value) : '')
                }
                disabled={leftoverOptions.length === 0}
              >
                <option value="">
                  {leftoverOptions.length
                    ? 'Choose a leftover source...'
                    : 'No earlier meals available yet'}
                </option>
                {leftoverOptions.map((option) => (
                  <option key={option.mealId} value={option.mealId}>
                    {option.label}
                  </option>
                ))}
              </select>
              <button
                className="secondary-button"
                type="button"
                disabled={leftoverChoice === ''}
                onClick={() =>
                  void applyPlanUpdate(
                    () =>
                      api.setSlot(plan.id, {
                        slot_id: selectedSlot.id,
                        meal_id: Number(leftoverChoice),
                        slot_type: 'leftover',
                      }),
                    'Slot marked as leftovers.',
                  )
                }
              >
                Mark leftover
              </button>
            </div>
          </label>
          <div className="slot-actions inspector-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={() =>
                void applyPlanUpdate(
                  () => api.rerollSlot(plan.id, selectedSlot.id),
                  'Slot rerolled.',
                )
              }
            >
              Reroll
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() =>
                void applyPlanUpdate(
                  () => api.setSlot(plan.id, { slot_id: selectedSlot.id, slot_type: 'takeout' }),
                  'Slot marked as takeout.',
                )
              }
            >
              Takeout
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() =>
                void applyPlanUpdate(
                  () => api.setSlot(plan.id, { slot_id: selectedSlot.id, slot_type: 'empty' }),
                  'Slot cleared.',
                )
              }
            >
              Clear slot
            </button>
          </div>
          <div className="slot-actions compact-row inspector-actions">
            <button
              className="ghost-button"
              type="button"
              onClick={() =>
                void applyPlanUpdate(
                  () => api.updateOutcome(plan.id, selectedSlot.id, 'cooked'),
                  'Outcome marked cooked.',
                )
              }
            >
              Cooked
            </button>
            <button
              className="ghost-button"
              type="button"
              onClick={() =>
                void applyPlanUpdate(
                  () => api.updateOutcome(plan.id, selectedSlot.id, 'skipped'),
                  'Outcome marked skipped.',
                )
              }
            >
              Skipped
            </button>
            <button
              className="ghost-button"
              type="button"
              disabled={!selectedSlot.outcome_status}
              onClick={() =>
                void applyPlanUpdate(
                  () => api.updateOutcome(plan.id, selectedSlot.id, null),
                  'Outcome cleared.',
                )
              }
            >
              Clear outcome
            </button>
          </div>
          {selectedSlot.outcome_status ? (
            <p className="slot-outcome">Outcome: {selectedSlot.outcome_status}</p>
          ) : null}
        </>
      ) : (
        <p className="subtle-copy">
          Select a day in the planner to unlock meal replacement, discovery, and outcome
          controls.
        </p>
      )}
    </div>
  );
}
