import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Home", path: "/metatheos/home" },
  { label: "Phases", path: "/metatheos/phases" },
  { label: "Goals", path: "/metatheos/goals" },
  { label: "Timeline", path: "/metatheos/timeline" },
  { label: "Audits", path: "/metatheos/audits" },
  { label: "Prompts", path: "/metatheos/prompts" },
  { label: "Assistant", path: "/metatheos/assistant" },
];

const Sidebar = () => {
  return (
    <aside className="metatheos-sidebar">
      <div>
        <div className="metatheos-kicker">Metatheos</div>
        <div className="metatheos-brand">Observatory</div>
      </div>
      <div>
        <div className="metatheos-kicker">Layers</div>
        <nav className="metatheos-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn("metatheos-nav-link", isActive && "metatheos-nav-link--active")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;
