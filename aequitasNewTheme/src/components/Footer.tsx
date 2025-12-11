import Logo from "./Logo";
import { Columns } from "lucide-react";

const footerLinks = {
  Chambers: ["Treasury", "Agora", "Scribe's Chamber", "Archives", "Oracle's Pool"],
  Fellowship: ["About Us", "Careers", "Chronicles", "Partners"],
  Scrolls: ["Documentation", "API Codex", "Guides", "Support"],
  Decrees: ["Privacy Oath", "Terms of Service", "Compliance"],
};

const Footer = () => {
  return (
    <footer className="bg-secondary/40 border-t border-border/50 pt-16 pb-8 relative overflow-hidden marble-texture">
      {/* Decorative archway at top */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-1 bg-gradient-to-r from-transparent via-gold/30 to-transparent" />
      
      <div className="container mx-auto px-6 relative z-10">
        <div className="grid md:grid-cols-2 lg:grid-cols-6 gap-12 mb-12">
          {/* Brand Column - Styled as main pedestal */}
          <div className="lg:col-span-2">
            <Logo />
            <p className="text-muted-foreground font-body text-sm mt-6 max-w-xs leading-relaxed">
              The Digital Athenaeum of Finance. Where ancient wisdom meets modern 
              software—secure, precise, equitable.
            </p>
            {/* Decorative seal */}
            <div className="mt-6 inline-flex items-center gap-2 px-3 py-2 rounded-sm bg-gold/5 border border-gold/20">
              <Columns className="w-4 h-4 text-gold/60" />
              <span className="text-xs text-gold/80 font-body uppercase tracking-wider">Est. MMXXIV</span>
            </div>
          </div>

          {/* Links - Styled as inscription columns */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h4 className="font-heading font-semibold text-foreground mb-4 text-sm uppercase tracking-wider">
                {category}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link}>
                    <a
                      href="#"
                      className="text-muted-foreground hover:text-gold transition-colors font-body text-sm"
                    >
                      {link}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar - Ceremonial archway style */}
        <div className="pt-8 border-t border-border/50">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-muted-foreground text-sm font-body">
              © MMXXIV Aequitas. All rights reserved under the laws of commerce.
            </p>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald/50" />
              <span className="text-muted-foreground text-sm font-body italic">
                "Secure. Precise. Equitable."
              </span>
              <div className="w-2 h-2 rounded-full bg-emerald/50" />
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;