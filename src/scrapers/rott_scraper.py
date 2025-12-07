from src.scrapers.scraper import Scraper
from typing import override
from src.data_structures.url import URLType, URL
from src.data_structures.movie import Movie
from src.data_structures.review import Review
import requests
from bs4 import BeautifulSoup
from src.storage import Storage
import json
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

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
        self.name = "Rotten Tomatoes"
    
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
    
    def scrapMovieInfo(self, site: BeautifulSoup, movie: Movie):
        section = site.find("section", {"class": "media-info"})
        if section:
            try:
                synopsis_tag = section.find("rt-text", {"data-qa": "synopsis-value"})
                synopsis = synopsis_tag.get_text(strip=True)
                movie.set_synopsis(synopsis)
            except Exception as e:
                print("Error: ", e)
            
            dates = []
            wraps = section.find_all("div", {"class": "category-wrap", "data-qa": "item"})
            for wrap in wraps:
                try:
                    label_tag = wrap.find("rt-text", {"data-qa": "item-label"})
                    if label_tag and "release date" in label_tag.text.strip().lower():
                        try:
                            val = wrap.find(attrs={"data-qa": "item-value"})
                            if val:
                                raw = val.text.strip()
                                # remover coisas extras tipo ", Wide"
                                parts = raw.split(", ")
                                if len(parts) > 2:
                                    cleaned = f"{parts[0]}, {parts[1]}"
                                else:
                                    cleaned = raw

                                dt = pd.to_datetime(cleaned).strftime("%Y-%m-%d").strip()
                                dates.append(dt)
                        except Exception as e:
                            print("Error: ", e)

                    elif label_tag and label_tag.text.strip().lower() == "runtime":
                        try:
                            val = wrap.find(attrs={"data-qa": "item-value"})
                            if val:
                                length = val.text.strip()
                                pd_length = pd.to_timedelta(length)
                                length_formatted = str(pd_length).split()[-1]
                                movie.set_length(length_formatted)
                        except Exception as e:
                            print("Error: ", e)
                except Exception as e:
                    print("Error: ", e)

            if dates:
                oldest_date = min(dates)
                movie.set_release_date(oldest_date)
     
    def scrapCast(self, movie: Movie, url: str):
        url_cast = f"{url}/cast-and-crew"

        response = requests.get(url_cast, headers=headers)
        if not response.ok:
            print(f"Nao foi possivel obter o html de {url_cast}")
            print(f"Conteudo retornado:")
            print(response.content)
            return
        
        try:
            cast_site = BeautifulSoup(response.content, "html.parser")
            script_tag = cast_site.find("script", type="application/ld+json")
            if script_tag:

                raw_json = script_tag.string.strip()
                data = json.loads(raw_json)
                actor_data = data.get("actor")
                for person in actor_data:
                    try:
                        name = person.get("name").strip()
                        if name:
                            movie.add_cast_member(name)
                    except Exception as e:
                        print("Error: ", e)
        except Exception as e:
            print("Error: ", e)

    def scrapRevData(self, site: BeautifulSoup, movie: Movie):
        script_tag = site.find("script", id="media-scorecard-json")

        try:
            if script_tag:
                raw_json = script_tag.text.strip()
                data = json.loads(raw_json)
                
                if data:
                    aud = data["audienceScore"]
                    crit = data["criticsScore"]

                    if aud:
                        try:
                            aud_review_count = int(aud["reviewCount"])
                            movie.set_usr_rev_count(aud_review_count)
                        except Exception as e:
                            print("Error: ", e)

                        try:
                            aud_score_percent = int(aud["scorePercent"].replace("%", ""))
                            movie.set_usr_avr_recommendation(aud_score_percent)
                        except Exception as e:
                            print("Error: ", e)

                        try:
                            aud_avg_rating = float(aud["averageRating"])*2   # *2 pra transformar nota até 5 em até 10
                            movie.set_usr_avr_rating(aud_avg_rating)
                        except Exception as e:
                            print("Error: ", e)
                    
                    if crit:
                        try:
                            crit_review_count = int(crit["reviewCount"])
                            movie.set_crit_rev_count(crit_review_count)
                        except Exception as e:
                            print("Error: ", e)
                        
                        try:
                            crit_score_percent = int(crit["scorePercent"].replace("%", ""))
                            movie.set_crit_avr_recommendation(crit_score_percent)
                        except Exception as e:
                            print("Error: ", e)

                        try:
                            crit_avg_rating = float(crit["averageRating"])
                            movie.set_crit_avr_rating(crit_avg_rating)
                        except Exception as e:
                            print("Error: ", e)

        except Exception as e:
            print("Error: ", e)

    def scrapUsrReviews(self, movie: Movie, url: str):
        url_rev = f"{url}/reviews?type=user"

        response = requests.get(url_rev, headers=headers)
        if not response.ok:
            print(f"Nao foi possivel obter o html de {url_rev}")
            print(f"Conteudo retornado:")
            print(response.content)
            return
        
        try:
            rev_site = BeautifulSoup(response.content, "html.parser")

            for review_div in rev_site.find_all("div", class_="audience-review-row"):
                try:
                    texto_tag = review_div.find("p", {"data-qa": "review-text"})
                    texto = texto_tag.get_text(strip=True) if texto_tag else None

                    score_tag = review_div.find("rating-stars-group")
                    nota = float(score_tag["score"])*2 if score_tag and score_tag.has_attr("score") else None

                    data_tag = review_div.find("span", {"data-qa": "review-duration"})
                    date = data_tag.get_text(strip=True) if data_tag else None
                    if date:
                        date_formatted = pd.to_datetime(date).strftime("%Y-%m-%d").strip()

                    review = Review()
                    review.set_text(texto)
                    review.set_rating(nota)
                    review.set_date(date_formatted)
                    movie.add_user_review(review)
                except Exception as e:
                    print("Error: ", e)

        except Exception as e:
            print("Error: ", e)

    def scrapCritReviews(self, movie: Movie, url: str):
        url_rev = f"{url}/reviews"

        response = requests.get(url_rev, headers=headers)
        if not response.ok:
            print(f"Nao foi possivel obter o html de {url_rev}")
            print(f"Conteudo retornado:")
            print(response.content)
            return
        
        try:
            rev_site = BeautifulSoup(response.content, "html.parser")

            for review_div in rev_site.find_all("div", class_="review-row"):
                try:
                    nota = None
                    score_tag = review_div.find("p", class_="original-score-and-url")
                    if score_tag:
                        parts = score_tag.get_text(strip=True).split("Original Score:")
                        if len(parts) > 1:
                            raw = parts[1].split("|")[0].strip()
                            raw = raw.strip().upper()

                            # 1) IGNORAR notas em letra
                            if re.match(r"^[A-F][+-]?$", raw):
                                pass

                            # 2) Frações (3/4, 9/10 etc.)
                            elif "/" in raw and re.match(r"^\d+(\.\d+)?/\d+(\.\d+)?$", raw):
                                num, den = raw.split("/")
                                num = float(num)
                                den = float(den)
                                if den == 0:
                                    pass
                                nota = round((num / den) * 10, 2)

                            # 3) Número direto (0–10)
                            elif re.match(r"^\d+(\.\d+)?$", raw):
                                value = float(raw)
                                if value <= 10:
                                    nota = value
                                # caso improvável (nota tipo 80/100 sem barra)
                                nota = round((value / 100) * 10, 2)

                    data_tag = review_div.find("span", {"data-qa": "review-date"})
                    date = data_tag.get_text(strip=True) if data_tag else None
                    if date:
                        date_formatted = pd.to_datetime(date).strftime("%Y-%m-%d").strip()
                            
                    texto_tag = review_div.find("p", {"data-qa": "review-quote", "class": "review-text"})
                    texto = texto_tag.get_text(strip=True) if texto_tag else None
                    
                    review = Review()
                    review.set_text(texto)
                    review.set_rating(nota)
                    review.set_date(date_formatted)
                    movie.add_critic_review(review)

                except Exception as e:
                    print("Error: ", e)
        except Exception as e:
            print("Error: ", e)

    def scrapNewMovies(self, site: BeautifulSoup):
        try:
            more_like_this = site.find("section", {"data-qa": "section:more-like-this"})
            if more_like_this:
                # Dentro dela, procura todos os <rt-link> que tenham o slot "primaryImage"
                for link_tag in more_like_this.select('rt-link[slot="primaryImage"]'):
                    href = link_tag.get("href")
                    if href and href.startswith("/m/"):  # garante que é link de filme
                        self.periodic_queue.put(URL("https://www.rottentomatoes.com" + href.strip(), URLType.ROTT))
        except Exception as e:
            print("Error: ", e)

    def scrapDynamicData(self, url: URL, movie: Movie):
        options = Options()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--headless")  # roda sem abrir janela
        driver = webdriver.Chrome(options=options)

        driver.get(url.get_url())  # The Matrix
        time.sleep(3)  # espera carregar o widget

        # Encontra o iframe correto dentro da div data-wheretowatchmanager="jwContainer"
        iframe = driver.find_element(
            By.XPATH,
            "//div[@data-wheretowatchmanager='jwContainer']//iframe[contains(@class, 'jw-widget-iframe')]"
        )

        # muda o contexto para dentro do iframe
        driver.switch_to.frame(iframe)

        time.sleep(2)  # espera o conteúdo dinâmico carregar

        # Encontra todos os blocos de ofertas (plataformas)
        offers = driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'jw-offer')]/a"
        )

        platforms = []
        for offer in offers:
            link = offer.get_attribute("href")
            try:
                img = offer.find_element(By.TAG_NAME, "img")
                platform_name = img.get_attribute("alt") or img.get_attribute("title")
            except:
                platform_name = "Unknown"
            platforms.append((platform_name, link))

        # exibe resultado
        for name, link in platforms:
            print(f"{name}: {link}")

        # sai do iframe e encerra
        driver.switch_to.default_content()
        driver.quit()

    @override
    def scrap(self):
        url = self.periodic_queue.get(timeout=5)

        if (url.get_type() == URLType.END):
            return
        
        url_str = url.get_url()
        response = requests.get(url_str, headers=self.headers)
        if not response.ok:
            print(f"Nao foi possivel obter o html de {url}")
            print(f"Conteudo retornado:")
            print(response.content)
            return
        
        movie = Movie()
        movie.set_url(url=url_str)
        site = BeautifulSoup(response.content, "html.parser")

        if self.scrapJSONLD(site, movie) == 1:
            return
        
        self.scrapMovieInfo(site, movie)
        self.scrapCast(movie, url_str)
        self.scrapRevData(site, movie)
        self.scrapUsrReviews(movie, url_str)
        self.scrapCritReviews(movie, url_str)
        # self.scrapDynamicData(url, movie)
        self.scrapNewMovies(site)
                    
        self.storage.store_movie(movie, URLType.ROTT)