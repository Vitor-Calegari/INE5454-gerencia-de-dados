from src.scrapers.scraper import Scraper
from typing import override
from src.data_structures.url import URLType, URL
from src.data_structures.movie import Movie
from src.data_structures.review import Review
from src.data_structures.plataform import Plataform
import requests
from bs4 import BeautifulSoup
from src.storage import Storage
import json
import pandas as pd
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from playwright.sync_api import sync_playwright
import urllib.parse


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
        self.count = 0
    
    def scrapJSONLD(self, site: BeautifulSoup, movie: Movie) -> int:
        try:
            url_str = movie.get_url()
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
                    directors = data.get("director", [])
                    if directors:
                        director_names = [(d["name"]).strip() for d in directors]
                        movie.set_directors(director_names)
                except Exception as e:
                    print(f"[ERROR] Falha ao obter os diretores na URL {url_str}. Erro: {e}")

                try:
                    genres = data.get("genre", [])
                    if genres:
                        genre_list = [g.strip() for genre in genres for g in genre.split("&")]
                        movie.set_genres(genre_list)
                except Exception as e:
                    print(f"[ERROR] Falha ao obter os gêneros na URL {url_str}. Erro: {e}")

                try:
                    content_rating = data.get("contentRating")
                    if content_rating:
                        content_rating = content_rating.strip()
                        movie.set_content_rating(content_rating)
                except Exception as e:
                    print(f"[ERROR] Falha ao obter a classificação indicativa na URL {url_str}. Erro: {e}")
                return 0
            else:
                return 1
        except Exception as e:
            print(f"[ERROR] Falha ao obter JSON-LD da URL {url_str}. Erro: {e}")
            return 1
    
    def scrapMovieInfo(self, site: BeautifulSoup, movie: Movie):
        url_str = movie.get_url()
        section = site.find("section", {"class": "media-info"})
        if section:
            try:
                synopsis_tag = section.find("rt-text", {"data-qa": "synopsis-value"})
                if synopsis_tag:
                    synopsis = synopsis_tag.get_text(strip=True)
                    movie.set_synopsis(synopsis)
            except Exception as e:
                print(f"[ERROR] Falha ao obter a sinopse na URL {url_str}. Erro: {e}")
            
            dates = []
            wraps = section.find_all("div", {"class": "category-wrap", "data-qa": "item"})
            if wraps:
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
                                print(f"[ERROR] Falha ao processar a data de lançamento na URL {url_str}. Erro: {e}")

                        elif label_tag and label_tag.text.strip().lower() == "runtime":
                            try:
                                val = wrap.find(attrs={"data-qa": "item-value"})
                                if val:
                                    length = val.text.strip()
                                    pd_length = pd.to_timedelta(length)
                                    length_formatted = str(pd_length).split()[-1]
                                    movie.set_length(length_formatted)
                            except Exception as e:
                                print(f"[ERROR] Falha ao processar a duração do filme na URL {url_str}. Erro: {e}")
                    except Exception as e:
                        print(f"[ERROR] Falha ao processar uma informação de categoria na URL {movie.url}. Erro: {e}")

            if dates:
                oldest_date = min(dates)
                movie.set_release_date(oldest_date)
     

    def scrapCast(self, movie: Movie, url: str):
        url_cast = f"{url}/cast-and-crew"

        response = requests.get(url_cast, headers=self.headers)
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
                if actor_data:
                    for person in actor_data:
                        try:
                            name = person.get("name")
                            if name:
                                name = name.strip()
                                if name:
                                    movie.add_cast_member(name)
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar ator no link {url_cast}. Erro: {e}")
        except Exception as e:
            print(f"[ERROR] Falha ao obter ou processar o cast na URL {url_cast}. Erro: {e}")

    def scrapRevData(self, site: BeautifulSoup, movie: Movie):
        url_str = movie.get_url()
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
                            print(f"[ERROR] Falha ao processar review de usuário (quantidade) na URL {url_str}. Erro: {e}")

                        try:
                            aud_score_percent = int(aud["scorePercent"].replace("%", ""))
                            movie.set_usr_avr_recommendation(aud_score_percent)
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar review de usuário (percentual de recomendação) na URL {url_str}. Erro: {e}")

                        try:
                            aud_avg_rating = float(aud["averageRating"])*2   # *2 pra transformar nota até 5 em até 10
                            movie.set_usr_avr_rating(aud_avg_rating)
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar review de usuário (nota média) na URL {url_str}. Erro: {e}")

                    if crit:
                        try:
                            crit_review_count = int(crit["reviewCount"])
                            movie.set_crit_rev_count(crit_review_count)
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar review de crítico (quantidade) na URL {url_str}. Erro: {e}")

                        try:
                            crit_score_percent = int(crit["scorePercent"].replace("%", ""))
                            movie.set_crit_avr_recommendation(crit_score_percent)
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar review de crítico (percentual de recomendação) na URL {url_str}. Erro: {e}")

                        try:
                            crit_avg_rating = float(crit["averageRating"])
                            movie.set_crit_avr_rating(crit_avg_rating)
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar review de crítico (nota média) na URL {url_str}. Erro: {e}")
                    poster = data["primaryImageUrl"]
                    if poster:
                        movie.set_poster_link(poster)
                    
        except Exception as e:
            print(f"[ERROR] Falha ao processar os dados de reviews na URL {url_str}. Erro: {e}")

    def parse_rotten_date(self, date_str, url_rev):
        # Converte datas do tipo '47m', '2h', '1d', 'Nov 27', '09/27/2024'
        if not date_str:
            return None

        s = date_str.lower().strip()
        now = pd.Timestamp.now()

        # minutos
        if s.endswith("m") and s[:-1].isdigit():
            minutes = int(s[:-1])
            dt = now - pd.Timedelta(minutes=minutes)
            return dt.strftime("%Y-%m-%d")

        # horas
        if s.endswith("h") and s[:-1].isdigit():
            hours = int(s[:-1])
            dt = now - pd.Timedelta(hours=hours)
            return dt.strftime("%Y-%m-%d")

        # dias
        if s.endswith("d") and s[:-1].isdigit():
            days = int(s[:-1])
            dt = now - pd.Timedelta(days=days)
            return dt.strftime("%Y-%m-%d")

        # semanas
        if s.endswith("w") and s[:-1].isdigit():
            weeks = int(s[:-1])
            dt = now - pd.Timedelta(weeks=weeks)
            return dt.strftime("%Y-%m-%d")


        # datas
        try:
            # Se não tem ano, adiciona o ano atual
            if re.match(r"^[a-z]{3} \d{1,2}$", s):
                dt = pd.to_datetime(f"{s}, {now.year}")
                # Se a data resultante for no futuro, subtrai 1 ano
                if dt > now:
                    dt = dt - pd.DateOffset(years=1)
                return dt.strftime("%Y-%m-%d")
            else:
                dt = pd.to_datetime(s)
                return dt.strftime("%Y-%m-%d")
        except:
            print(f"[ERROR] Falha ao processar data de uma reviews na URL {url_rev} no Playright. Erro: {e}")
        
    def scrapUsrReviews(self, movie: Movie, url: str):
        url_rev = f"{url}/reviews/all-audience"

        try:
            with sync_playwright() as p:

                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    page.goto(url_rev, wait_until="domcontentloaded")
                    page.wait_for_selector("review-card", timeout=5000)

                    cards = page.locator("review-card")
                    count = cards.count()
                    for i in range(count):
                        try:
                            card = cards.nth(i)

                            # Texto do review
                            loc = card.locator("drawer-more >> [slot='review'], span[slot='content']")
                            if loc.count() > 0:
                                texto = loc.inner_text(timeout=2000).strip()
                            else:
                                texto = None
                           
                            # Nota
                            score_el = card.locator("rating-stars-group")
                            nota = None
                            if score_el.count() > 0:
                                score = score_el.get_attribute("score")
                                nota = float(score) * 2 if score else None
                           
                            # Data 
                            data_el = card.locator("span[slot='timestamp']")
                            date_raw = data_el.inner_text() if data_el.count() > 0 else None
                            date_formatted = self.parse_rotten_date(date_raw, url_rev)
                         
                            if (texto or nota):
                                review = Review()
                                review.set_text(texto)
                                review.set_rating(nota)
                                review.set_date(date_formatted)
                                movie.add_user_review(review)
                            
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar uma review na URL {url_rev} no Playright. Erro: {e}")
                except Exception as e:
                    print(f"[ERROR] Falha ao processar URL {url_rev} no Playright. Erro: {e}")
                finally:
                    browser.close()
        except Exception as e:
            print(f"[ERROR] Falha ao iniciar Playright ou navegador para URL {url_rev}. Erro: {e}")

    def scrapCritReviews(self, movie: Movie, url: str):
        url_rev = f"{url}/reviews/all-critics"

        try:
            with sync_playwright() as p:

                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    page.goto(url_rev, wait_until="domcontentloaded")
                    page.wait_for_selector("review-card", timeout=5000)

                    cards = page.locator("review-card")
                    count = cards.count()
                    for i in range(count):
                        try:
                            card = cards.nth(i)

                            # Texto do review
                            loc = card.locator("drawer-more >> [slot='review'], span[slot='content']")
                            if loc.count() > 0:
                                texto = loc.inner_text(timeout=2000).strip()
                            else:
                                texto = None
                            # Nota
                            rating_span = card.locator("span[slot='rating'] > span")
                            raw = rating_span.inner_text(timeout=1000).strip() if rating_span.count() > 0 else None
                            if raw:
                                # 1) IGNORAR notas em letra
                                if re.match(r"^[A-F][+-]?$", raw):
                                    nota = None

                                # 2) Frações (3/4, 9/10 etc.)
                                elif "/" in raw and re.match(r"^\d+(\.\d+)?/\d+(\.\d+)?$", raw):
                                    num, den = raw.split("/")
                                    num = float(num)
                                    den = float(den)
                                    if den == 0:
                                        nota = None
                                    nota = round((num / den) * 10, 2)

                                # 3) Número direto (0–10)
                                elif re.match(r"^\d+(\.\d+)?$", raw):
                                    value = float(raw)
                                    if value <= 10:
                                        nota = value
                                    else:
                                    # caso improvável (nota tipo 80/100 sem barra)
                                        nota = round((value / 100) * 10, 2)
                            else:
                                nota = None
                            # Data 
                            data_el = card.locator("span[slot='timestamp']")
                            date_raw = data_el.inner_text() if data_el.count() > 0 else None
                            date_formatted = self.parse_rotten_date(date_raw, url_rev)
                            if (texto or nota):
                                review = Review()
                                review.set_text(texto)
                                review.set_rating(nota)
                                review.set_date(date_formatted)
                                movie.add_critic_review(review)
                            
                        except Exception as e:
                            print(f"[ERROR] Falha ao processar uma review na URL {url_rev} no Playright. Erro: {e}")
                except Exception as e:
                    print(f"[ERROR] Falha ao processar URL {url_rev} no Playright. Erro: {e}")
                finally:
                    browser.close()
        except Exception as e:
            print(f"[ERROR] Falha ao iniciar Playright ou navegador para URL {url_rev}. Erro: {e}")

    def scrapNewMovies(self, site: BeautifulSoup, url_str: str):
        try:
            more_like_this = site.find("section", {"data-qa": "section:more-like-this"})
            if more_like_this:
                # Dentro dela, procura todos os <rt-link> que tenham o slot "primaryImage"
                for link_tag in more_like_this.select('rt-link[slot="primaryImage"]'):
                    href = link_tag.get("href")
                    if href and href.startswith("/m/"):  # garante que é link de filme
                        self.periodic_queue.put(URL("https://www.rottentomatoes.com" + href.strip(), URLType.ROTT))
        except Exception as e:
            print(f"[ERROR] Falha ao processar seção 'more like this' em {url_str}. Erro: {e}")

    # Pega o link do click.justwatch.com e tenta identificar a plataforma com base no domínio final (param 'r=' do redirect).
    def normalize_platform_from_url(self, link: str) -> str | None:
        # Lista de plataformas
        PLATFORM_MAP = {
            "primevideo": "Prime Video", "apple": "Apple TV", "netflix": "Netflix", "hbomax": "HBO Max",
            "disneyplus": "Disney Plus", "paramount": "Paramount+", "globoplay": "Globoplay",
            "youtubepremium": "YouTube Premium", "play.google": "Google Play"
        }

        if not link:
            return None

        try:
            # decodifica URL
            decoded = urllib.parse.unquote(link)

            # extrai o parâmetro 'r' do link (redirect do JustWatch)
            parsed = urllib.parse.urlparse(decoded)
            query = urllib.parse.parse_qs(parsed.query)
            redirect_url = query.get("r", [None])[0]

            if redirect_url is None:
                return None
            
            # extrai domínio do destino real
            dest = urllib.parse.urlparse(redirect_url)
            hostname = (dest.hostname or "").lower()
            # tenta descobrir plataforma pelo hostname
            for key, pretty_name in PLATFORM_MAP.items():
                if key in hostname:
                    return pretty_name

            return None  # plataforma não reconhecida
        except Exception as e:
            print(f"[ERROR] Falha ao normalizar a plataforma a partir do link {link}. Erro: {e}")
            return None
    
    def scrapDynamicData(self, url: URL, movie: Movie):
        try:
            options = Options()
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--headless")  # roda sem abrir janela
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            service = Service()
            service.startup_timeout = 10
            driver = webdriver.Chrome(service=service, options=options)
        except TimeoutException as e:
            print(f"[TIMEOUT] ChromeDriver excedeu o tempo limite ao inicializar. URL: {url.get_url()}. Erro: {e}")
            return
        except Exception as e:
            print(f"[ERROR] Falha ao iniciar ChromeDriver para URL {url.get_url()}. Pulando coleta de plataformas de streaming. Erro: {e}")
            return
        
        try:
            driver.get(url.get_url())
            time.sleep(3)
            try:
                iframe = driver.find_element(
                    By.XPATH, "//div[@data-wheretowatchmanager='jwContainer']//iframe[contains(@class, 'jw-widget-iframe')]"
                )
            except NoSuchElementException:
                print(f"[TIMEOUT] Iframe não encontrado em {url.get_url()}")
                iframe = None
    
        
            if iframe:
                # muda o contexto para dentro do iframe
                driver.switch_to.frame(iframe)
                time.sleep(3)
                try:
                    offers = driver.find_elements(By.XPATH, "//div[contains(@class,'jw-offer')]/a")
                except NoSuchElementException:
                    print(f"[ERROR] Nenhuma plataforma encontrada no iframe para: {url.get_url()}")
                    offers = []
                
                if offers:
                    plataform_names = []
                    for offer in offers:
                        link = offer.get_attribute("href")
                        plataform_name = self.normalize_platform_from_url(link)

                        if plataform_name and plataform_name not in plataform_names:
                            plataform_names.append(plataform_name)
                            plataform = Plataform(plataform_name, link)
                            movie.add_platform(plataform)

        except WebDriverException as e:
            print(f"[ERROR] Ocorreu um erro no WebDriver para a URL {url.get_url()}. Erro: {e}")
        except Exception as e:
            print(f"[ERROR] Falha ao coletar dados dinâmicos da URL {url.get_url()}. Erro: {e}")
        finally:
            # sai do iframe e encerra
            driver.quit()

    @override
    def scrap(self):
        url = self.periodic_queue.get()
        if (url.get_type() == URLType.END):
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
            if self.scrapJSONLD(site, movie) == 1:
                print(f"[ERROR] Nenhum título foi encontrado na URL: {url_str}. O scraping desta página será interrompido.")
                return
            
            self.scrapMovieInfo(site, movie)
            self.scrapCast(movie, url_str)
            self.scrapRevData(site, movie)
            self.scrapUsrReviews(movie, url_str)
            self.scrapCritReviews(movie, url_str)
            self.scrapDynamicData(url, movie)
            self.scrapNewMovies(site, url_str)
            self.count += 1
            print(f"[INFO] Concluída a coleta de dados da URL: {url_str}. Quantidade de filmes coletados do Rotten Tomatoes: {self.count}")

            self.storage.store_movie(movie, URLType.ROTT)