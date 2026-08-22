import { useState } from 'react';

import { DashboardNav, type DashboardView } from './components/DashboardNav';
import { LoginScreen } from './components/LoginScreen';
import { MealsView } from './components/MealsView';
import { PlannerView } from './components/PlannerView';
import { PreferencesView } from './components/PreferencesView';
import { StatusBanners } from './components/StatusBanners';
import { useDashboard } from './hooks/useDashboard';
import { useStatusMessages } from './hooks/useStatusMessages';
import { formatWeekRange } from './lib/dates';
import './styles.css';

export function App() {
  const messages = useStatusMessages();
  const dashboard = useDashboard(messages);
  const [activeView, setActiveView] = useState<DashboardView>('planner');

  if (dashboard.authState === 'loading') {
    return (
      <main className="app-shell loading-shell">
        <section className="hero-panel">
          <p className="eyebrow">Fridgestare</p>
          <h1>Loading the kitchen radar.</h1>
        </section>
      </main>
    );
  }

  if (dashboard.authState === 'anonymous') {
    return (
      <LoginScreen
        errorMessage={messages.errorMessage}
        onLogin={(email, password) => void dashboard.login(email, password)}
      />
    );
  }

  const displayedWeek = dashboard.plan?.week_start_date ?? dashboard.viewedWeek;
  const activeWeekRange = displayedWeek ? formatWeekRange(displayedWeek) : 'No week selected';

  return (
    <main className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Fridgestare</p>
          <h1>Weekly meal calendar</h1>
          <p className="subtle-copy">
            {dashboard.session?.user.email} · {activeWeekRange}
          </p>
        </div>
        <div className="topbar-actions">
          {activeView === 'planner' && dashboard.plan ? (
            <button onClick={() => void dashboard.generatePlan()}>Regenerate week</button>
          ) : null}
          <button className="secondary-button" onClick={() => void dashboard.logout()}>
            Log out
          </button>
        </div>
      </header>

      <StatusBanners
        statusMessage={messages.statusMessage}
        errorMessage={messages.errorMessage}
      />

      <DashboardNav
        activeView={activeView}
        onSelect={(view) => {
          messages.reset();
          setActiveView(view);
        }}
      />

      <section className="dashboard-content">
        {activeView === 'planner' ? (
          <PlannerView dashboard={dashboard} messages={messages} />
        ) : null}
        {activeView === 'meals' ? <MealsView dashboard={dashboard} messages={messages} /> : null}
        {activeView === 'preferences' ? <PreferencesView dashboard={dashboard} /> : null}
      </section>
    </main>
  );
}

export default App;
