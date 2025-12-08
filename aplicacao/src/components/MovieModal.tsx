import { X, Star, Clock, Calendar, Film, Users, Play, ExternalLink, MessageSquare } from "lucide-react";
import { Movie, Review, SiteNote, SiteTaxa, SiteQuantidade } from "@/types/movie";
import { Dialog, DialogContent, DialogTitle, DialogClose } from "./ui/dialog";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";

interface MovieModalProps {
  movie: Movie | null;
  isOpen: boolean;
  onClose: () => void;
}

const getSiteName = (link: string): string => {
  if (link.includes("imdb")) return "IMDb";
  if (link.includes("rottentomatoes")) return "Rotten Tomatoes";
  if (link.includes("letterboxd")) return "Letterboxd";
  return "Outro";
};

const getSiteColor = (link: string): string => {
  if (link.includes("imdb")) return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
  if (link.includes("rottentomatoes")) return "bg-red-500/20 text-red-400 border-red-500/30";
  if (link.includes("letterboxd")) return "bg-orange-500/20 text-orange-400 border-orange-500/30";
  return "bg-muted text-muted-foreground";
};

interface RatingsBreakdownProps {
  title: string;
  average: number;
  notes: SiteNote[];
  taxas: SiteTaxa[];
  quantidades: SiteQuantidade[];
}

const RatingsBreakdown = ({ title, average, notes, taxas, quantidades }: RatingsBreakdownProps) => {
  const hasSingleSource = notes.length === 1;
  
  return (
    <div className="p-4 rounded-xl bg-secondary/50 border border-border">
      <h4 className="font-display text-lg text-foreground mb-3">{title}</h4>
      
      {/* Média geral */}
      <div className="flex items-center gap-2 mb-4">
        <Star className="h-6 w-6 fill-primary text-primary" />
        <span className="text-2xl font-bold text-foreground">{average.toFixed(1)}</span>
        <span className="text-muted-foreground">/10</span>
        {hasSingleSource && (
          <span className="text-sm text-muted-foreground ml-2">
            (via {getSiteName(notes[0].link)})
          </span>
        )}
      </div>

      {/* Notas por site */}
      {!hasSingleSource && notes.length > 0 && (
        <div className="mb-4">
          <p className="text-sm text-muted-foreground mb-2">Ratings by site:</p>
          <div className="flex flex-wrap gap-2">
            {notes.map((note) => (
              <div
                key={note.link}
                className={`px-3 py-1.5 rounded-lg border ${getSiteColor(note.link)}`}
              >
                <span className="font-semibold">{note.nota.toFixed(1)}</span>
                <span className="text-xs ml-1.5 opacity-80">{getSiteName(note.link)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Taxa de recomendação */}
      {taxas.length > 0 && (
        <div className="mb-4">
          <p className="text-sm text-muted-foreground mb-2">Recommendation rate:</p>
          <div className="flex flex-wrap gap-2">
            {taxas.map((taxa) => (
              <div
                key={taxa.link}
                className={`px-3 py-1.5 rounded-lg border ${getSiteColor(taxa.link)}`}
              >
                <span className="font-semibold">{taxa.taxa}%</span>
                <span className="text-xs ml-1.5 opacity-80">{getSiteName(taxa.link)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quantidade de reviews */}
      {quantidades.length > 0 && (
        <div>
          <p className="text-sm text-muted-foreground mb-2">Number of reviews:</p>
          <div className="flex flex-wrap gap-2">
            {quantidades.map((qtd) => (
              <div
                key={qtd.link}
                className={`px-3 py-1.5 rounded-lg border ${getSiteColor(qtd.link)}`}
              >
                <span className="font-semibold">{qtd.quantidade.toLocaleString("pt-BR")}</span>
                <span className="text-xs ml-1.5 opacity-80">{getSiteName(qtd.link)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

interface ReviewsListProps {
  reviews: Review[];
  maxReviews?: number;
}

const ReviewsList = ({ reviews, maxReviews = reviews.length }: ReviewsListProps) => {
  const validReviews = reviews.filter((r) => r.texto);
  
  if (validReviews.length === 0) {
    return <p className="text-muted-foreground text-sm">No reviews available.</p>;
  }

  return (
    <div className="space-y-4">
      {validReviews.slice(0, maxReviews).map((review, index) => (
        <div
          key={index}
          className="p-4 rounded-xl bg-secondary/50 border border-border"
        >
          <div className="flex items-center justify-between gap-3 mb-2">
            <div className="flex items-center gap-2">
              {review["avaliação (nota até 10)"] && (
                <div className="flex items-center gap-1 px-2 py-1 bg-primary/20 rounded-lg">
                  <Star className="h-3.5 w-3.5 fill-primary text-primary" />
                  <span className="text-sm font-semibold text-primary">
                    {review["avaliação (nota até 10)"].toFixed(1)}
                  </span>
                </div>
              )}
              {review.data && (
                <span className="text-xs text-muted-foreground">{review.data}</span>
              )}
            </div>
            <Badge variant="outline" className={`text-xs ${getSiteColor(review.link)}`}>
              {getSiteName(review.link)}
            </Badge>
          </div>
          <p className="text-sm text-foreground/90 leading-relaxed italic">
            "{review.texto}"
          </p>
        </div>
      ))}
    </div>
  );
};

const MovieModal = ({ movie, isOpen, onClose }: MovieModalProps) => {
  if (!movie) return null;
  console.log("isOpen:", isOpen); 
  const rating = movie["nota média dos criticos"];
  const userRating = movie["nota média dos usuários"];
  const year = movie["data de lançamento"]?.split("-")[0];
  const criticReviews = movie["reviews de críticos"] || [];
  const userReviews = movie["reviews de usuários"] || [];

  const formatDuration = (duration: string) => {
    const match = duration.match(/(\d+):(\d+)/);
    if (match) {
      const hours = parseInt(match[1]);
      const minutes = parseInt(match[2]);
      return `${hours}h ${minutes}min`;
    }
    return duration;
  };

  return (
    <Dialog
            open={isOpen}
            onOpenChange={(open: boolean) => {
                if (!open) onClose();
            }}
            >

      <DialogContent className="max-w-4xl max-h-[90vh] p-0 bg-card border-border overflow-hidden">
        <VisuallyHidden>
          <DialogTitle>{movie.titulo}</DialogTitle>
        </VisuallyHidden>
        
        <ScrollArea className="max-h-[90vh]">
          {/* Hero Section */}
          <div className="relative">
            {/* HERO: imagem de fundo via CSS (background-image) para evitar layering issues com filter/blur */}
            <div className="h-64 md:h-80 bg-muted overflow-hidden relative z-0">
              <div
                className="w-full h-full bg-center bg-cover opacity-40 scale-110"
                style={{
                  backgroundImage: `url(${movie["link do poster"]})`,
                  filter: "blur(6px)",
                  transform: "scale(1.1)",
                }}
                aria-hidden="true"
              />
            </div>

            {/* gradiente acima da imagem (decorativo) */}
            <div
              className="absolute inset-0 z-20 bg-gradient-to-b from-transparent via-card/80 to-card pointer-events-none"
              aria-hidden="true"
            />

            {/* botão X — claramente acima de tudo */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 z-50 p-2 bg-background/80 backdrop-blur-sm rounded-full hover:bg-background transition-colors"
              aria-label="Fechar"
            >
              <X className="h-5 w-5" />
            </button>

            {/* Movie Info Overlay */}
            <div className="absolute bottom-0 left-0 right-0 z-20 p-6 md:p-8">
              <div className="flex gap-6">
                {/* Poster */}
                <div className="hidden md:block w-40 flex-shrink-0">
                  <img
                    src={movie["link do poster"]}
                    alt={movie.titulo}
                    className="w-full rounded-xl shadow-poster"
                    onError={(e) => {
                      e.currentTarget.src = "/placeholder.svg";
                    }}
                  />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <h2 className="font-display text-3xl md:text-4xl text-foreground mb-3">
                    {movie.titulo}
                  </h2>
                  
                  <div className="flex flex-wrap items-center gap-3 mb-4 text-sm text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" />
                      {year}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {formatDuration(movie.duracao)}
                    </span>
                    <Badge variant="outline" className="border-primary/50 text-primary">
                      {movie["classificacao indicativa"]}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {movie.generos.map((genre) => (
                      <Badge key={genre} variant="secondary" className="bg-secondary text-secondary-foreground">
                        {genre}
                      </Badge>
                    ))}
                  </div>

                  {/* Quick Ratings */}
                  <div className="flex flex-wrap gap-6">
                    {rating && (
                      <div className="flex items-center gap-2">
                        <Star className="h-6 w-6 fill-primary text-primary" />
                        <div>
                          <span className="text-2xl font-bold text-foreground">{rating.toFixed(1)}</span>
                          <span className="text-muted-foreground text-sm ml-1">critics</span>
                        </div>
                      </div>
                    )}
                    {userRating && (
                      <div className="flex items-center gap-2">
                        <Star className="h-6 w-6 fill-accent text-accent" />
                        <div>
                          <span className="text-2xl font-bold text-foreground">{userRating.toFixed(1)}</span>
                          <span className="text-muted-foreground text-sm ml-1">users</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 md:p-8 space-y-8">
            {/* Synopsis */}
            <section>
              <h3 className="font-display text-xl text-foreground mb-3">Synopsis</h3>
              <p className="text-muted-foreground leading-relaxed">{movie.sinopse}</p>
            </section>

            {/* Director & Cast */}
            <section className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-display text-xl text-foreground mb-3 flex items-center gap-2">
                  <Film className="h-5 w-5 text-primary" />
                  Directors
                </h3>
                <p className="text-muted-foreground">{movie.diretor.join(", ")}</p>
              </div>
              <div>
                <h3 className="font-display text-xl text-foreground mb-3 flex items-center gap-2">
                  <Users className="h-5 w-5 text-primary" />
                  Cast
                </h3>
                <p className="text-muted-foreground">{movie.elenco.join(", ")}</p>
              </div>
            </section>

            {/* Ratings Breakdown */}
            <section>
              <h3 className="font-display text-xl text-foreground mb-4">Detailed Review Info</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <RatingsBreakdown
                  title="Critics"
                  average={movie["nota média dos criticos"]}
                  notes={movie["notas dos criticos"] || []}
                  taxas={movie["taxas de recomendação dos críticos"] || []}
                  quantidades={movie["quantidades de reviews dos críticos"] || []}
                />
                <RatingsBreakdown
                  title="Users"
                  average={movie["nota média dos usuários"]}
                  notes={movie["notas dos usuários"] || []}
                  taxas={movie["taxas de recomendação dos usuários"] || []}
                  quantidades={movie["quantidades de reviews dos usuários"] || []}
                />
              </div>
            </section>

            {/* Where to Watch */}
            {movie["onde assistir"]?.length > 0 && (
              <section>
                <h3 className="font-display text-xl text-foreground mb-3 flex items-center gap-2">
                  <Play className="h-5 w-5 text-primary" />
                  Where To Watch
                </h3>
                <div className="flex flex-wrap gap-3">
                  {movie["onde assistir"].map((provider) => (
                    <a
                      key={provider.plataforma}
                      href={provider.link}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Button variant="secondary" className="gap-2">
                        {provider.plataforma}
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </a>
                  ))}
                </div>
              </section>
            )}

            {/* Reviews with Tabs */}
            <section>
              <h3 className="font-display text-xl text-foreground mb-4 flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-primary" />
                Reviews
              </h3>
              <Tabs defaultValue="critics" className="w-full">
                <TabsList className="mb-4">
                  <TabsTrigger value="critics">
                    Critics ({criticReviews.filter(r => r.texto).length})
                  </TabsTrigger>
                  <TabsTrigger value="users">
                    Users ({userReviews.filter(r => r.texto).length})
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="critics">
                  <ReviewsList reviews={criticReviews} />
                </TabsContent>
                <TabsContent value="users">
                  <ReviewsList reviews={userReviews} />
                </TabsContent>
              </Tabs>
            </section>

            {/* External Links */}
            {movie.url?.length > 0 && (
              <section>
                <h3 className="font-display text-xl text-foreground mb-3">External Links</h3>
                <div className="flex flex-wrap gap-2">
                  {movie.url.map((url) => (
                    <a key={url} href={url} target="_blank" rel="noopener noreferrer">
                      <Button variant="outline" size="sm" className="gap-2">
                        {getSiteName(url)}
                        <ExternalLink className="h-3.5 w-3.5" />
                      </Button>
                    </a>
                  ))}
                </div>
              </section>
            )}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};

export default MovieModal;
