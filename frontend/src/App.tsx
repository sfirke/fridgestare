import './styles.css';

export function App() {
  return (
    <main className="app-shell">
      <section className="hero-panel">
        <p className="eyebrow">Fridgestare</p>
        <h1>Plan dinners like a benevolent kitchen goblin.</h1>
        <p className="lede">
          Weekly plans, drag-and-drop edits, chat tweaks, and recipe discovery all live
          here. The rest of the app lands in the next build phases.
        </p>
      </section>
      <section className="status-panel">
        <h2>Build status</h2>
        <ul>
          <li>Backend scaffold is live.</li>
          <li>Frontend shell is live.</li>
          <li>Domain, auth, planner, and UI features are next.</li>
        </ul>
      </section>
    </main>
  );
}

export default App;
