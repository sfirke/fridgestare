import { FormEvent, useMemo, useState } from 'react';

import { api } from '../lib/api';
import {
  complexityOptions,
  createDefaultMealForm,
  mealFormFromMeal,
  mealPayloadFromForm,
  mealSeasonalOverrideSummary,
  recurrenceOptions,
  seasonOptions,
  type MealForm,
} from '../lib/meals';
import type { Dashboard } from '../hooks/useDashboard';
import type { StatusMessages } from '../hooks/useStatusMessages';
import type { Meal, MealComplexity, RecurrenceTier } from '../types/api';

type MealsViewProps = {
  dashboard: Dashboard;
  messages: StatusMessages;
};

type MealFilter = {
  complexity: '' | MealComplexity;
  tag: string;
};

function matchesFilter(meal: Meal, filter: MealFilter): boolean {
  if (filter.complexity && meal.complexity !== filter.complexity) {
    return false;
  }
  if (!filter.tag.trim()) {
    return true;
  }
  const needle = filter.tag.trim().toLowerCase();
  return meal.tags.some((tag) => tag.name.includes(needle));
}

export function MealsView({ dashboard, messages }: MealsViewProps) {
  const { meals, tagSuggestions, refreshMeals, refreshTagSuggestions } = dashboard;
  const [mealForm, setMealForm] = useState<MealForm>(createDefaultMealForm);
  const [selectedMealId, setSelectedMealId] = useState<number | null>(null);
  const [bulkText, setBulkText] = useState('');
  const [filter, setFilter] = useState<MealFilter>({ complexity: '', tag: '' });

  // Filtering happens here rather than server-side: the whole library is already
  // loaded, so a round-trip per keystroke bought nothing but latency.
  const filteredMeals = useMemo(
    () => meals.filter((meal) => matchesFilter(meal, filter)),
    [filter, meals],
  );

  function clearForm() {
    setSelectedMealId(null);
    setMealForm(createDefaultMealForm());
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await messages.run(
      async () => {
        const payload = mealPayloadFromForm(mealForm);
        if (selectedMealId) {
          await api.updateMeal(selectedMealId, payload);
        } else {
          await api.createMeal(payload);
        }
        clearForm();
        await Promise.all([refreshMeals(), refreshTagSuggestions()]);
      },
      {
        success: selectedMealId ? 'Meal updated.' : 'Meal added.',
        failure: 'Unable to save meal.',
      },
    );
  }

  async function handleBulkAdd() {
    await messages.run(
      async () => {
        await api.bulkFastAdd(bulkText);
        setBulkText('');
        await refreshMeals();
      },
      { success: 'Fast-add complete.', failure: 'Unable to fast-add meals.' },
    );
  }

  async function handleArchive(mealId: number) {
    await messages.run(
      async () => {
        await api.archiveMeal(mealId);
        await refreshMeals();
      },
      { success: 'Meal archived.', failure: 'Unable to archive meal.' },
    );
  }

  async function handleExport() {
    await messages.run(
      async () => {
        const csv = await api.exportMealsCsv();
        const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
        const link = document.createElement('a');
        link.href = url;
        link.download = 'fridgestare-meals.csv';
        link.click();
        URL.revokeObjectURL(url);
      },
      { success: 'CSV export downloaded.', failure: 'Unable to export meals.' },
    );
  }

  return (
    <section
      className="single-panel-layout"
      role="tabpanel"
      id="meals-panel"
      aria-labelledby="meals-tab"
    >
      <section className="panel meals-panel">
        <div className="panel-header">
          <h2>Meal library</h2>
          <p>Add new dinners, edit metadata, fast-enter a backlog, and export CSV.</p>
        </div>
        <div className="form-grid compact-grid">
          <label>
            <span>Filter by complexity</span>
            <select
              value={filter.complexity}
              onChange={(event) =>
                setFilter((current) => ({
                  ...current,
                  complexity: event.target.value as MealFilter['complexity'],
                }))
              }
            >
              <option value="">All</option>
              {complexityOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Filter by tag</span>
            <input
              value={filter.tag}
              onChange={(event) => setFilter((current) => ({ ...current, tag: event.target.value }))}
              placeholder="soup, tacos, cozy"
            />
          </label>
          <button className="secondary-button" type="button" onClick={() => void handleExport()}>
            Export CSV
          </button>
        </div>

        <form className="stacked-form" onSubmit={handleSubmit}>
          <div className="section-header-inline">
            <h3>{selectedMealId ? 'Edit meal' : 'Add meal'}</h3>
            {selectedMealId ? (
              <button className="ghost-button" type="button" onClick={clearForm}>
                Clear
              </button>
            ) : null}
          </div>
          <div className="form-grid">
            <label>
              <span>Title</span>
              <input
                value={mealForm.title}
                onChange={(event) =>
                  setMealForm((current) => ({ ...current, title: event.target.value }))
                }
                required
              />
            </label>
            <label>
              <span>Complexity</span>
              <select
                value={mealForm.complexity}
                onChange={(event) =>
                  setMealForm((current) => ({
                    ...current,
                    complexity: event.target.value as MealComplexity,
                  }))
                }
              >
                {complexityOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Base recurrence</span>
              <select
                value={mealForm.recurrence_tier}
                onChange={(event) =>
                  setMealForm((current) => ({
                    ...current,
                    recurrence_tier: event.target.value as RecurrenceTier,
                  }))
                }
              >
                {recurrenceOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Tags</span>
              <input
                value={mealForm.tags}
                onChange={(event) =>
                  setMealForm((current) => ({ ...current, tags: event.target.value }))
                }
                placeholder={tagSuggestions.slice(0, 5).join(', ')}
              />
            </label>
            <label>
              <span>Dietary exclusions</span>
              <input
                value={mealForm.dietary_exclusions}
                onChange={(event) =>
                  setMealForm((current) => ({ ...current, dietary_exclusions: event.target.value }))
                }
                placeholder="mushrooms, gluten"
              />
            </label>
            <label>
              <span>Source note</span>
              <input
                value={mealForm.source_note}
                onChange={(event) =>
                  setMealForm((current) => ({ ...current, source_note: event.target.value }))
                }
              />
            </label>
            <label>
              <span>Source URL</span>
              <input
                type="url"
                value={mealForm.source_url}
                onChange={(event) =>
                  setMealForm((current) => ({ ...current, source_url: event.target.value }))
                }
              />
            </label>
          </div>
          <div className="form-grid compact-grid">
            {seasonOptions.map((season) => (
              <label key={season.id}>
                <span>{season.label} override</span>
                <select
                  value={mealForm.seasonal_recurrence_overrides[season.id]}
                  onChange={(event) =>
                    setMealForm((current) => ({
                      ...current,
                      seasonal_recurrence_overrides: {
                        ...current.seasonal_recurrence_overrides,
                        [season.id]: event.target.value as '' | RecurrenceTier,
                      },
                    }))
                  }
                >
                  <option value="">Use base</option>
                  {recurrenceOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          <label>
            <span>Notes</span>
            <textarea
              value={mealForm.notes}
              onChange={(event) =>
                setMealForm((current) => ({ ...current, notes: event.target.value }))
              }
              rows={2}
            />
          </label>
          <button type="submit">{selectedMealId ? 'Update meal' : 'Add meal'}</button>
        </form>

        <div className="panel-subsection">
          <div className="section-header-inline">
            <h3>Bulk fast-add</h3>
            <button
              className="secondary-button"
              type="button"
              onClick={() => void handleBulkAdd()}
              disabled={!bulkText.trim()}
            >
              Fast-add list
            </button>
          </div>
          <textarea
            value={bulkText}
            onChange={(event) => setBulkText(event.target.value)}
            rows={4}
            placeholder="One meal title per line"
          />
        </div>

        <div className="meal-list">
          {filteredMeals.length === 0 ? (
            <p className="subtle-copy">
              {meals.length ? 'No meals match these filters.' : 'No meals in the library yet.'}
            </p>
          ) : null}
          {filteredMeals.map((meal) => {
            const overrideSummary = mealSeasonalOverrideSummary(meal);
            return (
              <article key={meal.id} className="meal-card">
                <div>
                  <h3>{meal.title}</h3>
                  <p>{meal.notes || 'No notes yet.'}</p>
                  {overrideSummary ? <p>Seasonal overrides: {overrideSummary}</p> : null}
                  <div className="chip-row">
                    <span className="chip">{meal.complexity}</span>
                    <span className="chip">{meal.recurrence_tier}</span>
                    {meal.tags.map((tag) => (
                      <span key={tag.id} className="chip">
                        {tag.name}
                      </span>
                    ))}
                    {meal.agent_sourced ? <span className="chip accent-chip">agent sourced</span> : null}
                  </div>
                </div>
                <div className="card-actions">
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => {
                      setSelectedMealId(meal.id);
                      setMealForm(mealFormFromMeal(meal));
                    }}
                  >
                    Edit
                  </button>
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => void handleArchive(meal.id)}
                  >
                    Archive
                  </button>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </section>
  );
}
