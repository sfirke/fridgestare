import { FormEvent } from 'react';

import { dayNames } from '../lib/dates';
import { timezoneOptionsFor, weekStartOptions } from '../lib/timezones';
import type { Dashboard } from '../hooks/useDashboard';

const ruleTypeOptions = [
  { value: 'prefer_tag', label: 'Prefer tag' },
  { value: 'must_include_tag', label: 'Must include tag' },
  { value: 'takeout', label: 'Takeout' },
  { value: 'avoid_complex', label: 'Avoid complex' },
];

const complexityToggles = [
  { field: 'allow_simple', label: 'Simple meals' },
  { field: 'allow_intermediate', label: 'Intermediate meals' },
  { field: 'allow_complex', label: 'Complex meals' },
  { field: 'email_enabled', label: 'Weekly email summary' },
] as const;

/** Rule types whose behavior comes from the day alone, with no tag to supply. */
const TAGLESS_RULE_TYPES = new Set(['takeout', 'avoid_complex']);

export function PreferencesView({ dashboard }: { dashboard: Dashboard }) {
  const {
    preferencesDraft,
    setPreferencesDraft,
    rulesDraft,
    setRulesDraft,
    timezoneDraft,
    setTimezoneDraft,
    weekStartsOnDraft,
    setWeekStartsOnDraft,
    savePreferences,
  } = dashboard;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void savePreferences();
  }

  return (
    <section
      className="single-panel-layout"
      role="tabpanel"
      id="preferences-panel"
      aria-labelledby="preferences-tab"
    >
      <section className="panel preferences-panel">
        <div className="panel-header">
          <h2>Preferences</h2>
          <p>Set planning guidance, complexity limits, email timing, and recurring rules.</p>
        </div>
        <form className="stacked-form" onSubmit={handleSubmit}>
          <label>
            <span>Guidance</span>
            <textarea
              value={preferencesDraft.planning_guidance_text}
              onChange={(event) =>
                setPreferencesDraft((current) => ({
                  ...current,
                  planning_guidance_text: event.target.value,
                }))
              }
              rows={3}
            />
          </label>
          <label>
            <span>Dietary notes</span>
            <textarea
              value={preferencesDraft.dietary_notes}
              onChange={(event) =>
                setPreferencesDraft((current) => ({ ...current, dietary_notes: event.target.value }))
              }
              rows={2}
            />
          </label>
          <div className="form-grid compact-grid">
            <label>
              <span>Takeout per week</span>
              <input
                type="number"
                min="0"
                max="7"
                step="1"
                value={preferencesDraft.takeout_frequency_per_week}
                onChange={(event) =>
                  setPreferencesDraft((current) => ({
                    ...current,
                    takeout_frequency_per_week: Number(event.target.value),
                  }))
                }
              />
            </label>
            <label>
              <span>Leftovers per week</span>
              <input
                type="number"
                min="0"
                max="7"
                step="1"
                value={preferencesDraft.leftovers_per_week}
                onChange={(event) =>
                  setPreferencesDraft((current) => ({
                    ...current,
                    leftovers_per_week: Number(event.target.value),
                  }))
                }
              />
            </label>
            <label>
              <span>Planning timezone</span>
              <select value={timezoneDraft} onChange={(event) => setTimezoneDraft(event.target.value)}>
                {timezoneOptionsFor(timezoneDraft).map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Week starts on</span>
              <select
                value={weekStartsOnDraft}
                onChange={(event) => setWeekStartsOnDraft(Number(event.target.value))}
              >
                {weekStartOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Email day</span>
              <select
                value={preferencesDraft.email_day_of_week}
                onChange={(event) =>
                  setPreferencesDraft((current) => ({
                    ...current,
                    email_day_of_week: Number(event.target.value),
                  }))
                }
              >
                {dayNames.map((day, index) => (
                  <option key={day} value={index}>
                    {day}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Email time</span>
              <input
                type="time"
                value={preferencesDraft.email_local_time.slice(0, 5)}
                onChange={(event) =>
                  setPreferencesDraft((current) => ({
                    ...current,
                    email_local_time: `${event.target.value}:00`,
                  }))
                }
              />
            </label>
          </div>
          <div className="checkbox-row">
            {complexityToggles.map((toggle) => (
              <label className="checkbox-option" key={toggle.field}>
                <input
                  type="checkbox"
                  checked={preferencesDraft[toggle.field]}
                  onChange={(event) =>
                    setPreferencesDraft((current) => ({
                      ...current,
                      [toggle.field]: event.target.checked,
                    }))
                  }
                />
                <span>{toggle.label}</span>
              </label>
            ))}
          </div>

          <div className="panel-subsection">
            <div className="section-header-inline">
              <h3>Recurring rules</h3>
              <button
                className="secondary-button"
                type="button"
                onClick={() =>
                  setRulesDraft((current) => [
                    ...current,
                    {
                      day_of_week: 0,
                      rule_type: 'prefer_tag',
                      rule_payload: { tag: 'soup' },
                      priority: 100,
                      active: true,
                    },
                  ])
                }
              >
                Add rule
              </button>
            </div>
            <div className="rule-stack">
              {rulesDraft.map((rule, index) => {
                const updateRule = (patch: Partial<(typeof rulesDraft)[number]>) =>
                  setRulesDraft((current) =>
                    current.map((item, itemIndex) =>
                      itemIndex === index ? { ...item, ...patch } : item,
                    ),
                  );
                return (
                  <div key={`${rule.rule_type}-${index}`} className="rule-card">
                    <select
                      aria-label="Rule day"
                      value={rule.day_of_week}
                      onChange={(event) => updateRule({ day_of_week: Number(event.target.value) })}
                    >
                      {dayNames.map((day, dayIndex) => (
                        <option key={day} value={dayIndex}>
                          {day}
                        </option>
                      ))}
                    </select>
                    <select
                      aria-label="Rule type"
                      value={rule.rule_type}
                      onChange={(event) => updateRule({ rule_type: event.target.value })}
                    >
                      {ruleTypeOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <input
                      type="text"
                      aria-label="Rule tag"
                      value={String(rule.rule_payload.tag ?? '')}
                      placeholder="tag payload"
                      onChange={(event) =>
                        updateRule({
                          rule_payload: event.target.value ? { tag: event.target.value } : {},
                        })
                      }
                      disabled={TAGLESS_RULE_TYPES.has(rule.rule_type)}
                    />
                    <button
                      className="ghost-button"
                      type="button"
                      onClick={() =>
                        setRulesDraft((current) =>
                          current.filter((_, itemIndex) => itemIndex !== index),
                        )
                      }
                    >
                      Remove
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          <button type="submit">Save preferences</button>
        </form>
      </section>
    </section>
  );
}
