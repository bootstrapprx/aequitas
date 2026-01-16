import React from "react";
import { cn } from "@/lib/utils";
import { useMetatheosTheme } from "@/contexts/MetatheosThemeContext";

interface MetatheosSurfaceProps {
  children: React.ReactNode;
  className?: string;
}

const MetatheosSurface = ({ children, className }: MetatheosSurfaceProps) => {
  const { theme } = useMetatheosTheme();

  return (
    <div className={cn("metatheos", className)} data-theme={theme}>
      {children}
    </div>
  );
};

export default MetatheosSurface;
