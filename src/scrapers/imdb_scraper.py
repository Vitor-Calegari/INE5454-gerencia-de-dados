import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, urlunparse

from src.scrapers.scraper import Scraper
from src.data_structures.periodic_queue import PeriodicQueue
from typing import override
from src.data_structures.url import URL, URLType
from src.data_structures.movie import Movie
from src.storage import Storage
from src.data_structures.review import Review


class IMDBScraper(Scraper):
    
    def __init__(self, periodic_queue: PeriodicQueue, storage: Storage) -> None:
        super().__init__(periodic_queue, storage)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        }
    
    @override
    def scrap(self):
        url = self.periodic_queue.get()
        
        if (url.get_type() == URLType.END):
            return
        
        response = requests.get(url.get_url(), headers=self.headers)
        
        if (not response.ok):
            print(f"Nao foi possivel obter o html de {url}")
            print(f"Conteudo retornado:")
            print(response.content)
    
        site = BeautifulSoup(response.content, "html.parser")
        script_tag = site.find("script", type="application/ld+json")

        if script_tag:
            
            movie = Movie()
            movie.set_url(url=url.get_url())
            data = json.loads(script_tag.string)
            
            # Extracting details from JSON-LD
            movie.set_title(data.get("name"))
            movie.set_genres(data.get("genre", []))
            movie.set_release_date_theater(data.get("datePublished"))
            movie.set_synopsis(data.get("description"))
            
            duration = data.get("duration")
            if duration:
                movie.set_length(duration)
            
            # Extracting content rating
            movie.set_content_rating(data.get("contentRating"))

            # Extracting user ratings
            aggregate_rating = data.get("aggregateRating", {})
            movie.set_usr_avr_rating(aggregate_rating.get("ratingValue"))
            movie.set_usr_rev_count(aggregate_rating.get("ratingCount"))

        # Encontra o bloco onde o rótulo é "Directors"
        directors_section = site.find("span", string="Directors")

        if directors_section:
            # Pega o container logo após o span
            container = directors_section.find_next("div", class_="ipc-metadata-list-item__content-container")
            if container:
                # Pega todos os nomes (links)
                for director in container.find_all("a"):
                    movie.add_director(director.text.strip())

        # Extrai membros do cast
        cast_tags = site.find_all("a", {"data-testid": "title-cast-item__actor"})
        cast = [a.get_text(strip=True) for a in cast_tags]
        movie.set_cast(cast)

        # Usr reviews
        usr_review_url = url.get_url() + "reviews"
        resp = requests.get(usr_review_url, headers=self.headers)
        reviews_site = BeautifulSoup(resp.text, "html.parser")

        # encontra todos os containers de reviews
        review_divs = reviews_site.find_all("article")
        if not review_divs:
            # talvez a nova classe
            review_divs = reviews_site.find_all("div", class_="lister-item mode-detail imdb-user-review")

        for div in review_divs:
            # extrai a nota
            rating_span = div.find("span", class_="ipc-rating-star--rating")
            rating = None
            if rating_span:
                rating = rating_span.get_text(strip=True)

            # extrai o texto do review
            text_div = div.find("div", class_="ipc-html-content-inner-div")
            comment = text_div.get_text(strip=True) if text_div else None

            # data da review
            date_span = div.find("li", class_="ipc-inline-list__item review-date")
            date = date_span.get_text(strip=True) if date_span else None

            usr_review = Review()
            usr_review.set_date(date)
            usr_review.set_rating(rating)
            usr_review.set_text(comment)
            movie.add_user_review(usr_review)

        section = site.find("section", {"data-testid": "MoreLikeThis"})
        movies = section.find_all("div", class_="ipc-poster-card ipc-poster-card--base ipc-poster-card--media-radius ipc-poster-card--dynamic-width ipc-sub-grid-item ipc-sub-grid-item--span-2")

        for new_movie in movies:
            a_tag = new_movie.find("a", class_="ipc-lockup-overlay ipc-focusable")
            new_url = "https://www.imdb.com" + a_tag["href"]
            parsed_url = urlparse(new_url)
            clean_url = urlunparse(parsed_url._replace(query=""))
            self.periodic_queue.put(URL(clean_url, URLType.IMDB))

        self.storage.store_movie(movie, URLType.IMDB)

# Lista de infos:
# url -> Ok
# title -> Ok
# genres -> Ok
# release_date_theater -> Ok
# release_date_streaming -> Não tem no IMDB
# synopsis -> Ok
# length -> Ok, mas está em ISO 8601
# directors -> Ok
# cast -> Ok
# platforms -> Não vem com o html
# content_rating -> Ok
# crit_avr_rating
# crit_rev_count
# crit_reviews -> Todas são reviews externas, remover esse atributo?
# usr_avr_rating -> Ok
# usr_reviews -> Ok
# usr_rev_count -> Ok
