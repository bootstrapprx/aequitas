import React, { useState } from 'react';
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Building2,
  Users,
  FileText,
  Database,
  GitBranch,
  Upload,
  Wand2,
  BookOpen,
  Receipt,
  Scale,
  BarChart3,
  FileSpreadsheet,
  Download,
  Settings,
  Plug,
  ScrollText,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User,
  ChevronDown,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/contexts/AuthContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useNavigate } from "react-router-dom";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";

interface NavLink {
  label: string;
  path: string;
  icon?: React.ElementType;
}

interface NavSection {
  title: string;
  icon: React.ElementType;
  links: NavLink[];
  defaultOpen?: boolean;
}

const AequitasSidebar = () => {
  const [isOpen, setIsOpen] = useState(true);
  const [openSections, setOpenSections] = useState<string[]>([
    'registration',
    'chartforge',
  ]);
  const location = useLocation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const onToggle = () => setIsOpen(!isOpen);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const toggleSection = (sectionId: string) => {
    setOpenSections((prev) =>
      prev.includes(sectionId)
        ? prev.filter((id) => id !== sectionId)
        : [...prev, sectionId]
    );
  };

  const isSectionOpen = (sectionId: string) => openSections.includes(sectionId);

  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return location.pathname === '/dashboard';
    }
    return location.pathname.startsWith(path);
  };

  // Navigation structure
  const navSections: Record<string, NavSection> = {
    registration: {
      title: "REGISTRATION",
      icon: FileText,
      links: [
        { label: "Companies", path: "/companies", icon: Building2 },
        { label: "Users", path: "/registration/users", icon: Users },
        { label: "Chart of Accounts", path: "/registration/coa", icon: FileText },
      ],
    },
    chartforge: {
      title: "CHARTFORGE",
      icon: Database,
      links: [
        { label: "Master Chart", path: "/chartforge/masterchart", icon: Database },
        { label: "Mapping", path: "/chartforge/mapping", icon: GitBranch },
        { label: "Import / Export", path: "/chartforge/import", icon: Upload },
        { label: "AI Organizer", path: "/chartforge/organizer", icon: Wand2 },
      ],
    },
    accountancy: {
      title: "ACCOUNTANCY",
      icon: BookOpen,
      links: [
        { label: "Daily Ledger", path: "/accountancy/ledger", icon: Receipt },
        { label: "Ledger Accounts", path: "/accountancy/journal", icon: BookOpen },
        { label: "Trial Balance", path: "/accountancy/trial-balance", icon: Scale },
      ],
    },
    reports: {
      title: "REPORTS",
      icon: BarChart3,
      links: [
        { label: "Financial Statements", path: "/reports/statements", icon: FileSpreadsheet },
        { label: "Custom Reports", path: "/reports/custom", icon: BarChart3 },
        { label: "Export Center", path: "/reports/export", icon: Download },
      ],
    },
    administration: {
      title: "ADMINISTRATION",
      icon: Settings,
      links: [
        { label: "System Settings", path: "/admin/system", icon: Settings },
        { label: "Integrations", path: "/admin/integrations", icon: Plug },
        { label: "Audit Log", path: "/admin/audit", icon: ScrollText },
      ],
    },
  };

  return (
    <div
      className={cn(
        "flex flex-col h-screen bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300",
        isOpen ? "w-72" : "w-16"
      )}
    >
      {/* Header with Logo and Toggle */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
        {isOpen && (
          <Link to="/dashboard" className="flex items-center space-x-2">
            <span className="text-2xl">⚖️</span>
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              Aequitas
            </span>
          </Link>
        )}
        {!isOpen && (
          <Link to="/dashboard" className="flex items-center justify-center w-full">
            <span className="text-2xl">⚖️</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className={cn("ml-auto", !isOpen && "mx-auto")}
        >
          {isOpen ? (
            <ChevronLeft className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-2">
        {/* Dashboard - Always visible */}
        <Link
          to="/dashboard"
          className={cn(
            "flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors",
            isActive("/dashboard")
              ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 font-medium"
              : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
          )}
        >
          <LayoutDashboard className="h-5 w-5 flex-shrink-0" />
          {isOpen && <span>Dashboard</span>}
        </Link>

        {/* Sections */}
        {Object.entries(navSections).map(([sectionId, section]) => (
          <Collapsible
            key={sectionId}
            open={isSectionOpen(sectionId)}
            onOpenChange={() => toggleSection(sectionId)}
          >
            <CollapsibleTrigger asChild>
              <button
                className={cn(
                  "flex items-center justify-between w-full px-3 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider hover:text-gray-700 dark:hover:text-gray-300 transition-colors",
                  !isOpen && "justify-center"
                )}
              >
                {isOpen ? (
                  <>
                    <span>{section.title}</span>
                    <ChevronDown
                      className={cn(
                        "h-4 w-4 transition-transform",
                        isSectionOpen(sectionId) && "transform rotate-180"
                      )}
                    />
                  </>
                ) : (
                  <section.icon className="h-5 w-5" />
                )}
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-1 mt-1">
              {section.links.map((link) => {
                const Icon = link.icon;
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={cn(
                      "flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors text-sm",
                      isActive(link.path)
                        ? "bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 font-medium"
                        : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800",
                      !isOpen && "justify-center"
                    )}
                  >
                    {Icon && <Icon className="h-4 w-4 flex-shrink-0" />}
                    {isOpen && <span>{link.label}</span>}
                  </Link>
                );
              })}
            </CollapsibleContent>
          </Collapsible>
        ))}
      </nav>

      {/* Footer with User Profile and Theme Toggle */}
      <div className="border-t border-gray-200 dark:border-gray-800 p-4 space-y-2">
        {isOpen && (
          <div className="flex items-center justify-between mb-2">
            <ThemeToggle />
          </div>
        )}
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className={cn(
                "flex items-center space-x-3 w-full px-3 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors",
                !isOpen && "justify-center"
              )}
            >
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-400 font-semibold">
                {user?.email?.[0].toUpperCase() || 'U'}
              </div>
              {isOpen && (
                <div className="flex-1 text-left">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {user?.email || 'User'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {user?.is_superuser ? 'Superuser' : 'User'}
                  </p>
                </div>
              )}
              {isOpen && <ChevronDown className="h-4 w-4 text-gray-500" />}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate('/settings')}>
              <User className="mr-2 h-4 w-4" />
              Profile Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-red-600">
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};

export default AequitasSidebar;
