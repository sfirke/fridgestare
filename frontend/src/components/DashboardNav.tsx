export type DashboardView = 'planner' | 'meals' | 'preferences';

const dashboardViews: Array<{ id: DashboardView; label: string; description: string }> = [
  { id: 'planner', label: 'Planner', description: 'Week view, chat, discovery, and email.' },
  { id: 'meals', label: 'Meals', description: 'Library management and meal entry.' },
  {
    id: 'preferences',
    label: 'Preferences',
    description: 'Guidance, email settings, and recurring rules.',
  },
];

type DashboardNavProps = {
  activeView: DashboardView;
  onSelect: (view: DashboardView) => void;
};

export function DashboardNav({ activeView, onSelect }: DashboardNavProps) {
  return (
    <section className="dashboard-nav" role="tablist" aria-label="Workspace sections">
      {dashboardViews.map((view) => {
        const isActive = activeView === view.id;
        return (
          <button
            key={view.id}
            id={`${view.id}-tab`}
            className={`view-tab ${isActive ? 'is-active' : ''}`}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-controls={`${view.id}-panel`}
            onClick={() => onSelect(view.id)}
          >
            <span>{view.label}</span>
            <small>{view.description}</small>
          </button>
        );
      })}
    </section>
  );
}
