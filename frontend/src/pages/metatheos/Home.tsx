const Home = () => {
  // TODO: Replace placeholders with live governance state.
  const activePhase = "Threshold";
  const currentDay = "Day 0";
  // TODO: Wire recent events to the audit feed.
  const recentEvents = [
    "Observation window opened.",
    "First annotation recorded.",
    "Causality trace queued for verification.",
  ];

  return (
    <div className="metatheos-fade-in">
      <div className="metatheos-home-header">
        <span className="metatheos-kicker">Observatory</span>
        <h1>Metatheos Home</h1>
        <p className="metatheos-muted">A calm shell for governance oversight.</p>
      </div>

      <div className="metatheos-home-grid">
        <section className="metatheos-panel">
          <h2>Active Phase</h2>
          <div>{activePhase}</div>
          <div className="metatheos-muted">Awaiting phase linkage.</div>
        </section>
        <section className="metatheos-panel">
          <h2>Current Day</h2>
          <div>{currentDay}</div>
          <div className="metatheos-muted">Synced at session start.</div>
        </section>
      </div>

      <section className="metatheos-panel">
        <h2>Recent Events / Annotations</h2>
        <ul className="metatheos-list">
          {recentEvents.map((event) => (
            <li key={event}>{event}</li>
          ))}
        </ul>
      </section>
    </div>
  );
};

export default Home;
