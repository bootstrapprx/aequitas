import { useEffect, useState } from "react";
import { TimelineItemDto, getTimeline } from "@/integrations/metatheosApi";

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

const Timeline = () => {
  const [items, setItems] = useState<TimelineItemDto[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await getTimeline({ limit: 50 });
        if (!isMounted) {
          return;
        }
        setItems(response.data || []);
      } catch (err) {
        if (!isMounted) {
          return;
        }
        const message = err instanceof Error ? err.message : "Unable to load timeline.";
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

  return (
    <div className="metatheos-fade-in">
      <span className="metatheos-kicker">Sequence</span>
      <h1>Timeline</h1>
      <p className="metatheos-muted">Merged events and annotations across phases.</p>
      <div className="metatheos-divider" />
      <section className="metatheos-panel">
        {error ? <div className="metatheos-error">{error}</div> : null}
        {isLoading ? (
          <div className="metatheos-muted">Loading timeline...</div>
        ) : items.length ? (
          <ul className="metatheos-list">
            {items.map((item) => (
              <li key={item.id}>
                <div>{item.summary}</div>
                <div className="metatheos-muted">
                  {item.kind} · {formatTimestamp(item.ts)}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="metatheos-muted">No timeline activity yet.</div>
        )}
      </section>
    </div>
  );
};

export default Timeline;
