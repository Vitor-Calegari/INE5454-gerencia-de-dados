from src.data_structures.movie import Movie
from src.data_structures.url import URLType
from src.observers import Observed
from threading import Lock
import json
from pathlib import Path

class Storage(Observed):
    
    def __init__(self, threshold: int = 30) -> None:
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
            

            for type_key, movies in self.scrapers.items():
                for movie in movies:
                    # Monta o dicionário do filme
                    movie_dict = {
                        "url": movie.get_url(),
                        "titulo": movie.get_title(),
                        "generos": movie.get_genres(),
                        "data de lançamento": movie.get_release_date(),
                        "classificacao indicativa": movie.get_content_rating(),
                        "sinopse": movie.get_synopsis(),
                        "duracao": movie.get_length(),
                        "diretor": movie.get_directors(),
                        "elenco": movie.get_cast(),
                        "onde assistir": [
                            {
                                "plataforma": p.get_plataform(),
                                "link": p.get_link()
                            } for p in movie.get_platforms()
                        ],
                        "link do poster": movie.get_poster_link(),
                        "nota média dos criticos": movie.get_crit_avr_rating(),
                        "taxa de recomendação dos críticos": movie.get_crit_avr_recommendation(),
                        "quantidade de reviews de críticos": movie.get_crit_reviews_count(),
                        "reviews de críticos": [
                            {
                                "avaliação (nota até 10)": r.get_rating(),
                                "texto": r.get_text(),
                                "data": r.get_date()
                            } for r in movie.get_crit_reviews()
                        ],
                        "nota média dos usuários": movie.get_usr_avr_rating(),
                        "taxa de recomendação dos usuários": movie.get_usr_avr_recommendation(),
                        "quantidade de reviews de usuários": movie.get_usr_reviews_count(),
                        "reviews de usuários": [
                            {
                                "avaliação (nota até 10)": r.get_rating(),
                                "texto": r.get_text(),
                                "data": r.get_date()
                            } for r in movie.get_usr_reviews()
                        ]
                    }
                    data["filmes"].append(movie_dict)
                    
            output_path = Path("movies.json")

            # Salva no arquivo com indentação para melhor leitura
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)


            print(f"Arquivo salvo em: {output_path.resolve()}")
            
            first = True
            processed_movies: list[Movie] = []
            
            for outer_type_key, unprocessed_movies in self.scrapers.items():
                if first:
                    for unprocessed_movie in unprocessed_movies:
                        rev = unprocessed_movie.get_crit_reviews()
                        url_rev = unprocessed_movie.get_url()[0]
                        new_rev = []
                        for r in rev:
                            r.set_link(url_rev)
                            new_rev.append(r)
                        unprocessed_movie.set_crit_reviews(new_rev)
                        rev = unprocessed_movie.get_usr_reviews()
                        url_rev = unprocessed_movie.get_url()[0]
                        new_rev = []
                        for r in rev:
                            r.set_link(url_rev)
                            new_rev.append(r)
                        unprocessed_movie.set_usr_reviews(new_rev)
                        
                        processed_movies.append(unprocessed_movie)
                    first = False
                else:
                    new_movies = []
                    for unprocessed_movie in unprocessed_movies:
                        equal = False
                        for processed_movie in processed_movies:
                            if processed_movie == unprocessed_movie:  # Overloaded operator for similarity comparation
                                movie = processed_movie.unite(unprocessed_movie)
                                equal = True
                                break
                        if not equal:
                            rev = unprocessed_movie.get_crit_reviews()
                            url_rev = unprocessed_movie.get_url()[0]
                            new_rev = []
                            for r in rev:
                                r.set_link(url_rev)
                                new_rev.append(r)
                            unprocessed_movie.set_crit_reviews(new_rev)
                            rev = unprocessed_movie.get_usr_reviews()
                            url_rev = unprocessed_movie.get_url()[0]
                            new_rev = []
                            for r in rev:
                                r.set_link(url_rev)
                                new_rev.append(r)
                            unprocessed_movie.set_usr_reviews(new_rev)
                            new_movies.append(unprocessed_movie)
                    processed_movies.extend(new_movies)

            data_united = {"filmes": []}        

            for movie in processed_movies:
                # Monta o dicionário do filme
                movie_dict = {
                    "url": movie.get_url(),
                    "titulo": movie.get_title(),
                    "generos": movie.get_genres(),
                    "data de lançamento": movie.get_release_date(),
                    "classificacao indicativa": movie.get_content_rating(),
                    "sinopse": movie.get_synopsis(),
                    "duracao": movie.get_length(),
                    "diretor": movie.get_directors(),
                    "elenco": movie.get_cast(),
                    "onde assistir": [
                        {
                            "plataforma": p.get_plataform(),
                            "link": p.get_link()
                        } for p in movie.get_platforms()
                    ],
                    "link do poster": movie.get_poster_link(),
                    "nota média dos criticos": movie.get_crit_avr_rating(),
                    "notas dos criticos": [
                        {"link": link, "nota": nota}
                        for link, nota in movie.crit_avr_ratings.items()
                    ],
                    "taxa de recomendação dos críticos": movie.get_crit_avr_recommendation(),
                    "taxas de recomendação dos críticos": [
                        {"link": link, "taxa": taxa}
                        for link, taxa in movie.crit_avr_recommendations.items()
                    ],
                    "quantidade de reviews de críticos": movie.get_crit_reviews_count(),
                    "quantidades de reviews dos críticos": [
                        {"link": link, "quantidade": quant}
                        for link, quant in movie.crit_rev_counts.items()
                    ],
                    "reviews de críticos": [
                        {
                            "avaliação (nota até 10)": r.get_rating(),
                            "texto": r.get_text(),
                            "data": r.get_date(),
                            "link": r.get_link()
                        } for r in movie.get_crit_reviews()
                    ],
                    "nota média dos usuários": movie.get_usr_avr_rating(),
                    "notas dos usuários": [
                        {"link": link, "nota": nota}
                        for link, nota in movie.usr_avr_ratings.items()
                    ],
                    "taxa de recomendação dos usuários": movie.get_usr_avr_recommendation(),
                    "taxas de recomendação dos usuários": [
                        {"link": link, "taxa": taxa}
                        for link, taxa in movie.usr_avr_recommendations.items()
                    ],
                    "quantidade de reviews de usuários": movie.get_usr_reviews_count(),
                    "quantidades de reviews dos usuários": [
                        {"link": link, "quantidade": quant}
                        for link, quant in movie.usr_rev_counts.items()
                    ],
                    "reviews de usuários": [
                        {
                            "avaliação (nota até 10)": r.get_rating(),
                            "texto": r.get_text(),
                            "data": r.get_date(),
                            "link": r.get_link()
                        } for r in movie.get_usr_reviews()
                    ]
                }
                data_united["filmes"].append(movie_dict)

            output_path = Path("movies_united.json")

            # Salva no arquivo com indentação para melhor leitura
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data_united, f, ensure_ascii=False, indent=4)

            print(f"Arquivo salvo em: {output_path.resolve()}")