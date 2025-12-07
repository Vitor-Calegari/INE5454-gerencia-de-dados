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
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import pandas as pd


class IMDBScraper(Scraper):

    def __init__(self, periodic_queue: PeriodicQueue, storage: Storage) -> None:
        super().__init__(periodic_queue, storage)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        self.count = 0


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
        url_str = movie.get_url()
        try:
            script_tag = site.find("script", type="application/ld+json")
            if script_tag:

                data = json.loads(script_tag.string)

                # Extracting details from JSON-LD
                try:
                    title = (data.get("name")).strip()
                    if not title:
                        return 1
                    movie.set_title(str(title))
                except Exception:
                    return 1
                
                try:
                    movie.set_genres([g.strip() for g in data.get("genre", [])])
                except Exception as e:
                    print(f"[ERROR] Falha ao obter os gêneros na URL {url_str}. Erro: {e}")

                try:
                    movie.set_release_date(data.get("datePublished").strip())
                except Exception as e:
                    print(f"[ERROR] Falha ao obter data de lançamento na URL {url_str}. Erro: {e}")

                try:
                    movie.set_synopsis((data.get("description")).strip())
                except Exception as e:
                    print(f"[ERROR] Falha ao obter sinopse na URL {url_str}. Erro: {e}")

                try:
                    duration = data.get("duration")
                    if duration:
                            pd_duration = pd.to_timedelta(duration)
                            formatted = str(pd_duration).split()[-1]
                            movie.set_length(formatted.strip())
                except Exception as e:
                    print(f"[ERROR] Falha ao obter duração do filme na URL {url_str}. Erro: {e}")

                # Extracting content rating
                try:
                    movie.set_content_rating((data.get("contentRating")).strip())
                except Exception as e:
                    print(f"[ERROR] Falha ao obter a classificação indicativa na URL {url_str}. Erro: {e}")

                # Extracting user ratings
                aggregate_rating = data.get("aggregateRating", {})
                try:
                    ratingValue = aggregate_rating.get("ratingValue")
                    movie.set_usr_avr_rating(float(ratingValue))
                except Exception as e:
                    print(f"[ERROR] Falha ao obter nota média de reviews usuários na URL {url_str}. Erro: {e}")

                try:
                    ratingCount = aggregate_rating.get("ratingCount")
                    movie.set_usr_rev_count(int(ratingCount))
                except Exception as e:
                    print(f"[ERROR] Falha ao obter quantidade de reviews de usuários na URL {url_str}. Erro: {e}")
                
                return 0
            else:
                return 1
        except Exception as e:
            print(f"[ERROR] Falha ao obter JSON-LD da URL {url_str}. Erro: {e}")
            return 1

    def scrapPoster(self, site: BeautifulSoup, movie: Movie):
        try:
            poster_div = site.find('div', class_='ipc-media ipc-media--poster-27x40 ipc-image-media-ratio--poster-27x40 ipc-media--media-radius ipc-media--baseAlt ipc-media--poster-l ipc-poster__poster-image ipc-media__img')
        
            if poster_div:
                img_tag = poster_div.find('img')
                if img_tag and 'src' in img_tag.attrs:
                    movie.set_poster_link(img_tag['src'].strip())
        except Exception as e:
            print(f"[ERROR] Falha ao obter link do poster na URL {movie.get_url()}. Erro: {e}")
        
    def scrapDirector(self, site: BeautifulSoup, movie: Movie):
        try:
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
                        if director.text:
                            movie.add_director(director.text.strip())
        except Exception as e:
            print(f"[ERROR] Falha ao obter os diretores na URL {movie.get_url()}. Erro: {e}")

    def scrapCast(self, site: BeautifulSoup, movie: Movie):
        try:
            # Extrai membros do cast
            cast_tags = site.find_all("a", {"data-testid": "title-cast-item__actor"})
            cast = [a.get_text(strip=True) for a in cast_tags if a.get_text(strip=True)]
            if cast:
                movie.set_cast(cast)
        except Exception as e:
            print(f"[ERROR] Falha ao obter o elenco na URL {movie.get_url()}. Erro: {e}")

    def scrapUsrReviews(self, url: URL, movie: Movie):
        # Usr reviews
        usr_review_url = url.get_url() + "reviews"
        resp = requests.get(usr_review_url, headers=self.headers)

        if not resp.ok:
            print(f"Nao foi possivel obter o html de {usr_review_url}")
            print(f"Conteudo retornado:")
            print(resp.content)
            return
        
        try:
            reviews_site = BeautifulSoup(resp.text, "html.parser")
            # encontra todos os containers de reviews
            review_divs = reviews_site.find_all("article")
            if not review_divs:
                # talvez a nova classe
                review_divs = reviews_site.find_all(
                    "div", class_="lister-item mode-detail imdb-user-review"
                )
            
            if review_divs:
                for div in review_divs:
                    try:
                        rating = None
                        # extrai a nota
                        rating_span = div.find("span", class_="ipc-rating-star--rating")
                        if rating_span:
                            rating = float(rating_span.get_text(strip=True))

                        # extrai o texto do review
                        text_div = div.find("div", class_="ipc-html-content-inner-div")
                        comment = text_div.get_text(strip=True) if text_div else None

                        # data da review
                        date_span = div.find("li", class_="ipc-inline-list__item review-date")
                        date = date_span.get_text(strip=True) if date_span else None
                        datetime = pd.to_datetime(date, format="%b %d, %Y") if date else None
                        data_formatada = (datetime.strftime("%Y-%m-%d")).strip() if datetime else None
                        usr_review = Review()
                        usr_review.set_date(data_formatada)
                        usr_review.set_rating(rating)
                        usr_review.set_text(comment)
                        movie.add_user_review(usr_review)
                    except Exception as e:
                        print("Error: ", e)
        except Exception as e:
            print(f"[ERROR] Falha ao obter ou processar reviews de usuários na URL {usr_review_url}. Erro: {e}")

    def scrapCritReviews(self, url: URL, movie: Movie):
        # Crit reviews
        crit_review_url = url.get_url() + "criticreviews"
        resp = requests.get(crit_review_url, headers=self.headers)

        if not resp.ok:
            print(f"Nao foi possivel obter o html de {crit_review_url}")
            print(f"Conteudo retornado:")
            print(resp.content)
            return
        try:
            reviews_site = BeautifulSoup(resp.text, "html.parser")

            try:
                metascore_header = reviews_site.find("div", class_=re.compile(r'^sc-88e7efde-1'))
                rating = int(metascore_header.text.strip())/10
                movie.set_crit_avr_rating(rating)
            except Exception as e:
                print(f"[ERROR] Falha ao obter nota média de reviews de crítico na URL {crit_review_url}. Erro: {e}")

            # encontra cada bloco de review
            script_tag = reviews_site.find("script", type="application/json")
            if script_tag:
                data = json.loads(script_tag.string)
                try :
                    reviewCount = data['props']['pageProps']['contentData']['data']['title']['metacritic']["metascore"]["reviewCount"]
                    int_review_count = int(reviewCount)
                    movie.set_crit_rev_count(int_review_count)
                except Exception as e:
                    print(f"[ERROR] Falha ao obter quantidade de reviews de crítico na URL {crit_review_url}. Erro: {e}")
                
                try:
                    reviews = data['props']['pageProps']['contentData']['data']['title']['metacritic']['reviews']['edges']
                    for reviewContainer in reviews:
                        try:
                            review = reviewContainer.get("node")
                            # nota do crítico (pode estar em um span, strong ou outro elemento)
                            rating = review["score"]
                            rating_formatted = int(rating)/10 if rating else None
                            text = (review["quote"]["value"]).strip()
                            rev = Review()
                            rev.set_rating(rating_formatted)
                            rev.set_text(text)
                            movie.add_critic_review(rev)
                        except Exception as e:
                            print(f"[ERROR] Falha ao obter uma review de crítico na URL {crit_review_url}. Erro: {e}")
                except Exception as e:
                    print(f"[ERROR] Falha ao obter reviews de crítico na URL {crit_review_url}. Erro: {e}")
        except Exception as e:
            print(f"[ERROR] Falha ao obter ou processar reviews de críticos na URL {crit_review_url}. Erro: {e}")
           

    def scrapNewMovies(self, site: BeautifulSoup, url_str: str):
        try:
            section = site.find("section", {"data-testid": "MoreLikeThis"})
            if section:
                movies = section.find_all(
                    "div",
                    class_="ipc-poster-card ipc-poster-card--base ipc-poster-card--media-radius ipc-poster-card--dynamic-width ipc-sub-grid-item ipc-sub-grid-item--span-2",
                )
                if movies:
                    for new_movie in movies:
                        a_tag = new_movie.find("a", class_="ipc-poster-card__title ipc-poster-card__title--clamp-2 ipc-poster-card__title--clickable")
                        new_url = "https://www.imdb.com" + a_tag["href"]
                        parsed_url = urlparse(new_url)
                        clean_url = urlunparse(parsed_url._replace(query=""))
                        self.periodic_queue.put(URL(clean_url, URLType.IMDB))
        except Exception as e:
            print(f"[ERROR] Falha ao processar seção 'more like this' em {url_str}. Erro: {e}")
    
    def scrapStreamingPlataforms(self, url:URL, movie: Movie):
        options = Options()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--headless")  # roda sem abrir janela

        try:
            service = Service()
            service.startup_timeout = 20
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url.get_url())
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
                except Exception as e:
                    print(f"[ERROR] Falha ao processar uma plataforma de streaming da URL {url.get_url()}. Erro: {e}")
                
            driver.quit()
        except TimeoutException as e:
            print(f"[TIMEOUT] ChromeDriver excedeu o tempo limite ao inicializar. URL: {url.get_url()}. Erro: {e}")
            return
        except Exception as e:
            print(f"[ERROR] Falha ao coletar plataformas de streaming da URL {url.get_url()}. Erro: {e}")
        

    @override
    def scrap(self):
        url = self.periodic_queue.get()

        if url.get_type() == URLType.END:
            return

        print(f"[INFO] Iniciando web scraping da URL: {url.get_url()}")
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
            print(f"[ERROR] Nenhum título foi encontrado na URL: {url.get_url()}. O scraping desta página será interrompido.")
            return
        self.scrapPoster(site, movie)
        self.scrapDirector(site, movie)
        self.scrapCast(site, movie)
        self.scrapUsrReviews(url, movie)
        self.scrapCritReviews(url, movie)
        self.scrapNewMovies(site, url.get_url())
        self.scrapStreamingPlataforms(url, movie)
        self.count += 1
        self.storage.store_movie(movie, URLType.IMDB)
        print(f"[INFO] Concluída a coleta de dados da URL: {url.get_url()}. Quantidade de filmes coletados do IMDB: {self.count}")


# Lista de infos:
# url -> Ok
# title -> Ok
# genres -> Ok
# release_date -> Ok
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
