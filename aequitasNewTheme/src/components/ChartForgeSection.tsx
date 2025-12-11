import { Sparkles, ScrollText, Feather, Search } from "lucide-react";
import { Button } from "@/components/ui/button";

const capabilities = [
  {
    icon: Sparkles,
    title: "Oracle's Vision",
    description: "AI-powered account classification that sees patterns mortals cannot.",
  },
  {
    icon: ScrollText,
    title: "Scroll Automation",
    description: "Rules inscribed once, executed eternally—automate your ledger entries.",
  },
  {
    icon: Feather,
    title: "Quill Interface",
    description: "Every entry feels like writing on parchment—tactile and precise.",
  },
  {
    icon: Search,
    title: "Crystal Ball Search",
    description: "Find any record in the Archives with mystical search powers.",
  },
];

const ChartForgeSection = () => {
  return (
    <section id="chartforge" className="py-24 relative overflow-hidden">
      {/* Background Pattern - Subtle parchment texture */}
      <div className="absolute inset-0 marble-texture" />
      <div className="absolute inset-0 opacity-[0.03]">
        <div className="absolute inset-0" style={{
          backgroundImage: `radial-gradient(circle at 2px 2px, hsl(var(--gold)) 1px, transparent 0)`,
          backgroundSize: "32px 32px",
        }} />
      </div>

      <div className="container mx-auto px-6 relative z-10">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Content */}
          <div>
            <div className="inline-flex items-center gap-3 mb-6">
              <div className="h-px w-8 bg-emerald/50" />
              <span className="text-emerald text-sm font-body font-semibold uppercase tracking-[0.15em]">
                The Scribe's Chamber
              </span>
            </div>
            <h2 className="text-3xl md:text-5xl font-heading font-bold mb-6 text-engraved">
              ChartForge{" "}
              <span className="text-gradient-emerald">Engine</span>
            </h2>
            <p className="text-muted-foreground text-lg font-body mb-10 leading-relaxed">
              Within the Scribe's Chamber, ChartForge weaves AI magic into your chart 
              of accounts. Watch as the quill moves on its own, mapping accounts with 
              ancient precision and modern intelligence.
            </p>

            {/* Capabilities - Styled as scroll items */}
            <div className="grid sm:grid-cols-2 gap-6 mb-10">
              {capabilities.map((cap) => (
                <div key={cap.title} className="flex gap-4 group">
                  <div className="flex-shrink-0 w-12 h-12 rounded-sm bg-emerald/10 border border-emerald/20 flex items-center justify-center group-hover:shadow-glow transition-shadow">
                    <cap.icon className="h-5 w-5 text-emerald" />
                  </div>
                  <div>
                    <h4 className="font-heading font-semibold text-foreground mb-1">
                      {cap.title}
                    </h4>
                    <p className="text-muted-foreground text-sm font-body">
                      {cap.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <Button variant="default" size="lg" className="group">
              <Feather className="mr-2 h-4 w-4 group-hover:animate-quill" />
              Enter the Chamber
            </Button>
          </div>

          {/* Visual - Scribe's Desk with Parchment */}
          <div className="relative">
            <div className="relative bg-gradient-stone rounded-sm stone-border p-8 shadow-card">
              {/* Parchment header */}
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border/50">
                <div className="w-8 h-8 rounded-sm bg-gold/20 flex items-center justify-center">
                  <ScrollText className="h-4 w-4 text-gold" />
                </div>
                <div>
                  <span className="text-foreground font-heading font-semibold">Chart of Accounts</span>
                  <span className="block text-xs text-muted-foreground">Mapped by ChartForge AI</span>
                </div>
                <div className="ml-auto flex items-center gap-2">
                  <Feather className="h-4 w-4 text-gold/50 animate-quill" />
                </div>
              </div>

              {/* Mock Chart of Accounts - Scroll style */}
              <div className="space-y-2">
                {[
                  { code: "I", name: "Assets", type: "Header", confidence: 100 },
                  { code: "I.I", name: "Cash & Gold Reserves", type: "Account", confidence: 98 },
                  { code: "I.II", name: "Trade Receivables", type: "Account", confidence: 96 },
                  { code: "II", name: "Liabilities", type: "Header", confidence: 100 },
                  { code: "II.I", name: "Debts Owed", type: "Account", confidence: 94 },
                  { code: "III", name: "Empire's Equity", type: "Header", confidence: 100 },
                ].map((account) => (
                  <div
                    key={account.code}
                    className={`flex items-center justify-between p-3 rounded-sm transition-all ${
                      account.type === "Header" 
                        ? "bg-gold/10 border-l-2 border-gold" 
                        : "bg-secondary/30 hover:bg-secondary/50"
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <span className="font-heading text-sm text-gold/80 w-10">
                        {account.code}
                      </span>
                      <span className={`font-body text-sm ${
                        account.type === "Header" ? "font-semibold text-gold" : "text-foreground"
                      }`}>
                        {account.name}
                      </span>
                    </div>
                    {account.type !== "Header" && (
                      <div className="flex items-center gap-2">
                        <Sparkles className="h-3 w-3 text-emerald" />
                        <span className="text-xs text-emerald font-body">
                          {account.confidence}%
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Processing Indicator */}
              <div className="mt-6 flex items-center gap-3 pt-4 border-t border-border/50">
                <div className="w-4 h-4 border-2 border-emerald/30 border-t-emerald rounded-full animate-spin" />
                <span className="text-sm font-body text-emerald">The Oracle maps your accounts...</span>
              </div>
            </div>

            {/* Floating Seal Badge */}
            <div className="absolute -top-4 -right-4 px-4 py-3 rounded-sm bg-gradient-gold shadow-gold animate-float">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-accent-foreground/20 flex items-center justify-center">
                  <Sparkles className="h-3 w-3 text-accent-foreground" />
                </div>
                <span className="text-accent-foreground font-heading font-bold text-sm">
                  98% Accuracy
                </span>
              </div>
            </div>

            {/* Decorative corner scroll */}
            <div className="absolute -bottom-2 -left-2 w-16 h-16 opacity-20">
              <svg viewBox="0 0 100 100" className="w-full h-full text-gold">
                <path d="M0,100 Q0,0 100,0" fill="none" stroke="currentColor" strokeWidth="2" />
                <path d="M10,100 Q10,10 100,10" fill="none" stroke="currentColor" strokeWidth="1" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ChartForgeSection;