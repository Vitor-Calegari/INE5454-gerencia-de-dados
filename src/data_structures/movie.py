from src.data_structures.review import Review
from src.data_structures.plataform import Plataform
from rapidfuzz import fuzz
import pandas as pd


class Movie:
    def __init__(self) -> None:
        self.url = []
        self.title = None
        self.genres = []
        self.release_date = None
        self.synopsis = None
        self.length = None
        self.directors = []
        self.cast = []
        self.platforms = []
        self.content_rating = None
        self.crit_avr_rating = None
        self.crit_avr_recommendation = None
        self.crit_reviews = []
        self.crit_rev_count = None
        self.usr_avr_rating = None
        self.usr_avr_recommendation = None
        self.usr_reviews = []
        self.usr_rev_count = None
        self.poster_link = None

        self.usr_avr_ratings = dict()
        self.usr_avr_recommendations = dict()
        self.usr_rev_counts = dict()
        self.crit_avr_ratings = dict()
        self.crit_avr_recommendations = dict()
        self.crit_rev_counts = dict()
    
    # Overloaded ==
    def __eq__(self, other) -> bool:
        if not isinstance(other, Movie):
            return NotImplemented
        similarity = fuzz.ratio(self.title.lower(), other.title.lower())
        limiar = 80
        return similarity >= limiar
    
    def __ne__(self, other):
        if not isinstance(other, Movie):
            return NotImplemented
        return not self.__eq__(other)
    
    def similar(self, a, b):
        similarity = fuzz.ratio(a.lower(), b.lower())
        limiar = 80
        return similarity >= limiar
    
    def unite(self, other):
        if not isinstance(other, Movie):
            return NotImplemented
        
        # urls
        if len(self.get_url()) == 1:
            if self.get_usr_avr_rating():
                self.usr_avr_ratings[self.get_url()[0]] = self.get_usr_avr_rating()
            if self.get_usr_avr_recommendation():
                self.usr_avr_recommendations[self.get_url()[0]] = self.get_usr_avr_recommendation()
            if self.get_usr_reviews_count():
                self.usr_rev_counts[self.get_url()[0]] = self.get_usr_reviews_count()
            if self.get_crit_avr_rating():
                self.crit_avr_ratings[self.get_url()[0]] = self.get_crit_avr_rating()
            if self.get_crit_avr_recommendation():
                self.crit_avr_recommendations[self.get_url()[0]] = self.get_crit_avr_recommendation()
            if self.get_crit_reviews_count():
                self.crit_rev_counts[self.get_url()[0]] = self.get_crit_reviews_count()
            for rev in self.usr_reviews:
                rev.link = self.get_url()[0]
            for rev in self.crit_reviews:
                rev.link = self.get_url()[0]
        self.add_url(other.get_url()[0])
        
        # genres
        for genre_other in other.get_genres():
            exists = False
            for genre_self in self.get_genres():
                if self.similar(genre_self, genre_other):
                    exists = True
                    break
            if not exists:
                self.add_genre(genre_other)

        # realease dates
        format = "%Y-%m-%d"
        release_date_t = pd.to_datetime([self.get_release_date(), other.get_release_date()], format=format, errors="coerce")
        min_date = release_date_t.min()
        if pd.isna(min_date):
            self.set_release_date(None)   # ou "", ou não setar
        else:
            self.set_release_date(min_date.strftime("%Y-%m-%d"))
        
        # synopsis
        if self.get_synopsis() and other.get_synopsis():
            if len(self.get_synopsis()) < len(other.get_synopsis()):
                self.set_synopsis(other.get_synopsis())
        elif not self.get_synopsis():
            self.set_synopsis(other.get_synopsis())
        else: 
            self.set_synopsis(self.get_synopsis())
        
        # length
        if self.get_length() and other.get_length():
            if self.get_length() < other.get_length():
                self.set_length(other.get_length())
        elif not self.get_length():
            self.set_length(other.get_length())
        else:
            self.set_length(self.get_length())
        
        # directors
        for director_other in other.get_directors():
            exists = False
            for director_self in self.get_directors():
                if self.similar(director_self, director_other):
                    exists = True
                    break
            if not exists:
                self.add_director(director_other)           
        
        # cast
        for cast_other in other.get_cast():
            exists = False
            for cast_self in self.get_cast():
                if self.similar(cast_self, cast_other):
                    exists = True
                    break
            if not exists:
                self.add_cast_member(cast_other) 
        
        # platforms
        for other_plat in other.get_platforms():
            exists = False
            for movie_plat in self.get_platforms():
                if movie_plat == other_plat:
                    exists = True
                    break
            if not exists:
                self.add_platform(other_plat)
        
        # content rating
        if not self.get_content_rating():
            self.set_content_rating(other.get_content_rating())

        # user avr rating
        if other.get_usr_avr_rating():
            self.usr_avr_ratings[other.get_url()[0]] = other.get_usr_avr_rating()
        if self.usr_avr_ratings:
            avg_usr_rating = sum(self.usr_avr_ratings.values()) / len(self.usr_avr_ratings)
            self.usr_avr_rating = avg_usr_rating
        
        # user avr recommendation
        if other.get_usr_avr_recommendation():
            self.usr_avr_recommendations[other.get_url()[0]] = other.get_usr_avr_recommendation()
        if self.usr_avr_recommendations:
            avg_usr_rec = sum(self.usr_avr_recommendations.values()) / len(self.usr_avr_recommendations)
            self.usr_avr_recommendation = avg_usr_rec
        
        # user reviews
        for review in other.get_usr_reviews():
            review.link = other.get_url()[0]
            self.add_user_review(review)

        # user reviews count
        if other.get_usr_reviews_count():
            self.usr_rev_counts[other.get_url()[0]] = other.get_usr_reviews_count()
        if self.usr_rev_counts:
            total_usr_rev_count = sum(self.usr_rev_counts.values())
            self.usr_rev_count = total_usr_rev_count
        
        # crit avr rating
        if other.get_crit_avr_rating():
            self.crit_avr_ratings[other.get_url()[0]] = other.get_crit_avr_rating()
        if self.crit_avr_ratings:
            avg_crit_rating = sum(self.crit_avr_ratings.values()) / len(self.crit_avr_ratings)
            self.crit_avr_rating = avg_crit_rating
        
        # crit avr recommendation
        if other.get_crit_avr_recommendation():
            self.crit_avr_recommendations[other.get_url()[0]] = other.get_crit_avr_recommendation()
        if self.crit_avr_recommendations:
            avg_crit_rec = sum(self.crit_avr_recommendations.values()) / len(self.crit_avr_recommendations)
            self.crit_avr_recommendation = avg_crit_rec
        
        # crit reviews
        for review in other.get_crit_reviews():
            review.link = other.get_url()[0]
            self.add_critic_review(review)

        # crit reviews count
        if other.get_crit_reviews_count():
            self.crit_rev_counts[other.get_url()[0]] = other.get_crit_reviews_count()
        if self.crit_rev_counts:
            total_crit_rev_count = sum(self.crit_rev_counts.values())
            self.crit_rev_count = total_crit_rev_count
        
        # poster link
        if not self.get_poster_link():
            self.set_poster_link(other.get_poster_link())
       
    # Getters -----------------------
    def get_title(self) -> str | None:
        return self.title

    def get_url(self) -> list[str]:
        return self.url
    
    def get_genres(self) -> list:
        return self.genres
    
    def get_release_date(self) -> str | None:
        return self.release_date
    

    def get_synopsis(self) -> str | None:
        return self.synopsis
    
    def get_length(self) -> str | None:
        return self.length
    
    def get_directors(self) -> list:
        return self.directors
    
    def get_cast(self) -> list:
        return self.cast
    
    def get_platforms(self) -> list:
        return self.platforms
    
    def get_content_rating(self) -> str | None:
        return self.content_rating
    
    def get_crit_avr_rating(self) -> float | None:
        return self.crit_avr_rating
    
    def get_crit_avr_recommendation(self) -> int | None:
        return self.crit_avr_recommendation

    def get_crit_reviews(self) -> list:
        return self.crit_reviews
    
    def get_crit_reviews_count(self) -> int | None:
        return self.crit_rev_count
    
    def get_usr_avr_rating(self) -> float | None:
        return self.usr_avr_rating
    
    def get_usr_avr_recommendation(self) -> int | None:
        return self.usr_avr_recommendation
    
    def get_usr_reviews(self) -> list:
        return self.usr_reviews
    
    def get_usr_reviews_count(self) -> int | None:
        return self.usr_rev_count
    
    def get_poster_link(self) -> str | None:
        return self.poster_link
    
    # Setters -----------------------
    def set_title(self, title: str | None) -> None:
        self.title = title

    def set_url(self, url: list[str]) -> None:
        if type(url) != list:
            self.url = [url]
        else:
            self.url = url
    
    def set_genres(self, genres: list) -> None:
        self.genres = genres
    
    def set_release_date(self, release_date: str) -> None:
        self.release_date = release_date
    
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
    
    def set_crit_avr_recommendation(self, recommendation) -> None:
        self.crit_avr_recommendation = recommendation
    
    def set_usr_avr_rating(self, rating: float) -> None:
        self.usr_avr_rating = rating
    
    def set_usr_reviews(self, reviews: list) -> None:
        self.usr_reviews = reviews
    
    def set_usr_rev_count(self, reviews_count: int) -> None:
        self.usr_rev_count = reviews_count
    
    def set_usr_avr_recommendation(self, recommendation) -> None:
        self.usr_avr_recommendation = recommendation
    
    def set_poster_link(self, poster) -> None:
        self.poster_link = poster

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
                f"-Release Date (Theater): {self.release_date}\n"
                f"-Synopsis: {self.synopsis}\n"
                f"-Length: {self.length}\n"
                f"-Directors: {', '.join(self.directors)}\n"
                f"-Cast: {', '.join(self.cast)}\n"
                f"-Platforms: {', '.join(self.platforms)}\n"
                f"-Content Rating: {self.content_rating}\n"
                f"-Critics Average Rating: {self.crit_avr_rating}\n"
                f"-Critics Rating count: {self.crit_rev_count}\n"
                f"-Critics Average Recommendation Percentage: {self.crit_avr_recommendation}\n"
                f"-User Average Rating: {self.usr_avr_rating}\n"
                f"-User Rating count: {self.usr_rev_count}\n"
                f"-User Average Recommendation Percentage: {self.usr_avr_recommendation}")