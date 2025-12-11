import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import FeaturesSection from "@/components/FeaturesSection";
import ChartForgeSection from "@/components/ChartForgeSection";
import CTASection from "@/components/CTASection";
import Footer from "@/components/Footer";

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-background font-body selection:bg-gold/30">
      <Navbar />
      <main>
        <HeroSection />
        <FeaturesSection />
        <ChartForgeSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
};

export default LandingPage;
