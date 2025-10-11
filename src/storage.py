from src.data_structures.movie import Movie
from src.data_structures.url import URLType
from src.observers import Observed

class Storage(Observed):
    
    def __init__(self, threshold: int = 1000) -> None:
        self.scrapers = {}
        self.threshold = threshold

    def get_total_movies(self) -> int:
        """Retorna o número total de filmes em todas as listas"""
        return sum(len(movies) for movies in self.scrapers.values())
    
    def store_movie(self, movie: Movie, type: URLType) -> None:
        self.scrapers[type].append(movie)
        total_movies = self.get_total_movies()
        
        if total_movies >= self.threshold:
            self.notify(total_movies)

    def enroll_new_scraper(self, type: URLType) -> None:
        if type not in self.scrapers:
            self.scrapers[type] = []
    
    def dump_to_json(self):
        print("Implementar Storage.dump_to_json.")
        pass