from src.data_structures.movie import Movie
from src.data_structures.url import URLType
from src.observers import Observed
from threading import Lock

class Storage(Observed):
    
    def __init__(self, threshold: int = 1000) -> None:
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
            total_movies = self.get_total_movies()
            
            if total_movies >= self.threshold:
                self.notify(total_movies)

    def enroll_new_scraper(self, type: URLType) -> None:
        with self._lock:
            if type not in self.scrapers:
                self.scrapers[type] = []
    
    def dump_to_json(self):
        with self._lock:
            print("Implementar Storage.dump_to_json.")
            pass