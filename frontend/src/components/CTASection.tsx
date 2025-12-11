import { Button } from "@/components/ui/button";
import { ArrowRight, Columns } from "lucide-react";
import { Link } from "react-router-dom";

const CTASection = () => {
  return (
    <section className="py-24 relative overflow-hidden">
      {/* ... existing background code ... */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-secondary/30 to-background marble-texture" />

      {/* Column effects on sides */}
      <div className="absolute left-8 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-gold/20 to-transparent" />
      <div className="absolute right-8 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-gold/20 to-transparent" />

      {/* Ambient torchlight */}
      <div className="absolute top-1/3 left-20 w-48 h-48 bg-gold/10 rounded-full blur-[80px] animate-torch" />
      <div className="absolute bottom-1/3 right-20 w-48 h-48 bg-gold/10 rounded-full blur-[80px] animate-torch animation-delay-300" />

      <div className="container mx-auto px-6 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          {/* Decorative header */}
          <div className="flex items-center justify-center gap-4 mb-8">
            <div className="h-px w-20 bg-gradient-to-r from-transparent to-gold/50" />
            <Columns className="w-6 h-6 text-gold/60" />
            <div className="h-px w-20 bg-gradient-to-l from-transparent to-gold/50" />
          </div>

          <h2 className="text-3xl md:text-5xl font-heading font-bold mb-6 text-engraved">
            Ready to Enter the{" "}
            <span className="text-gradient-gold">Athenaeum</span>?
          </h2>
          <p className="text-muted-foreground text-lg font-body mb-12 max-w-2xl mx-auto leading-relaxed">
            Join the fellowship of enterprises that trust Aequitas to guard their treasuries.
            Your journey through the Digital Athenaeum begins with a single step.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Link to="/register">
              <Button variant="gold" size="xl" className="group">
                <span>Begin Your Journey</span>
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/contact">
              <Button variant="outline" size="xl" className="border-gold/30 hover:bg-gold/10 hover:border-gold/50">
                Request an Audience
              </Button>
            </Link>
          </div>

          {/* Stats styled as carved inscriptions */}
          <div className="grid grid-cols-3 gap-8 pt-10 border-t border-border/30">
            {[
              { value: "X·M", label: "Active Citizens", subtext: "10,000+" },
              { value: "XCIX.IX%", label: "Uptime Oath", subtext: "99.9%" },
              { value: "II·B", label: "Gold Processed", subtext: "$2B+" },
            ].map((stat) => (
              <div key={stat.label} className="text-center group">
                <div className="text-2xl md:text-3xl font-heading font-bold text-gradient-gold mb-1 glow-rune">
                  {stat.value}
                </div>
                <div className="text-xs text-muted-foreground/60 mb-1">{stat.subtext}</div>
                <div className="text-muted-foreground text-sm font-body">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTASection;