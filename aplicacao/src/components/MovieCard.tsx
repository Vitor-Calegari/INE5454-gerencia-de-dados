import { Star } from "lucide-react";
import { Movie } from "@/types/movie";

interface MovieCardProps {
  movie: Movie;
  onClick: () => void;
  index: number;
}

const MovieCard = ({ movie, onClick, index }: MovieCardProps) => {
  const rating = movie["nota média dos criticos"];
  const year = movie["data de lançamento"]?.split("-")[0];

  return (
    <div
      onClick={onClick}
      className="group cursor-pointer fade-in"
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      <div className="relative overflow-hidden rounded-xl poster-hover">
        <div className="aspect-[2/3] bg-muted">
          <img
            src={movie["link do poster"]}
            alt={movie.titulo}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={(e) => {
              e.currentTarget.src = "/placeholder.svg";
            }}
          />
        </div>
        
        {/* Overlay on hover */}
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
          <div className="absolute bottom-0 left-0 right-0 p-4">
            <div className="flex items-center gap-2 mb-2">
              <Star className="h-4 w-4 fill-primary text-primary" />
              <span className="text-primary font-semibold">{rating?.toFixed(1) || "N/A"}</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {movie.generos.slice(0, 2).map((genre) => (
                <span
                  key={genre}
                  className="text-xs px-2 py-0.5 bg-secondary/80 rounded-full text-secondary-foreground"
                >
                  {genre}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Rating badge */}
        {rating && (
          <div className="absolute top-3 right-3 flex items-center gap-1 px-2 py-1 bg-background/90 backdrop-blur-sm rounded-lg">
            <Star className="h-3.5 w-3.5 fill-primary text-primary" />
            <span className="text-sm font-semibold text-foreground">{rating.toFixed(1)}</span>
          </div>
        )}
      </div>

      <div className="mt-3 px-1">
        <h3 className="font-semibold text-foreground truncate group-hover:text-primary transition-colors">
          {movie.titulo}
        </h3>
        <p className="text-sm text-muted-foreground">{year}</p>
      </div>
    </div>
  );
};

export default MovieCard;
