import { useState } from 'react';

import { formatDayNumber, formatMonthLabel } from '../lib/dates';
import { slotBadgeLabel, slotCalendarLabel, slotCardTitle } from '../lib/slots';
import type { Plan, PlanSlot } from '../types/api';

type PlannerBoardProps = {
  plan: Plan;
  selectedSlotId: number | null;
  onSelectSlot: (slotId: number) => void;
  onMoveSlot: (sourceSlotId: number, targetSlotId: number) => void;
  onRerollSlot: (slotId: number) => void;
};

export function PlannerBoard({
  plan,
  selectedSlotId,
  onSelectSlot,
  onMoveSlot,
  onRerollSlot,
}: PlannerBoardProps) {
  const [draggedSlotId, setDraggedSlotId] = useState<number | null>(null);

  function handleDrop(targetSlotId: number) {
    if (draggedSlotId !== null && draggedSlotId !== targetSlotId) {
      onMoveSlot(draggedSlotId, targetSlotId);
    }
    setDraggedSlotId(null);
  }

  return (
    <div className="planner-board">
      {plan.slots.map((slot: PlanSlot) => (
        <article
          key={slot.id}
          className={`slot-card slot-type-${slot.slot_type} ${
            selectedSlotId === slot.id ? 'slot-selected' : ''
          }`}
          draggable
          aria-current={selectedSlotId === slot.id}
          onClick={() => onSelectSlot(slot.id)}
          onDragStart={() => setDraggedSlotId(slot.id)}
          onDragEnd={() => setDraggedSlotId(null)}
          onDragOver={(event) => event.preventDefault()}
          onDrop={() => handleDrop(slot.id)}
        >
          <div className="slot-calendar-row">
            <div className="slot-calendar-copy">
              <p className="slot-day">{slotCalendarLabel(slot)}</p>
              <p className="slot-date-inline">{formatMonthLabel(slot.slot_date)}</p>
            </div>
            <div className="slot-date-number">{formatDayNumber(slot.slot_date)}</div>
          </div>
          <div className="slot-body">
            <h3>{slotCardTitle(slot)}</h3>
            {slot.notes_snapshot ? <p className="slot-note">{slot.notes_snapshot}</p> : null}
          </div>
          <div className="slot-footer">
            <span className="slot-type-pill">{slotBadgeLabel(slot)}</span>
            {slot.outcome_status ? <span className="outcome-pill">{slot.outcome_status}</span> : null}
            <button
              className="reroll-icon-button"
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                onRerollSlot(slot.id);
              }}
              title={`Reroll ${slotCalendarLabel(slot)}`}
              aria-label={`Reroll ${slotCalendarLabel(slot)}`}
            >
              🎲
            </button>
            {selectedSlotId === slot.id ? <span className="slot-focus-pill">Selected</span> : null}
          </div>
        </article>
      ))}
    </div>
  );
}
