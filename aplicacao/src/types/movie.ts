export interface Review {
  "avaliação (nota até 10)": number | null;
  texto: string | null;
  data: string | null;
  link: string;
}

export interface WatchProvider {
  plataforma: string;
  link: string;
}

export interface SiteNote {
  link: string;
  nota: number;
}

export interface SiteTaxa {
  link: string;
  taxa: number;
}

export interface SiteQuantidade {
  link: string;
  quantidade: number;
}

export interface Movie {
  url: string[];
  titulo: string;
  generos: string[];
  "data de lançamento": string;
  "classificacao indicativa": string;
  sinopse: string;
  duracao: string;
  diretor: string[];
  elenco: string[];
  "onde assistir": WatchProvider[];
  "link do poster": string;
  // Críticos
  "nota média dos criticos": number;
  "notas dos criticos": SiteNote[];
  "taxa de recomendação dos críticos": number;
  "taxas de recomendação dos críticos": SiteTaxa[];
  "quantidade de reviews de críticos": number;
  "quantidades de reviews dos críticos": SiteQuantidade[];
  "reviews de críticos": Review[];
  // Usuários
  "nota média dos usuários": number;
  "notas dos usuários": SiteNote[];
  "taxa de recomendação dos usuários": number;
  "taxas de recomendação dos usuários": SiteTaxa[];
  "quantidade de reviews de usuários": number;
  "quantidades de reviews dos usuários": SiteQuantidade[];
  "reviews de usuários": Review[];
}

export interface MoviesData {
  filmes: Movie[];
}
