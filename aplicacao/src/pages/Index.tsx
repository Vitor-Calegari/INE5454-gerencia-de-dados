import { useState, useMemo } from "react";
import Header from "@/components/Header";
import SearchBar from "@/components/SearchBar";
import MovieCard from "@/components/MovieCard";
import MovieModal from "@/components/MovieModal";
import moviesData from "@/data/movies_united.json";
import { Movie, MoviesData } from "@/types/movie";
import { Film } from "lucide-react";

const Index = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);

  const movies = (moviesData as MoviesData).filmes;

  const filteredMovies = useMemo(() => {
    if (!searchQuery.trim()) return movies;
    
    const query = searchQuery.toLowerCase().trim();
    return movies.filter((movie) =>
      movie.titulo.toLowerCase().includes(query)
    );
  }, [movies, searchQuery]);

  return (
    <div className="min-h-screen bg-gradient-dark">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <section className="text-center mb-12 slide-up">
          <h2 className="font-display text-4xl md:text-6xl text-foreground mb-4">
            The complete view of each movie
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto mb-8">
            Quickly find ratings from top sites — IMDb, Rotten Tomatoes, and Letterboxd — all in one place
          </p>
          
          <SearchBar value={searchQuery} onChange={setSearchQuery} />
        </section>

        {/* Results Count */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Film className="h-5 w-5" />
            <span>
              {filteredMovies.length} {filteredMovies.length === 1 ? "filme encontrado" : "filmes encontrados"}
            </span>
          </div>
        </div>

        {/* Movie Grid */}
        {filteredMovies.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 md:gap-6">
            {filteredMovies.map((movie, index) => (
              <MovieCard
                key={`${movie.titulo}-${index}`}
                movie={movie}
                onClick={() => setSelectedMovie(movie)}
                index={index}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-20">
            <Film className="h-16 w-16 text-muted-foreground/50 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-foreground mb-2">Nenhum filme encontrado</h3>
            <p className="text-muted-foreground">
              Tente buscar por outro título
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 py-8 border-t border-border">
        <div className="container mx-auto px-4 text-center">
          <p className="text-muted-foreground text-sm">
            © 2024 Cinebase. Dados de filmes para fins demonstrativos.
          </p>
        </div>
      </footer>

      {/* Movie Modal */}
      <MovieModal
        movie={selectedMovie}
        isOpen={!!selectedMovie}
        onClose={() => setSelectedMovie(null)}
      />
    </div>
  );
};

export default Index;
