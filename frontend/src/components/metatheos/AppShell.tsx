import { Outlet } from "react-router-dom";
import MetatheosSurface from "@/components/metatheos/MetatheosSurface";
import Sidebar from "@/components/metatheos/Sidebar";
import TopBar from "@/components/metatheos/TopBar";

const AppShell = () => {
  return (
    <MetatheosSurface className="metatheos-shell">
      <Sidebar />
      <div className="metatheos-main">
        <TopBar />
        <div className="metatheos-content">
          <Outlet />
        </div>
      </div>
    </MetatheosSurface>
  );
};

export default AppShell;
