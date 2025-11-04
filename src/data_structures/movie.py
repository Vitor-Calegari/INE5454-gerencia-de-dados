from src.data_structures.review import Review
from src.data_structures.plataform import Plataform
from rapidfuzz import fuzz
import pandas as pd


class Movie:
    def __init__(self) -> None:
        self.url = []
        self.title = ""
        self.genres = []
        self.release_date_theater = ""
        self.release_date_streaming = ""
        self.synopsis = ""
        self.length = ""
        self.directors = []
        self.cast = []
        self.platforms = []
        self.content_rating = ""
        self.crit_avr_rating = 0
        self.crit_reviews = []
        self.crit_rev_count = 0
        self.usr_avr_rating = 0
        self.usr_reviews = []
        self.usr_rev_count = 0
    
    # Overloaded ==
    def __eq__(self, other) -> bool:
        if not isinstance(other, Movie):
            return NotImplemented
        similarity = fuzz.ratio(self.title.lower(), other.title.lower())
        limiar = 0.8
        return similarity >= limiar
    
    def __ne__(self, other):
        if not isinstance(other, Movie):
            return NotImplemented
        return not self.__eq__(other)
    
    def unite(self, other):
        if not isinstance(other, Movie):
            return NotImplemented
        
        movie = Movie()
        
        movie.set_title(self.title)
        
        movie.set_url([self.url])
        for url in other.get_url():
            movie.add_url(url)
        
        movie.set_genres(self.genres)
        for genre in other.get_genres():
            movie.add_genre(genre)

        format = "%Y-%m-%d"  # TODO definir formato correto
        release_date_s = pd.to_datetime([self.get_release_date_streaming(), other.get_release_date_streaming()], format=format, errors="coerce")
        movie.set_release_date_streaming(release_date_s.min())
        
        release_date_t = pd.to_datetime([self.get_release_date_theater(), other.get_release_date_theater()], format=format, errors="coerce")
        movie.set_release_date_theater(release_date_t.min())
        
        if len(self.get_synopsis()) >= len(other.get_synopsis()):
            movie.set_synopsis(self.get_synopsis())
        else:
            movie.set_synopsis(other.get_synopsis())
        
        movie.set_length(self.get_length())
        
        # TODO Devemos ver se existem diretores diferentes entre sites?
        movie.set_directors(self.get_directors())              
        
        movie.set_cast(self.get_cast())
        
        movie.set_platforms(self.get_platforms())
        for other_plat in other.get_platforms():
            for movie_plat in movie.get_platforms():
                if movie_plat != other:
                    movie.add_platform(other_plat)
        
        movie.set_content_rating(self.get_content_rating())

        usr_avr_rating = (self.get_usr_avr_rating() + other.get_usr_avr_rating()) / 2
        movie.set_usr_avr_rating(usr_avr_rating)
        
        movie.set_usr_reviews(self.get_usr_reviews())
        for review in other.get_usr_reviews():
            movie.add_user_review(review)
        movie.set_usr_rev_count(self.get_usr_reviews_count() + other.get_usr_reviews_count())
        
        crit_avr_rating = (self.get_crit_avr_rating() + other.get_crit_reviews()) / 2
        movie.set_crit_avr_rating(crit_avr_rating)
        
        movie.set_crit_reviews(self.get_crit_reviews())
        for review in other.get_crit_reviews():
            movie.add_critic_review(review)
        movie.set_crit_rev_count(self.get_crit_reviews_count() + other.get_crit_reviews_count())

        return movie
       
    # Getters -----------------------
    def get_title(self) -> str:
        return self.title

    def get_url(self) -> list[str]:
        return self.url
    
    def get_genres(self) -> list:
        return self.genres
    
    def get_release_date_theater(self) -> str:
        return self.release_date_theater
    
    def get_release_date_streaming(self) -> str:
        return self.release_date_streaming
    
    def get_synopsis(self) -> str:
        return self.synopsis
    
    def get_length(self) -> str:
        return self.length
    
    def get_directors(self) -> list:
        return self.directors
    
    def get_cast(self) -> list:
        return self.cast
    
    def get_platforms(self) -> list:
        return self.platforms
    
    def get_content_rating(self) -> str:
        return self.content_rating
    
    def get_crit_avr_rating(self) -> float:
        return self.crit_avr_rating
    
    def get_crit_reviews(self) -> list:
        return self.crit_reviews
    
    def get_crit_reviews_count(self) -> int:
        return self.crit_rev_count
    
    def get_usr_avr_rating(self) -> float:
        return self.usr_avr_rating
    
    def get_usr_reviews(self) -> list:
        return self.usr_reviews
    
    def get_usr_reviews_count(self) -> int:
        return self.usr_rev_count
    
    # Setters -----------------------
    def set_title(self, title: str) -> None:
        self.title = title

    def set_url(self, url: list[str]) -> None:
        self.url = url
    
    def set_genres(self, genres: list) -> None:
        self.genres = genres
    
    def set_release_date_theater(self, release_date_theater: str) -> None:
        self.release_date_theater = release_date_theater
    
    def set_release_date_streaming(self, release_date_streaming: str) -> None:
        self.release_date_streaming = release_date_streaming
    
    def set_synopsis(self, synopsis: str) -> None:
        self.synopsis = synopsis
    
    def set_length(self, length: str) -> None:
        self.length = length
    
    def set_directors(self, directors: list) -> None:
        self.directors = directors
    
    def set_cast(self, cast: list) -> None:
        self.cast = cast
    
    def set_platforms(self, platforms: list) -> None:
        self.platforms = platforms
    
    def set_content_rating(self, content_rating: str) -> None:
        self.content_rating = content_rating
    
    def set_crit_avr_rating(self, rating: float) -> None:
        self.crit_avr_rating = rating
    
    def set_crit_reviews(self, reviews: list) -> None:
        self.crit_reviews = reviews
    
    def set_crit_rev_count(self, reviews_count: int) -> None:
        self.crit_rev_count = reviews_count
    
    def set_usr_avr_rating(self, rating: float) -> None:
        self.usr_avr_rating = rating
    
    def set_usr_reviews(self, reviews: list) -> None:
        self.usr_reviews = reviews
    
    def set_usr_rev_count(self, reviews_count: int) -> None:
        self.usr_rev_count = reviews_count

    # List insertion methods
    def add_url(self, url: str) -> None:
        self.url.append(url)

    def add_genre(self, genre: str) -> None:
        self.genres.append(genre)

    def add_cast_member(self, cast_member: str) -> None:
        self.cast.append(cast_member)

    def add_platform(self, platform: Plataform) -> None:
        self.platforms.append(platform)

    def add_critic_review(self, review: Review) -> None:
        self.crit_reviews.append(review)

    def add_user_review(self, review: Review) -> None:
        self.usr_reviews.append(review)
    
    def add_director(self, director: str) -> None:
        self.directors.append(director)
    
    # String representation
    def __str__(self) -> str:
        return (f"{self.title}:\n"
                f"-URL: {self.url}\n"
                f"-Genres: {', '.join(self.genres)}\n"
                f"-Release Date (Theater): {self.release_date_theater}\n"
                f"-Release Date (Streaming): {self.release_date_streaming}\n"
                f"-Synopsis: {self.synopsis}\n"
                f"-Length: {self.length}\n"
                f"-Directors: {', '.join(self.directors)}\n"
                f"-Cast: {', '.join(self.cast)}\n"
                f"-Platforms: {', '.join(self.platforms)}\n"
                f"-Content Rating: {self.content_rating}\n"
                f"-Critics Average Rating: {self.crit_avr_rating}\n"
                f"-Critics Rating count: {self.crit_rev_count}\n"
                f"-User Average Rating: {self.usr_avr_rating}\n"
                f"-User Rating count: {self.usr_rev_count}")