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
from src.data_structures.plataform import Plataform
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time


class IMDBScraper(Scraper):

    def __init__(self, periodic_queue: PeriodicQueue, storage: Storage) -> None:
        super().__init__(periodic_queue, storage)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        }

    def scrapJSONLD(self, site: BeautifulSoup, movie: Movie):
        """
        Scraps:
        - Title
        - Genre
        - Release Date
        - Synopsis
        - Duration
        - User average rating
        - User rating count
        """
        script_tag = site.find("script", type="application/ld+json")
        if script_tag:

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

    def scrapDirector(self, site: BeautifulSoup, movie: Movie):
        # Encontra o bloco onde o rótulo é "Directors"
        directors_section = site.find("span", string="Directors")

        if directors_section:
            # Pega o container logo após o span
            container = directors_section.find_next(
                "div", class_="ipc-metadata-list-item__content-container"
            )
            if container:
                # Pega todos os nomes (links)
                for director in container.find_all("a"):
                    movie.add_director(director.text.strip())

    def scrapCast(self, site: BeautifulSoup, movie: Movie):
        # Extrai membros do cast
        cast_tags = site.find_all("a", {"data-testid": "title-cast-item__actor"})
        cast = [a.get_text(strip=True) for a in cast_tags]
        movie.set_cast(cast)

    def scrapUsrReviews(self, url: URL, movie: Movie):
        # Usr reviews
        usr_review_url = url.get_url() + "reviews"
        resp = requests.get(usr_review_url, headers=self.headers)
        reviews_site = BeautifulSoup(resp.text, "html.parser")

        # encontra todos os containers de reviews
        review_divs = reviews_site.find_all("article")
        if not review_divs:
            # talvez a nova classe
            review_divs = reviews_site.find_all(
                "div", class_="lister-item mode-detail imdb-user-review"
            )

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

    def scrapCritReviews(self, url: URL, movie: Movie):
        # Crit reviews
        crit_review_url = url.get_url() + "criticreviews"
        resp = requests.get(crit_review_url, headers=self.headers)
        reviews_site = BeautifulSoup(resp.text, "html.parser")

        metascore_header = reviews_site.find("div", class_=re.compile(r'^sc-88e7efde-1'))
        movie.set_crit_avr_rating(metascore_header.text.strip())
         # encontra cada bloco de review (ajuste se necessário)
        script_tag = reviews_site.find("script", type="application/json")
        data = json.loads(script_tag.string)
        try :
            reviewCount = data['props']['pageProps']['contentData']['data']['title']['metacritic']["metascore"]["reviewCount"]
            movie.set_crit_rev_count(reviewCount)
        except:
            pass
        
        try :
            reviews = data['props']['pageProps']['contentData']['data']['title']['metacritic']['reviews']['edges']
            for reviewContainer in reviews:
                review = reviewContainer.get("node")
                # nota do crítico (pode estar em um span, strong ou outro elemento)
                rating = review["score"]
                text = review["quote"]["value"]
                rev = Review()
                rev.set_rating(rating)
                rev.set_text(text)
                movie.add_critic_review(rev)
        except:
            pass

    def scrapNewMovies(self, site: BeautifulSoup):
        section = site.find("section", {"data-testid": "MoreLikeThis"})
        movies = section.find_all(
            "div",
            class_="ipc-poster-card ipc-poster-card--base ipc-poster-card--media-radius ipc-poster-card--dynamic-width ipc-sub-grid-item ipc-sub-grid-item--span-2",
        )

        for new_movie in movies:
            a_tag = new_movie.find("a", class_="ipc-lockup-overlay ipc-focusable")
            new_url = "https://www.imdb.com" + a_tag["href"]
            parsed_url = urlparse(new_url)
            clean_url = urlunparse(parsed_url._replace(query=""))
            self.periodic_queue.put(URL(clean_url, URLType.IMDB))
    
    def scrapStreamingPlataforms(self, url:URL, movie: Movie):
        options = Options()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--headless")  # roda sem abrir janela
        driver = webdriver.Chrome(options=options)

        driver.get(url.get_url())  # The Matrix
        time.sleep(2)  # espera carregar o conteúdo dinâmico

        # encontra todos os <a> com essa classe
        stream_links = driver.find_elements(
            By.XPATH,
            "//a[contains(@class, 'ipc-lockup-overlay') and contains(@class, 'ipc-focusable') and contains(@aria-label, 'Watch on')]"
        )

        for link in stream_links:
            label = link.get_attribute("aria-label") # geralmente diz "Watch on <servico>"
            href = link.get_attribute("href")  # URL do streaming
            
            try:
                plat = Plataform(plataform=label[label.find("on") + 3:], link=href)
                movie.add_platform(plat)
            except:
                pass
            
        driver.quit()
        

    @override
    def scrap(self):
        url = self.periodic_queue.get()

        if url.get_type() == URLType.END:
            return

        response = requests.get(url.get_url(), headers=self.headers)

        if not response.ok:
            print(f"Nao foi possivel obter o html de {url}")
            print(f"Conteudo retornado:")
            print(response.content)

        movie = Movie()
        movie.set_url(url=url.get_url())
        site = BeautifulSoup(response.content, "html.parser")

        self.scrapJSONLD(site, movie)
        self.scrapDirector(site, movie)
        self.scrapCast(site, movie)
        self.scrapUsrReviews(url, movie)
        self.scrapCritReviews(url, movie)
        self.scrapNewMovies(site)
        self.scrapStreamingPlataforms(url, movie)

        self.storage.store_movie(movie, URLType.IMDB)


# Lista de infos:
# url -> Ok
# title -> Ok
# genres -> Ok
# release_date_theater -> Ok
# synopsis -> Ok
# length -> Ok, mas está em ISO 8601
# directors -> Ok
# cast -> Ok
# content_rating -> Ok
# usr_avr_rating -> Ok
# usr_reviews -> Ok
# usr_rev_count -> Ok
# crit_avr_rating -> Ok
# crit_rev_count -> Ok
# crit_reviews -> Ok
# platforms -> Ok

# release_date_streaming -> Não tem no IMDB
