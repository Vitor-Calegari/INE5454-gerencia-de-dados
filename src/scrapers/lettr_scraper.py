from src.scrapers.scraper import Scraper
from src.data_structures.movie import Movie
from src.data_structures.url import URL, URLType
from typing import override
from src.storage import Storage
from bs4 import BeautifulSoup
import requests


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

            # detalhes iniciais
            title, directors = self.get_details(site)
            movie.set_title(title)
            movie.set_directors(directors)

            # synopsis
            synopsis = self.get_synopsis(site)
            movie.set_synopsis(synopsis)

            # section principal
            section = site.find("div", {"id": "tabbed-content"})
            # ---> cast
            movie.set_cast(self.get_cast(section))
            # --->release date (Brasil)
            movie.set_release_date_theater(self.get_release_date(section))
            # ---> genres
            movie.set_genres(self.get_genres(section))

            # legth
            movie.set_length(self.get_length(site))

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
        cast_tags = details.find_all("div", class_="text-slug tooltip")
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

# platforms -> 
# content_rating ->
# crit_avr_rating
# crit_rev_count
# crit_reviews ->
# usr_avr_rating ->
# usr_reviews ->
# usr_rev_count ->
