import { useEffect, useState } from "react";
import { ContextOverviewDto, TimelineItemDto, getContextOverview, getTimeline } from "@/integrations/metatheosApi";

const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return "Unknown time";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
};

const Home = () => {
  const [overview, setOverview] = useState<ContextOverviewDto | null>(null);
  const [timeline, setTimeline] = useState<TimelineItemDto[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [overviewResponse, timelineResponse] = await Promise.all([
          getContextOverview(),
          getTimeline({ limit: 6 }),
        ]);
        if (!isMounted) {
          return;
        }
        setOverview(overviewResponse);
        setTimeline(timelineResponse.data || []);
      } catch (err) {
        if (!isMounted) {
          return;
        }
        const message = err instanceof Error ? err.message : "Unable to load observatory data.";
        setError(message);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    load();
    return () => {
      isMounted = false;
    };
  }, []);

  const activePhase = overview?.active_phase || null;
  const currentDay = overview?.current_day || null;

  return (
    <div className="metatheos-fade-in">
      <div className="metatheos-home-header">
        <span className="metatheos-kicker">Observatory</span>
        <h1>Metatheos Home</h1>
        <p className="metatheos-muted">A calm shell for governance oversight.</p>
        {error ? <div className="metatheos-error">{error}</div> : null}
      </div>

      <div className="metatheos-home-grid">
        <section className="metatheos-panel">
          <h2>Active Phase</h2>
          {isLoading ? (
            <div className="metatheos-muted">Loading phase context...</div>
          ) : (
            <>
              <div>{activePhase?.title || "No active phase detected."}</div>
              <div className="metatheos-muted">
                {activePhase?.status ? `Status: ${activePhase.status}` : "Awaiting phase linkage."}
              </div>
            </>
          )}
        </section>
        <section className="metatheos-panel">
          <h2>Current Day</h2>
          {isLoading ? (
            <div className="metatheos-muted">Loading day context...</div>
          ) : (
            <>
              <div>{currentDay ? formatTimestamp(currentDay.created_at) : "Day context unavailable."}</div>
              <div className="metatheos-muted">
                {currentDay?.day_type ? `Type: ${currentDay.day_type}` : "Synced at session start."}
              </div>
            </>
          )}
        </section>
      </div>

      <section className="metatheos-panel">
        <h2>Recent Events / Annotations</h2>
        {isLoading ? (
          <div className="metatheos-muted">Loading timeline...</div>
        ) : timeline.length ? (
          <ul className="metatheos-list">
            {timeline.map((item) => (
              <li key={item.id}>
                <div>{item.summary}</div>
                <div className="metatheos-muted">{formatTimestamp(item.ts)}</div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="metatheos-muted">No recent events recorded.</div>
        )}
      </section>
    </div>
  );
};

export default Home;
