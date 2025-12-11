import { Button } from "@/components/ui/button";
import { ArrowRight, Play, Columns, BookOpen, Shield } from "lucide-react";

const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Marble Background with Texture */}
      <div className="absolute inset-0 z-0 bg-background marble-texture">
        {/* Column pillars effect on sides */}
        <div className="absolute left-0 top-0 bottom-0 w-24 opacity-20">
          <div className="h-full w-full" style={{
            background: `repeating-linear-gradient(90deg, 
              transparent 0px, 
              hsl(var(--gold) / 0.1) 2px, 
              transparent 4px, 
              transparent 24px)`
          }} />
        </div>
        <div className="absolute right-0 top-0 bottom-0 w-24 opacity-20">
          <div className="h-full w-full" style={{
            background: `repeating-linear-gradient(90deg, 
              transparent 0px, 
              hsl(var(--gold) / 0.1) 2px, 
              transparent 4px, 
              transparent 24px)`
          }} />
        </div>
        
        {/* Ambient light from "torches" */}
        <div className="absolute top-1/4 left-20 w-64 h-64 bg-gold/8 rounded-full blur-[100px] animate-torch" />
        <div className="absolute top-1/4 right-20 w-64 h-64 bg-gold/8 rounded-full blur-[100px] animate-torch animation-delay-500" />
        <div className="absolute bottom-1/3 left-1/3 w-96 h-96 bg-emerald/5 rounded-full blur-[120px]" />
        
        {/* Decorative Greek key pattern at top */}
        <div className="absolute top-20 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold/30 to-transparent" />
        <div className="absolute top-24 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold/15 to-transparent" />
      </div>

      {/* Content */}
      <div className="relative z-10 container mx-auto px-6 py-20 text-center">
        <div className="max-w-4xl mx-auto">
          {/* Architrave Badge */}
          <div className="inline-flex items-center gap-3 px-5 py-2.5 rounded-sm stone-border bg-card/50 mb-10 opacity-0 animate-fade-up">
            <div className="w-6 h-6 rounded-sm bg-gold/20 flex items-center justify-center">
              <Columns className="w-3 h-3 text-gold" />
            </div>
            <span className="text-gold text-sm font-body font-medium tracking-wide">
              The Digital Athenaeum of Finance
            </span>
          </div>

          {/* Main Headline - Engraved Style */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-heading font-bold leading-tight mb-6 opacity-0 animate-fade-up animation-delay-100">
            <span className="text-foreground text-engraved">Manage Your</span>
            <br />
            <span className="text-gradient-gold">Empire's Wealth</span>
          </h1>

          {/* Classical Subheadline */}
          <p className="text-xl md:text-2xl font-heading italic text-gold-light/80 mb-6 opacity-0 animate-fade-up animation-delay-200">
            "Ancient Wisdom, Modern Software"
          </p>

          {/* Descriptive Text */}
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-12 font-body leading-relaxed opacity-0 animate-fade-up animation-delay-300">
            Secure. Precise. Equitable. Enter the Athenaeum—where the gravitas of 
            ancient financial institutions meets cutting-edge AI technology.
          </p>

          {/* CTA Buttons styled as stone tablets */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 opacity-0 animate-fade-up animation-delay-400">
            <Button variant="gold" size="xl" className="group">
              <span>Enter the Atrium</span>
              <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Button>
            <Button variant="outline" size="xl" className="group border-gold/30 hover:bg-gold/10 hover:border-gold/50">
              <Play className="mr-2 h-5 w-5" />
              <span>View the Archives</span>
            </Button>
          </div>

          {/* Sector Preview - The Pathways */}
          <div className="mt-20 pt-10 border-t border-border/30 opacity-0 animate-fade-up animation-delay-500">
            <p className="text-muted-foreground text-sm mb-8 font-body uppercase tracking-wider">
              Explore the Chambers
            </p>
            <div className="flex flex-wrap items-center justify-center gap-6">
              {[
                { name: "Treasury", icon: Shield, desc: "Vaults & Assets" },
                { name: "Agora", icon: BookOpen, desc: "Invoicing & Trade" },
                { name: "Archives", icon: Columns, desc: "Reports & Data" },
              ].map((sector, i) => (
                <div 
                  key={sector.name} 
                  className="group flex items-center gap-3 px-5 py-3 rounded-sm stone-border bg-card/30 hover:bg-card/60 cursor-pointer transition-all hover:shadow-gold animate-column-glow"
                  style={{ animationDelay: `${i * 200}ms` }}
                >
                  <sector.icon className="w-5 h-5 text-gold/70 group-hover:text-gold transition-colors" />
                  <div className="text-left">
                    <span className="block text-sm font-heading font-semibold text-foreground">{sector.name}</span>
                    <span className="block text-xs text-muted-foreground">{sector.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Scroll Indicator - Styled as a hanging seal */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 opacity-0 animate-fade-up animation-delay-600">
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-12 rounded-sm stone-border flex items-start justify-center pt-2">
            <div className="w-1.5 h-3 bg-gold rounded-full animate-bounce" />
          </div>
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Descend</span>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;