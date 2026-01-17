import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import MetatheosSurface from "@/components/metatheos/MetatheosSurface";
import { useMetatheosAuth } from "@/contexts/MetatheosAuthContext";

const Login = () => {
  const { login } = useMetatheosAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login(identifier, password);
      navigate("/metatheos/home");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <MetatheosSurface className="metatheos-login">
      <div className="metatheos-login-card metatheos-fade-in">
        <div>
          <div className="metatheos-kicker">Metatheos</div>
          <h1>Admin Access</h1>
        </div>
        <form onSubmit={handleSubmit} className="metatheos-login-fields">
          <div>
            <label htmlFor="identifier">Username / Email</label>
            <input
              id="identifier"
              name="identifier"
              className="metatheos-input"
              type="text"
              autoComplete="username"
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              className="metatheos-input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>
          {error ? <div className="metatheos-error">{error}</div> : null}
          <button type="submit" className="metatheos-button metatheos-button--primary" disabled={isSubmitting}>
            {isSubmitting ? "Entering" : "Enter"}
          </button>
        </form>
      </div>
    </MetatheosSurface>
  );
};

export default Login;
