from src.scrapers.scraper import Scraper
from typing import override


class IMDBScraper(Scraper):
    
    def __init__(self, periodic_queue):
        super().__init__(periodic_queue)
    
    @override
    def scrap(self):
        print("Implemente o Scraper para o IMDB")
