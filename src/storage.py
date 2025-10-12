from src.data_structures.movie import Movie
from src.data_structures.url import URLType
from src.observers import Observed
from threading import Lock
import json
from pathlib import Path

class Storage(Observed):
    
    def __init__(self, threshold: int = 1) -> None:
        super().__init__()
        self.scrapers = {}
        self.threshold = threshold
        self._lock = Lock()

    def get_total_movies(self) -> int:
        """Retorna o número total de filmes em todas as listas"""
        with self._lock:
            return sum(len(movies) for movies in self.scrapers.values())
    
    def store_movie(self, movie: Movie, type: URLType) -> None:
        with self._lock:
            self.scrapers[type].append(movie)
            total_movies = sum(len(movies) for movies in self.scrapers.values())
            
            if total_movies >= self.threshold:
                self.notify()

    def enroll_new_scraper(self, type: URLType) -> None:
        with self._lock:
            if type not in self.scrapers:
                self.scrapers[type] = []
    
    def dump_to_json(self):
        with self._lock:
            data = {"filmes": []}

            # Garante que há filmes armazenados
            if not self.scrapers:
                print("Nenhum filme armazenado.")
                return
            
            # Aqui você pode escolher o tipo (ex: URLType.ROTT)
            # ou percorrer todos os tipos
            for type_key, movies in self.scrapers.items():
                for movie in movies:
                    # Monta o dicionário do filme
                    movie_dict = {
                        "url": movie.get_url(),
                        "titulo": movie.get_title(),
                        "generos": movie.get_genres(),
                        "data": movie.get_release_date_theater() or movie.get_release_date_streaming(),
                        "sinopse": movie.get_synopsis(),
                        "duracao": movie.get_length(),
                        "diretor": ", ".join(movie.get_directors()),
                        "cast": movie.get_cast(),
                        "media_crit": movie.get_crit_avr_rating(),
                        "reviews_crit": [
                            {
                                "avaliacao": r.get_rating(),
                                "texto": r.get_text(),
                                "data": r.get_date()
                            } for r in movie.get_crit_reviews()
                        ],
                        "media_usr": movie.get_usr_avr_rating(),
                        "reviews_usr": [
                            {
                                "avaliacao": r.get_rating(),
                                "texto": r.get_text(),
                                "data": r.get_date()
                            } for r in movie.get_usr_reviews()
                        ]
                    }

                    data["filmes"].append(movie_dict)

            # Define o caminho do arquivo JSON
            output_path = Path("filmes.json")

            # Salva no arquivo com indentação para melhor leitura
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            print(f"✅ Arquivo salvo em: {output_path.resolve()}")