import React, { useState } from 'react';
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  Landmark,
  Building,
  Scroll,
  Feather,
  Binoculars,
  Users,
  Archive,
  ChevronLeft,
  ChevronRight,
  LogOut,
  User,
  ChevronDown,
  LayoutDashboard,
  Shield,
  Settings,
  Scale,
  Calendar,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ThemeToggle";
import { PaletteSelector } from "@/components/PaletteSelector";
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
    'treasury',
    'agora',
    'scribe',
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

  // Navigation structure - The Digital Athenaeum
  const navSections: Record<string, NavSection> = {
    treasury: {
      title: "TREASURY",
      icon: Landmark,
      links: [
        { label: "Overview", path: "/dashboard", icon: LayoutDashboard },
      ],
    },
    agora: {
      title: "AGORA",
      icon: Building,
      links: [
        { label: "Companies", path: "/companies", icon: Building },
        { label: "My Chart", path: "/chartofaccounts", icon: Scroll },
      ],
    },
    scribe: {
      title: "SCRIBE'S CHAMBER",
      icon: Feather,
      links: [
        { label: "Daily Ledger", path: "/accountancy/ledger", icon: Scroll },
        { label: "Journal Entries", path: "/accountancy/journal", icon: Feather },
        { label: "Trial Balance", path: "/accountancy/trial-balance", icon: Scale },
        { label: "Fiscal Periods", path: "/accountancy/fiscal-periods", icon: Calendar },
      ],
    },
    auditor: {
      title: "AUDITOR'S TOWER",
      icon: Binoculars,
      links: [
        { label: "Financial Statements", path: "/reports/statements", icon: Scroll },
        { label: "Custom Reports", path: "/reports/custom", icon: Binoculars },
        { label: "Export Center", path: "/reports/export", icon: Archive },
      ],
    },
    council: {
      title: "COUNCIL HALL",
      icon: Users,
      links: [
        ...(user?.is_superuser ? [{ label: "Superuser Panel", path: "/admin/superuser", icon: Shield }] : []),
        { label: "System Settings", path: "/admin/system", icon: Settings },
        { label: "Users", path: "/registration/users", icon: Users },
      ],
    },
    archives: {
      title: "ARCHIVES",
      icon: Archive,
      links: [
        { label: "Template Catalog", path: "/chartofaccounts/master", icon: Archive },
        { label: "Audit Log", path: "/admin/audit", icon: Scroll },
      ],
    },
  };

  return (
    <div
      className={cn(
        "flex flex-col h-screen bg-sidebar text-sidebar-foreground border-r border-sidebar-border transition-all duration-300 marble-texture relative z-10",
        isOpen ? "w-72" : "w-20"
      )}
    >
      {/* Column Pattern Overlay */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03] column-pattern mix-blend-multiply" />


      {/* Header with Logo and Toggle */}
      <div className="relative z-10 flex items-center justify-between p-6 border-b border-sidebar-border/50">
        {isOpen && (
          <Link to="/dashboard" className="flex items-center space-x-3 group animate-fade-up">
            <div className="relative">
              <div className="absolute inset-0 bg-gold/20 blur-xl rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
              <span className="text-3xl relative z-10">⚖️</span>
            </div>

            <span className="text-2xl font-heading font-bold text-gradient-gold tracking-wide">
              Aequitas
            </span>
          </Link>
        )}
        {!isOpen && (
          <Link to="/dashboard" className="flex items-center justify-center w-full">
            <span className="text-2xl drop-shadow-lg">⚖️</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggle}
          className={cn("ml-auto text-sidebar-foreground/70 hover:text-gold hover:bg-gold/10", !isOpen && "mx-auto")}
        >
          {isOpen ? (
            <ChevronLeft className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {/* Sections */}
        {Object.entries(navSections).map(([sectionId, section]) => (
          <Collapsible
            key={sectionId}
            open={isSectionOpen(sectionId)}
            onOpenChange={() => toggleSection(sectionId)}
            className="group/section"
          >
            <CollapsibleTrigger asChild>
              <button
                className={cn(
                  "flex items-center justify-between w-full px-3 py-3 text-xs font-bold text-sidebar-foreground/60 font-heading tracking-widest uppercase hover:text-gold transition-all duration-300 border-b border-transparent hover:border-gold/20",
                  !isOpen && "justify-center"
                )}
              >
                {isOpen ? (
                  <>
                    <div className="flex items-center space-x-3">
                      <span className="p-1 rounded bg-sidebar-accent/50 text-gold group-hover/section:text-gold-light transition-colors">
                        <section.icon className="h-4 w-4" />
                      </span>
                      <span>{section.title}</span>
                    </div>
                    <ChevronDown
                      className={cn(
                        "h-3 w-3 transition-transform duration-300 opacity-50",
                        isSectionOpen(sectionId) && "transform rotate-180 opacity-100 text-gold"
                      )}
                    />
                  </>
                ) : (
                  <div className="relative group/tooltip">
                    <section.icon className="h-5 w-5 text-sidebar-foreground/70 hover:text-gold transition-colors" />
                  </div>
                )}
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent className="space-y-1 mt-2 ml-1 border-l border-sidebar-border/50 pl-2 animate-accordion-down">
              {section.links.map((link) => {
                const Icon = link.icon;
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={cn(
                      "flex items-center space-x-3 px-3 py-2 rounded-md transition-all duration-300 text-sm border border-transparent",
                      isActive(link.path)
                        ? "bg-gold/10 text-gold border-gold/20 shadow-sm shadow-gold/5 font-medium"
                        : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-gold-light hover:translate-x-1",
                      !isOpen && "justify-center px-0 py-3 hover:bg-transparent"
                    )}
                  >
                    {Icon && <Icon className={cn("h-4 w-4 flex-shrink-0", isActive(link.path) && "animate-pulse-glow")} />}
                    {isOpen && <span>{link.label}</span>}
                  </Link>
                );
              })}
            </CollapsibleContent>
          </Collapsible>
        ))}
      </nav>

      {/* Footer with User Profile and Theme Toggle */}
      <div className="relative z-10 border-t border-sidebar-border/50 p-4 space-y-4 bg-sidebar/50 backdrop-blur-sm">
        {isOpen && (
          <div className="flex items-center justify-between">
            <span className="text-xs font-heading text-sidebar-foreground/40 uppercase tracking-widest">Theme</span>
            <div className="flex items-center gap-1">
              <PaletteSelector />
              <ThemeToggle />
            </div>
          </div>
        )}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              className={cn(
                "flex items-center space-x-3 w-full px-3 py-2.5 rounded-lg border border-transparent hover:border-gold/30 hover:bg-gold/5 transition-all duration-300 group",
                !isOpen && "justify-center"
              )}
            >
              <div className="relative">
                <div className="absolute inset-0 bg-emerald/20 rounded-full blur-sm group-hover:bg-emerald/30 transition-all" />
                <div className="relative flex items-center justify-center w-9 h-9 rounded-full bg-gradient-emerald text-white font-bold font-heading shadow-lg border border-emerald-light/20">
                  {user?.email?.[0].toUpperCase() || 'U'}
                </div>
              </div>

              {isOpen && (
                <div className="flex-1 text-left">
                  <p className="text-sm font-bold text-sidebar-foreground font-heading group-hover:text-gold transition-colors">
                    {user?.email?.split('@')[0] || 'User'}
                  </p>
                  <p className="text-xs text-sidebar-foreground/50 truncate max-w-[120px]">
                    {user?.is_superuser ? 'Scribe' : 'Council Member'}
                  </p>
                </div>
              )}
              {isOpen && <ChevronDown className="h-4 w-4 text-sidebar-foreground/50 group-hover:text-gold" />}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-60 bg-sidebar border-sidebar-border text-sidebar-foreground shadow-2xl shadow-black/50">
            <DropdownMenuLabel className="font-heading text-gold">My Identity</DropdownMenuLabel>
            <DropdownMenuSeparator className="bg-sidebar-border" />
            <DropdownMenuItem onClick={() => navigate('/settings')} className="focus:bg-sidebar-accent focus:text-gold cursor-pointer">
              <User className="mr-2 h-4 w-4" />
              Profile Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator className="bg-sidebar-border" />
            <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:bg-destructive/10 focus:text-destructive cursor-pointer">
              <LogOut className="mr-2 h-4 w-4" />
              Return to Gateway
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};

export default AequitasSidebar;
