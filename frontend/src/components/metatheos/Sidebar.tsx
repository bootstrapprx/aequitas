import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Home", path: "/home" },
  { label: "Phases", path: "/phases" },
  { label: "Goals", path: "/goals" },
  { label: "Timeline", path: "/timeline" },
  { label: "Audits", path: "/audits" },
  { label: "Prompts", path: "/prompts" },
  { label: "Assistant", path: "/assistant" },
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
