from src.data_structures.review import Review
from src.scrapers.scraper import Scraper
from src.data_structures.movie import Movie
from src.data_structures.url import URL, URLType
from typing import override
from src.storage import Storage
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import requests
import re


class LettrScraper(Scraper):

    def __init__(self, periodic_queue, storage: Storage):
        super().__init__(periodic_queue, storage)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        }

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

        site = BeautifulSoup(response.content, "html.parser")

        if site:
            movie = Movie()
            movie.set_url(url=url.get_url())

            title, directors = self.get_details(site)
            movie.set_title(title)
            movie.set_directors(directors)

            synopsis = self.get_synopsis(site)
            movie.set_synopsis(synopsis)

            section = site.find("div", {"id": "tabbed-content"})
            movie.set_cast(self.get_cast(section))
            movie.set_release_date_theater(self.get_release_date(section))
            movie.set_genres(self.get_genres(section))

            movie.set_length(self.get_length(site))

            self.get_reviews(site, movie)

            with sync_playwright() as p:

                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                page.goto(url.get_url(), wait_until="domcontentloaded")

                avr, count = self.get_ratings_stats(page)
                movie.set_usr_avr_rating(avr)
                movie.set_usr_rev_count(count)    

                links = self.get_similar_movies(page)            
                for link in links:
                    self.periodic_queue.put(URL(link, URLType.LTTR))

                plataforms = self.get_plataforms(page)

                browser.close()

            # print(movie.__str__())
            self.storage.store_movie(movie, URLType.LTTR)

    def get_details(self, site):
        details = site.find("div", {"class": "details"})
        title = details.find("span", {"class": "name js-widont prettify"}).text
        directors = details.find_all("a", class_="contributor")
        director_names = [a.text.strip() for a in directors]
        return title, director_names

    def get_synopsis(self, site):
        synopsis_section = site.find("section", {"class": "production-synopsis"})
        synopsis = synopsis_section.find("p").text.strip()
        return synopsis

    def get_cast(self, site):
        details = site.find("div", {"class": "cast-list text-sluglist"})
        cast_tags = details.find_all("a", class_="text-slug tooltip")
        cast = [a.text.strip() for a in cast_tags]
        return cast

    def get_release_date(self, site):
        div_dates = site.find("section", {"class": "release-table-group"})
        list_realease_dates = div_dates.find_all("div", class_="listitem")
        for list_item in list_realease_dates:
            country_names = list_item.find_all("span", class_="name")
            country_names_list = [a.text.strip() for a in country_names]
            if "Brazil" in country_names_list:
                release_date = list_item.find("h5").text
                return release_date

    def get_genres(self, site):
        genre_div = site.find("div", class_="text-sluglist capitalize")
        genre_tags = genre_div.find_all("a")
        genres = [a.text.strip() for a in genre_tags]
        return genres

    def get_length(self, site):
        footer_text = site.find("p", {"class": "text-link text-footer"}).text
        footer_parts = footer_text.split()
        lenght = footer_parts[0] + " " + footer_parts[1]
        return lenght
    
    def get_similar_movies(self, page):
        section = page.locator("ul.poster-list.-p110.-horizontal.-scaled104")
        items = section.locator("li")
        links = []
        for i in range(items.count()):
            link = items.nth(i).locator("div.react-component").get_attribute("data-item-link")
            links.append("https://letterboxd.com" + link)
        return links

    # --> Dinâmico
    def get_ratings_stats(self, page):
        section = page.locator("section.ratings-histogram-chart")
        avg_rating = section.locator("span.average-rating a").get_attribute(
            "data-original-title"
        )
        numbers = re.findall(r"[\d,]+\.\d+|[\d,]+", avg_rating)
        num_average = float(numbers[0])
        num_ratings = int(numbers[1].replace(",", ""))
        return num_average, num_ratings
        
    # --> Dinâmico, usar selenium
    def get_plataforms(self, page):
        div = page.locator("section.services.-showall")
        span_locator = div.locator("span.name")
        plataforms = []
        for i in range(span_locator.count()):
            title = span_locator.nth(i).text_content()
            if title:
                plataforms.append(title)
        return plataforms

    def get_reviews(self, site, movie):
        reviews_section = site.find(
            "section", {"class": "film-reviews section js-popular-reviews"}
        )
        url_reviews_tag = reviews_section.find("a")
        url_reviews = "https://letterboxd.com" + url_reviews_tag["href"]

        response = requests.get(url_reviews, headers=self.headers)
        if response.ok:
            site = BeautifulSoup(response.content, "html.parser")
            reviews_section = site.find(
                "div", {"class": "viewing-list -marginblockstart"}
            )
            reviews_list = reviews_section.find_all("div", class_="listitem")
            for review_tag in reviews_list:
                review_score_span = review_tag.find("span", class_=re.compile(r"^rating"))

                if review_score_span:
                    review_score = review_score_span.text

                review_score_num = 0
                for char in review_score.strip():
                    if char == "★":
                        review_score_num += 1
                    else:
                        review_score_num += 0.5

                date = review_tag.find("time")["datetime"]
                review = review_tag.find("div", class_="body-text -prose -reset js-review-body js-collapsible-text") 
        
                if review:
                    review_text = review.find("p").text
                    usr_review = Review()
                    usr_review.set_date(date)
                    usr_review.set_rating(review_score_num)
                    usr_review.set_text(review_text)
                    movie.add_user_review(usr_review)
            return
        return []


# Lista de infos:
# url -> Ok
# title -> Ok
# genres -> Ok
# release_date_theater -> Ok --> Peguei do Brasil, mas atrasa a execução
# release_date_streaming -> Não tem no Letterbox
# synopsis -> Ok
# length -> Ok (em minutos)
# directors -> Ok
# cast -> Ok

# platforms -> Ok
# content_rating -> Não tem no Letterbox
# crit_avr_rating -> Não tem no Letterbox
# crit_rev_count -> Não tem no Letterbox
# crit_reviews -> Não tem no Letterbox

# usr_avr_rating -> Ok
# usr_reviews -> Ok
# usr_rev_count -> OK
