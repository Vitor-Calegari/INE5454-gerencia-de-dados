from src.scrapers.scraper import Scraper
from typing import override
from src.data_structures.url import URLType, URL
from src.data_structures.movie import Movie
from src.data_structures.review import Review
import requests
from bs4 import BeautifulSoup
from src.storage import Storage
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36"
}

class RottScraper(Scraper):
    
    def __init__(self, periodic_queue, storage: Storage):
        super().__init__(periodic_queue, storage)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
    
    def scrapJSONLD(self, site: BeautifulSoup, movie: Movie):
        script_tag = site.find("script", type="application/ld+json")
        if script_tag:

            data = json.loads(script_tag.string)
            
            try:
                title = (data.get("name")).strip()
                if not title:
                    return 1
                movie.set_title(str(title))
            except Exception:
                return 1
            
            try:
                directors = [(d["name"]).strip() for d in data.get("director", [])]
                movie.set_directors(directors)
            except Exception as e:
                print("Error: ", e)
            
            try:
                genres = data.get("genre", [])
                genre_list = [g.strip() for genre in genres for g in genre.split("&")]
                movie.set_genres(genre_list)
            except Exception as e:
                print("Error: ", e)

            try:
                content_rating = (data.get("contentRating")).strip()
                movie.set_content_rating(content_rating)
            except Exception as e:
                print("Error: ", e)

            return 0
        else:
            return 1
        
    @override
    def scrap(self):
        url = self.periodic_queue.get()
        if (url.get_type() == URLType.END):
            return
        
        response = requests.get(url.get_url(), headers=self.headers)
        if not response.ok:
            print(f"Nao foi possivel obter o html de {url}")
            print(f"Conteudo retornado:")
            print(response.content)
            return
        
        movie = Movie()
        movie.set_url(url=url.get_url())
        site = BeautifulSoup(response.content, "html.parser")

        if self.scrapJSONLD(site, movie) == 1:
            return
        # extração principal
        # movie.set_title(self._get_title(site))
        # movie.set_genres(self._get_genres(site))
        # movie.set_release_date(self._get_release_date(site, "Release Date (Theaters)"))
        # content_rating, length = self._get_metadata(site)
        # movie.set_content_rating(content_rating)
        # movie.set_length(length)
        # movie.set_synopsis(self._get_synopsis(site))
        # movie.set_directors(self._get_directors(site))
        # movie.set_cast(self._get_cast(url_str))
        # crit_score, usr_score = self._get_scores(site)
        # movie.set_crit_avr_rating(crit_score)
        # movie.set_usr_avr_rating(usr_score)
        # movie.set_usr_reviews(self._get_user_reviews(url_str))
        # movie.set_crit_reviews(self._get_critic_reviews(url_str))

        # more_like_this = site.find("section", {"data-qa": "section:more-like-this"})
        # if more_like_this:
        #     # Dentro dela, procura todos os <rt-link> que tenham o slot "primaryImage"
        #     for link_tag in more_like_this.select('rt-link[slot="primaryImage"]'):
        #         href = link_tag.get("href")
        #         if href and href.startswith("/m/"):  # garante que é link de filme
        #             self.periodic_queue.put(URL("https://www.rottentomatoes.com" + href, URLType.ROTT))
                    
        # self.storage.store_movie(movie, URLType.ROTT)
        return movie

    # ---------------------- FUNÇÕES AUXILIARES ----------------------

    def _get_title(self, site: BeautifulSoup) -> str:
        tag = site.find("rt-text", {"slot": "title", "context": "heading"})
        return tag.text.strip() if tag else ""

    def _get_genres(self, site: BeautifulSoup) -> list[str]:
        tags = site.find_all("rt-text", {"slot": "metadataGenre"})
        return [t.text.strip() for t in tags]

    def _get_release_date(self, site: BeautifulSoup, label: str) -> str:
        wraps = site.find_all("div", {"class": "category-wrap", "data-qa": "item"})
        for wrap in wraps:
            lbl = wrap.find("rt-text", {"data-qa": "item-label"})
            if lbl and lbl.text.strip() == label:
                val = wrap.find("rt-text", {"data-qa": "item-value"})
                return val.text.strip() if val else ""
        return ""

    def _get_metadata(self, site: BeautifulSoup) -> str:
        metadata = site.find_all("rt-text", {"slot": "metadataProp", "context": "label"})
        content_rating = metadata[0].text.strip() if metadata[0] else ""
        length = ""
        if len(metadata) >= 3:
            length = metadata[2].text.strip()
        return content_rating, length

    def _get_synopsis(self, site: BeautifulSoup) -> str:
        tag = site.find("rt-text", {"data-qa": "synopsis-value"})
        return tag.text.strip() if tag else ""

    def _get_directors(self, site: BeautifulSoup) -> list[str]:
        directors = []
        wraps = site.find_all("div", {"class": "category-wrap", "data-qa": "item"})
        for wrap in wraps:
            label_tag = wrap.find("rt-text", {"data-qa": "item-label"})
            if label_tag and label_tag.text.strip() == "Director":
                director_tags = wrap.find_all("rt-link", {"data-qa": "item-value"})
                directors.extend([t.text.strip() for t in director_tags])
        return directors

    def _get_cast(self, url: str) -> list[str]:
        url_cast = f"{url}/cast-and-crew"
        site = self._get_html(url_cast)
        if not site:
            return []
        cast = []
        cards = site.find_all("cast-and-crew-card", {"data-role": "all,cast"})
        for card in cards:
            credit_tag = card.find("rt-text", {"slot": "credits"})
            if credit_tag and credit_tag.text.strip() == "Actor":
                name_tag = card.find("rt-text", {"slot": "title"})
                if name_tag:
                    cast.append(name_tag.text.strip())
        return cast

    def _get_scores(self, site: BeautifulSoup) -> tuple[float, float]:
        scorecard = site.find("div", {"class": "media-scorecard"})
        crit, usr = "", ""
        if scorecard:
            crit_tag = scorecard.find("rt-text", {"slot": "criticsScore", "context": "label"})
            usr_tag = scorecard.find("rt-text", {"slot": "audienceScore", "context": "label"})
            crit = crit_tag.text.strip() if crit_tag else ""
            usr = usr_tag.text.strip() if usr_tag else ""
        return crit, usr


    def _get_user_reviews(self, url: str) -> list[Review]:
        url_usr = f"{url}/reviews?type=user"
        site = self._get_html(url_usr)
        if not site:
            return []

        reviews = []
        for review_div in site.find_all("div", class_="audience-review-row"):
            texto_tag = review_div.find("p", {"data-qa": "review-text"})
            texto = texto_tag.get_text(strip=True) if texto_tag else ""

            score_tag = review_div.find("rating-stars-group")
            nota = float(score_tag["score"]) if score_tag and score_tag.has_attr("score") else ""

            data_tag = review_div.find("span", {"data-qa": "review-duration"})
            data = data_tag.get_text(strip=True) if data_tag else ""

            review = Review()
            review.set_text(texto)
            review.set_rating(nota)
            review.set_date(data)
            reviews.append(review)
        return reviews

    def _get_critic_reviews(self, url: str) -> list[Review]:
        url_rev = f"{url}/reviews"
        site = self._get_html(url_rev)
        if not site:
            return []

        reviews = []
        for review_div in site.find_all("div", class_="review-row"):
            # nota
            nota = ""
            score_tag = review_div.find("p", class_="original-score-and-url")
            if score_tag:
                parts = score_tag.get_text(strip=True).split("Original Score:")
                if len(parts) > 1:
                    nota = parts[1].split("|")[0].strip()

            data_tag = review_div.find("span", {"data-qa": "review-date"})
            data = data_tag.get_text(strip=True) if data_tag else ""

            texto_tag = review_div.find("p", {"data-qa": "review-quote", "class": "review-text"})
            texto = texto_tag.get_text(strip=True) if texto_tag else ""

            review = Review()
            review.set_text(texto)
            review.set_rating(nota)
            review.set_date(data)
            reviews.append(review)
        return reviews

