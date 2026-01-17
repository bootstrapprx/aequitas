import { useEffect, useState } from "react";
import { PhaseDto, listPhases } from "@/integrations/metatheosApi";

const formatDate = (value?: string | null) => {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString();
};

const Phases = () => {
  const [phases, setPhases] = useState<PhaseDto[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await listPhases();
        if (!isMounted) {
          return;
        }
        setPhases(response.data || []);
      } catch (err) {
        if (!isMounted) {
          return;
        }
        const message = err instanceof Error ? err.message : "Unable to load phases.";
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
      <span className="metatheos-kicker">Layers</span>
      <h1>Phases</h1>
      <p className="metatheos-muted">Current and archived governance phases.</p>
      <div className="metatheos-divider" />
      <section className="metatheos-panel">
        {error ? <div className="metatheos-error">{error}</div> : null}
        {isLoading ? (
          <div className="metatheos-muted">Loading phases...</div>
        ) : phases.length ? (
          <ul className="metatheos-list">
            {phases.map((phase) => (
              <li key={phase.id}>
                <div>{phase.title}</div>
                <div className="metatheos-muted">
                  {phase.status}
                  {formatDate(phase.start_date) ? ` · started ${formatDate(phase.start_date)}` : ""}
                  {formatDate(phase.target_date) ? ` · target ${formatDate(phase.target_date)}` : ""}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="metatheos-muted">No phases available.</div>
        )}
      </section>
    </div>
  );
};

export default Phases;
