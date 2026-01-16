import { useState } from "react";
import { Menu, X, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import Logo from "./Logo";
import { ThemeToggle } from "./ThemeToggle";

const navItems = [
  { label: "Chambers", href: "#features" },
  { label: "Scribe's Chamber", href: "#chartforge" },
  { label: "Tariffs", href: "#pricing" },
  { label: "Chronicles", href: "#about" },
];

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/90 backdrop-blur-xl border-b border-border/50">
      {/* Top decorative line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold/30 to-transparent" />

      <div className="container mx-auto px-6">
        <div className="flex items-center justify-between h-16 lg:h-20">
          <Logo />

          {/* Desktop Navigation - Columned arcade style */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item, i) => (
              <a
                key={item.label}
                href={item.href}
                className="relative px-5 py-2 text-muted-foreground hover:text-foreground transition-colors font-body text-sm font-medium group"
              >
                <span className="relative z-10">{item.label}</span>
                {/* Column hover effect */}
                <div className="absolute inset-0 bg-gold/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-sm" />
                {/* Separator column */}
                {i < navItems.length - 1 && (
                  <div className="absolute right-0 top-1/4 bottom-1/4 w-px bg-border/50" />
                )}
              </a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            <ThemeToggle />
            {/* Metatheos Admin Access - Separate Container */}
            <Link to="/login">
              <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground" title="Metatheos Admin">
                <Lock className="h-4 w-4" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
                Enter
              </Button>
            </Link>
            <Link to="/register">
              <Button variant="gold" size="sm">
                Join the Fellowship
              </Button>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden text-foreground p-2 rounded-sm hover:bg-secondary/50 transition-colors"
            onClick={() => setIsOpen(!isOpen)}
          >
            {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>

        {/* Mobile Navigation - Scroll panel style */}
        {isOpen && (
          <div className="md:hidden py-4 border-t border-border/50 bg-card/50 rounded-b-sm">
            <div className="flex flex-col gap-1">
              {navItems.map((item) => (
                <a
                  key={item.label}
                  href={item.href}
                  className="text-muted-foreground hover:text-foreground hover:bg-gold/5 transition-colors font-body text-sm font-medium py-3 px-4 rounded-sm"
                  onClick={() => setIsOpen(false)}
                >
                  {item.label}
                </a>
              ))}
              <div className="flex flex-col gap-3 pt-4 mt-4 border-t border-border/50 px-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Theme</span>
                  <ThemeToggle />
                </div>
                <Link to="/login">
                  <Button variant="ghost" size="sm" className="justify-start w-full">
                    Enter
                  </Button>
                </Link>
                <Link to="/register">
                  <Button variant="gold" size="sm" className="w-full">
                    Join the Fellowship
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
