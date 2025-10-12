from src.scrapers.scraper import Scraper
from typing import override
from src.storage import Storage


class LettrScraper(Scraper):
    
    def __init__(self, periodic_queue, storage: Storage):
        super().__init__(periodic_queue, storage)
    
    @override
    def scrap(self):
        print("Implemente o Scraper para o Letterboxd")
