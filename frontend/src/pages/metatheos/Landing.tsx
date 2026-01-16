import { Link } from "react-router-dom";
import MetatheosSurface from "@/components/metatheos/MetatheosSurface";

const Landing = () => {
  return (
    <MetatheosSurface className="metatheos-landing">
      <div className="metatheos-landing-inner metatheos-fade-in">
        <span className="metatheos-kicker">Metatheos</span>
        <h1 className="metatheos-landing-title">Threshold</h1>
        <p>Observation, governance, verification.</p>
        <p className="metatheos-muted">Admin access only.</p>
        <div>
          <Link to="/login" className="metatheos-button metatheos-button--primary">
            Enter
          </Link>
        </div>
      </div>
    </MetatheosSurface>
  );
};

export default Landing;
