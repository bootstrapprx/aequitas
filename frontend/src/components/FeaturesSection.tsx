import { 
  Building2, 
  ScrollText, 
  FileText, 
  Settings, 
  Sparkles, 
  Eye,
  Vault,
  Shield
} from "lucide-react";

const sectors = [
  {
    icon: Vault,
    title: "Treasury",
    description: "The vault with golden ledgers—bank accounts, assets, and liabilities secured within stone walls.",
    visual: "vault",
    accent: "gold",
  },
  {
    icon: Building2,
    title: "Agora",
    description: "The open marketplace—invoicing, payables, and receivables flow like merchants through ancient stalls.",
    visual: "marketplace",
    accent: "emerald",
  },
  {
    icon: ScrollText,
    title: "Scribe's Chamber",
    description: "Parchment and quills digitized—journal entries and automation rules crafted with precision.",
    visual: "scrolls",
    accent: "gold",
  },
  {
    icon: Eye,
    title: "Auditor's Tower",
    description: "The watchtower with eagle motifs—audit logs, compliance tracking, and oversight reports.",
    visual: "tower",
    accent: "emerald",
  },
  {
    icon: Sparkles,
    title: "Oracle's Pool",
    description: "AI-powered insights surface from the depths—ChartForge maps your financial future.",
    visual: "pool",
    accent: "gold",
  },
  {
    icon: FileText,
    title: "The Archives",
    description: "A library of floating scrolls—reports generate as unfurling parchments ready to seal.",
    visual: "library",
    accent: "emerald",
  },
  {
    icon: Settings,
    title: "Chamber of Gears",
    description: "System settings and integrations—the hidden machinery that powers the Athenaeum.",
    visual: "gears",
    accent: "gold",
  },
  {
    icon: Shield,
    title: "Guardian's Gate",
    description: "Bank-grade encryption and the watchful Digicerberus protect your empire's wealth.",
    visual: "gate",
    accent: "emerald",
  },
];

const FeaturesSection = () => {
  return (
    <section id="features" className="py-24 relative overflow-hidden">
      {/* Background texture */}
      <div className="absolute inset-0 bg-secondary/40 marble-texture" />
      
      {/* Decorative border lines */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold/20 to-transparent" />
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold/20 to-transparent" />
      
      <div className="container mx-auto px-6 relative z-10">
        {/* Section Header - Classical pediment style */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center justify-center gap-4 mb-6">
            <div className="h-px w-16 bg-gradient-to-r from-transparent to-gold/50" />
            <span className="text-gold text-sm font-body font-semibold uppercase tracking-[0.2em]">
              The Sectors
            </span>
            <div className="h-px w-16 bg-gradient-to-l from-transparent to-gold/50" />
          </div>
          <h2 className="text-3xl md:text-5xl font-heading font-bold mb-6 text-engraved">
            Navigate the{" "}
            <span className="text-gradient-gold">Chambers</span>
          </h2>
          <p className="text-muted-foreground text-lg font-body leading-relaxed">
            Each sector is a distinct chamber with its own purpose and aesthetic—
            from the Treasury's vaults to the Oracle's mystic pool.
          </p>
        </div>

        {/* Sectors Grid - Styled as chamber doorways */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {sectors.map((sector, index) => (
            <div
              key={sector.title}
              className="group relative p-6 rounded-sm bg-gradient-stone stone-border hover:shadow-gold transition-all duration-500 hover:-translate-y-1 cursor-pointer"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Doorway arch effect at top */}
              <div className="absolute top-0 left-4 right-4 h-1 rounded-b-full bg-gradient-to-r from-transparent via-gold/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              
              {/* Icon in carved alcove */}
              <div className={`relative inline-flex p-4 rounded-sm mb-4 transition-all duration-300 group-hover:scale-105 ${
                sector.accent === 'gold' 
                  ? 'bg-gold/10 border border-gold/20' 
                  : 'bg-emerald/10 border border-emerald/20'
              }`}>
                <sector.icon className={`h-6 w-6 ${
                  sector.accent === 'gold' ? 'text-gold' : 'text-emerald'
                }`} />
                {/* Decorative corner */}
                <div className={`absolute -top-1 -right-1 w-2 h-2 ${
                  sector.accent === 'gold' ? 'bg-gold/50' : 'bg-emerald/50'
                } rounded-full opacity-0 group-hover:opacity-100 transition-opacity`} />
              </div>

              {/* Content */}
              <h3 className="font-heading text-lg font-semibold mb-2 text-foreground text-engraved">
                {sector.title}
              </h3>
              <p className="text-muted-foreground text-sm font-body leading-relaxed">
                {sector.description}
              </p>

              {/* Enter indicator */}
              <div className="mt-4 flex items-center gap-2 text-xs uppercase tracking-wider opacity-0 group-hover:opacity-100 transition-opacity">
                <span className={sector.accent === 'gold' ? 'text-gold' : 'text-emerald'}>
                  Enter Chamber
                </span>
                <span className={`${sector.accent === 'gold' ? 'text-gold' : 'text-emerald'}`}>→</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default FeaturesSection;