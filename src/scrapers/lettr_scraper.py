from src.data_structures.review import Review
from src.scrapers.scraper import Scraper
from src.data_structures.movie import Movie
from src.data_structures.url import URL, URLType
from src.data_structures.plataform import Plataform
from typing import override
from src.storage import Storage
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import logging
import requests
from datetime import datetime
import re
import json
from dateutil.parser import parse


class LettrScraper(Scraper):

    def __init__(self, periodic_queue, storage: Storage):
        super().__init__(periodic_queue, storage)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        }
        self.count = 0

    @override
    def scrap(self):
        url = self.periodic_queue.get()

        if url.get_type() == URLType.END:
            return

        url_str = url.get_url()
        response = requests.get(url_str, headers=self.headers)

        if not response.ok:
            print(f"[ERROR] Nao foi possivel obter o html de {url_str}")
            print(f"Conteudo retornado:")
            print(response.content)
            return

        site = BeautifulSoup(response.content, "html.parser")

        if site:
            print(f"[INFO] Iniciando web scraping da URL: {url_str}")
            movie = Movie()
            movie.set_url(url=url_str)

            title, directors = self.get_details(site, url_str)
            if not title:
                print(f"[ERROR] Nenhum título foi encontrado na URL: {url_str}. O scraping desta página será interrompido.")
                return
            movie.set_title(title)
            movie.set_directors(directors)

            poster = self.get_poster(site, url_str)
            movie.set_poster_link(poster)
            synopsis = self.get_synopsis(site, url_str)
            movie.set_synopsis(synopsis)

            section = site.find("div", {"id": "tabbed-content"})
            if section:
                movie.set_cast(self.get_cast(section, url_str))
                movie.set_release_date(self.get_release_date(section, url_str))
                movie.set_genres(self.get_genres(section, url_str))

            movie.set_length(self.get_length(site, url_str))

            self.scrap_reviews(site, movie)

            try:
                with sync_playwright() as p:

                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()

                    try:
                        page.goto(url.get_url(), wait_until="domcontentloaded")

                        avr, count = self.get_ratings_stats(page, url_str)
                        movie.set_usr_avr_rating(avr)
                        movie.set_usr_rev_count(count)    

                        links = self.get_similar_movies(page, url_str)            
                        for link in links:
                            self.periodic_queue.put(URL(link, URLType.LTTR))
                            
                        movie.set_platforms(self.get_plataforms(page, url_str))
                    except Exception as e:
                        print(f"[ERROR] Falha ao processar URL {url_str} no Playright. Erro: {e}")
                    finally:
                        browser.close()
            except Exception as e:
                print(f"[ERROR] Falha ao iniciar Playright ou navegador para URL {url_str}. Erro: {e}")
            
            self.count += 1
            print(f"[INFO] Concluída a coleta de dados da URL: {url_str}. Quantidade de filmes coletados do Letterboxd: {self.count}")
            self.storage.store_movie(movie, URLType.LTTR)

    def get_details(self, site, url_str):
        title = None
        director_names = []
        details = site.find("div", {"class": "details"})
        if details:
            try:
                title = details.find("span", {"class": "name js-widont prettify"}).text
            except Exception:
                pass
            try:
                directors = details.find_all("a", class_="contributor")
                if directors:
                    director_names = [a.text.strip() for a in directors]
            except Exception as e:
                print(f"[ERROR] Falha ao obter os diretores na URL {url_str}. Erro: {e}")
        return title, director_names
    
    def get_poster(self, site, url_str):
        link = None
        try:
            script_tag = site.find("script", type="application/ld+json")
            if script_tag and script_tag.string:

                raw = script_tag.string.strip()

                # Remove comentários CDATA
                raw = raw.replace("/* <![CDATA[ */", "").replace("/* ]]> */", "").strip()

                data = json.loads(raw)
                if data:
                    link = data.get("image").strip()
        except Exception as e:
            print(f"[ERROR] Falha ao obter o link do poster na URL {url_str}. Erro: {e}")
        return link

    def get_synopsis(self, site, url_str):
        synopsis = None
        try:
            synopsis_section = site.find("section", {"class": "production-synopsis"})
            if synopsis_section:
                synopsis = synopsis_section.find("p").text.strip()
        except Exception as e:
            print(f"[ERROR] Falha ao obter a sinopse na URL {url_str}. Erro: {e}")
        return synopsis

    def get_cast(self, site, url_str):
        cast = []
        try:
            details = site.find("div", {"class": "cast-list text-sluglist"})
            if details:
                cast_tags = details.find_all("a", class_="text-slug tooltip")
                if cast_tags:
                    cast = [a.text.strip() for a in cast_tags]
        except Exception as e:
            print(f"[ERROR] Falha ao obter a sinopse na URL {url_str}. Erro: {e}")
        return cast

    def get_release_date(self, site, url_str):
        release_date_final = None
        try:
            div_dates = site.find("section", {"class": "release-table-group"})
            if div_dates:
                list_realease_dates = div_dates.find_all("div", class_="listitem")
                if list_realease_dates:
                    for list_item in list_realease_dates:
                        country_names = list_item.find_all("span", class_="name")
                        if country_names:
                            country_names_list = [a.text.strip() for a in country_names]
                            if "Brazil" in country_names_list:
                                release_date = list_item.find("h5").text
                                try:
                                    release_date_format = datetime.strptime(release_date, "%d %b %Y").strftime("%Y-%m-%d")
                                    
                                    if not release_date_final:
                                        release_date_final = release_date_format
                                    else:
                                        if release_date_format < release_date_final:
                                            release_date_final = release_date_format
                                except Exception as e:
                                    print(f"[ERROR] Falha ao processar data de lançamento na URL {url_str}. Erro: {e}")
        except Exception as e:
            print(f"[ERROR] Falha ao obter data de lançamento na URL {url_str}. Erro: {e}")
        return release_date_final
                           
                

    def get_genres(self, site, url_str):
        genres = []
        try:
            genre_div = site.find("div", class_="text-sluglist capitalize")
            if genre_div:
                genre_tags = genre_div.find_all("a")
                if genre_tags:
                    genres = [
                        "Sci-Fi" if a.text.strip().lower() == "science fiction" else a.text.strip()
                        for a in genre_tags
                    ] # troca para sci-fi para deixar igual aos outros sites
        except Exception as e:
            print(f"[ERROR] Falha ao obter generos na URL {url_str}. Erro: {e}")
        return genres

    def get_length(self, site, url_str):
        lenght_format = None
        try:
            footer_text = site.find("p", {"class": "text-link text-footer"}).text
            if footer_text:
                footer_parts = footer_text.split()
                lenght = footer_parts[0] + " " + footer_parts[1]
                lenght = int(footer_parts[0])
                hour = lenght // 60
                mins = lenght % 60
                lenght_format = f"{hour:02d}:{mins:02d}:00"
        except:
            print(f"[ERROR] Falha ao obter duração na URL {url_str}. Erro: {e}")
        return lenght_format
    
    # Dinamico
    def get_similar_movies(self, page, url_str):
        links = []
        try:
            section = page.locator("ul.poster-list.-p110.-horizontal.-scaled104")
            if section:
                items = section.locator("li")
                for i in range(items.count()):
                    try:
                        link = items.nth(i).locator("div.react-component").get_attribute("data-item-link")
                        links.append("https://letterboxd.com" + link)
                    except Exception as e:
                        print(f"[ERROR] Falha ao obter um filme similar na URL {url_str}. Erro: {e}")
        except Exception as e:
            print(f"[ERROR] Falha ao obter filmes similares na URL {url_str}. Erro: {e}")
        return links

    # --> Dinâmico
    def get_ratings_stats(self, page, url_str):
        num_average_format = None
        num_ratings = None
        try:
            section = page.locator("section.ratings-histogram-chart")
            if section:
                avg_rating_sec = section.locator("span.average-rating a")
                if avg_rating_sec:
                    avg_rating = avg_rating_sec.get_attribute(
                        "data-original-title"
                    )
                    if avg_rating:
                        numbers = re.findall(r"[\d,]+\.\d+|[\d,]+", avg_rating)
                        try:
                            num_ratings = int(numbers[1].replace(",", ""))
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar quantidade de reviews de usuários em {url_str}. Erro: {e}")
                        try:
                            num_average = float(numbers[0])
                            num_average_format = (num_average * 10)/5
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar a nota média de usuários em {url_str}. Erro: {e}")
        except Exception as e:
            print(f"[ERROR] Falha ao obter quantidade e nota média das reviews usuários em {url_str}. Erro: {e}")
                        
        return num_average_format, num_ratings
        
    # --> Dinâmico
    def get_plataforms(self, page, url_str):
        plataforms = []
        try:
            div = page.locator("section.services.-showall")
            if div:
                services = div.locator("p.service")
                if services:
                    for i in range(services.count()):
                        try:
                            service = services.nth(i)

                            platform_name = service.locator(".label .name").inner_text().strip()
                            
                            # deixando nomes das plataformas iguais aos outros scrappers
                            if platform_name == "Amazon" or platform_name == "Amazon Video":
                                platform_name = "Prime Video"
                            elif platform_name == "Apple TV Store":
                                platform_name = "Apple TV"
                            elif platform_name == "Google Play Movies":
                                platform_name = "Google Play"
                            elif platform_name == "Paramount+ MTV Amazon Channel":
                                platform_name = "Paramount+"
                                
                            platform_link = service.locator("a.label").get_attribute("href").strip()
                            if platform_name and platform_link:
                                plataforms.append(Plataform(platform_name, platform_link))
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar uma plataforma de streaming em {url_str}. Erro: {e}")
                        
        except Exception as e:
                print(f"[ERROR] Falha ao obter plataformas de streaming em {url_str}. Erro: {e}")
        return plataforms

    def scrap_reviews(self, site, movie):
        try:
            reviews_section = site.find("section", {"class": "film-reviews section js-popular-reviews"})
            if reviews_section:
                url_reviews_tag = reviews_section.find("a")
                if url_reviews_tag:
                    url_reviews = "https://letterboxd.com" + url_reviews_tag["href"]

                    response = requests.get(url_reviews, headers=self.headers)
                    if not response.ok:
                        print(f"Nao foi possivel obter o html de {url_reviews}")
                        print(f"Conteudo retornado:")
                        print(response.content)
                        return
                    
                    soup = BeautifulSoup(response.content, "html.parser")
                    if soup:
                        reviews_list = soup.select("div.viewing-list.-marginblockstart div.listitem")
                        add_review = movie.add_user_review
                        if reviews_list:
                            for i, review_tag in enumerate(reviews_list, 1):
                                try:
                                    span = review_tag.find("span", class_=re.compile(r"^rating"))
                                    if not span:
                                        continue
                                    s = span.text.strip()
                                    rating = s.count("★") + 0.5 * s.count("½")
                                    rating_format = (rating * 10) / 5
                                    date_raw = review_tag.time["datetime"]
                                    date_obj = parse(date_raw)
                                    date_format = date_obj.strftime("%Y-%m-%d")
                                    review_div = review_tag.select_one("div.body-text.-prose.-reset.js-review-body.js-collapsible-text p")
                                    if not review_div:
                                        continue
                                    r = Review()
                                    r.set_date(date_format)
                                    r.set_rating(rating_format)
                                    r.set_text(review_div.text)
                                    add_review(r)
                                except Exception as e:
                                    print(f"[ERROR] Falha ao processar uma review de usuário na URL {url_reviews}. Erro: {e}")
        except Exception as e:
            print(f"[ERROR] Falha ao obter reviews de usuários na URL {url_reviews}. Erro: {e}")
            

# Lista de infos:
# url -> Ok
# title -> Ok
# genres -> Ok
# release_date -> Ok --> Peguei do Brasil, mas atrasa a execução
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