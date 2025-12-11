import { Scale } from "lucide-react";

const Logo = () => {
  return (
    <div className="flex items-center gap-3">
      {/* Classical Column-inspired icon container */}
      <div className="relative">
        <div className="w-10 h-10 rounded-sm bg-gradient-stone stone-border flex items-center justify-center">
          <Scale className="h-5 w-5 text-gold" />
        </div>
        {/* Decorative corner accents */}
        <div className="absolute -top-0.5 -left-0.5 w-2 h-2 border-l border-t border-gold/40" />
        <div className="absolute -top-0.5 -right-0.5 w-2 h-2 border-r border-t border-gold/40" />
        <div className="absolute -bottom-0.5 -left-0.5 w-2 h-2 border-l border-b border-gold/40" />
        <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 border-r border-b border-gold/40" />
      </div>
      <div className="flex flex-col">
        <span className="font-heading text-xl font-bold text-foreground tracking-wide text-engraved">
          AEQUITAS
        </span>
        <span className="text-[9px] uppercase tracking-[0.25em] text-gold/80 font-body font-medium -mt-0.5">
          Digital Athenaeum
        </span>
      </div>
    </div>
  );
};

export default Logo;