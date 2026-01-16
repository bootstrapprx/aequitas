import { useNavigate } from "react-router-dom";
import { useMetatheosAuth } from "@/contexts/MetatheosAuthContext";
import { useMetatheosTheme } from "@/contexts/MetatheosThemeContext";

const TopBar = () => {
  const { logout } = useMetatheosAuth();
  const { theme, toggleTheme } = useMetatheosTheme();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <header className="metatheos-topbar">
      <div className="metatheos-topbar-title">
        <span>Metatheos</span>
        <span className="metatheos-kicker">Governance Shell</span>
      </div>
      <div className="metatheos-topbar-actions">
        <button type="button" className="metatheos-button metatheos-button--ghost" onClick={toggleTheme}>
          {theme === "dark" ? "Light" : "Dark"}
        </button>
        <button type="button" className="metatheos-button metatheos-button--ghost" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
};

export default TopBar;
