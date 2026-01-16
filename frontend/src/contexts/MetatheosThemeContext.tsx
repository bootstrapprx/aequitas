import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

export type MetatheosTheme = "light" | "dark";

interface MetatheosThemeContextValue {
  theme: MetatheosTheme;
  setTheme: (theme: MetatheosTheme) => void;
  toggleTheme: () => void;
}

const MetatheosThemeContext = createContext<MetatheosThemeContextValue | undefined>(undefined);

const STORAGE_KEY = "metatheos_theme";

export const MetatheosThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<MetatheosTheme>(() => {
    if (typeof window === "undefined") {
      return "dark";
    }
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : "dark";
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  const value = useMemo(
    () => ({
      theme,
      setTheme: (nextTheme: MetatheosTheme) => setThemeState(nextTheme),
      toggleTheme: () => setThemeState((prev) => (prev === "dark" ? "light" : "dark")),
    }),
    [theme]
  );

  return <MetatheosThemeContext.Provider value={value}>{children}</MetatheosThemeContext.Provider>;
};

export const useMetatheosTheme = () => {
  const context = useContext(MetatheosThemeContext);
  if (!context) {
    throw new Error("useMetatheosTheme must be used within MetatheosThemeProvider");
  }
  return context;
};
