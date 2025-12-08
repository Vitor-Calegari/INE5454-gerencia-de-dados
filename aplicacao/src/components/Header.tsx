import { Film } from "lucide-react";

const Header = () => {
  return (
    <header className="sticky top-0 z-50 w-full bg-background/80 backdrop-blur-xl border-b border-border">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-center gap-3">
          <Film className="h-8 w-8 text-primary" />
          <h1 className="font-display text-3xl md:text-4xl tracking-wider text-gradient-gold">
            CINEBASE
          </h1>
        </div>
      </div>
    </header>
  );
};

export default Header;
