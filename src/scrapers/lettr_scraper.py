from src.scrapers.scraper import Scraper
from typing import override


class LettrScraper(Scraper):
    
    def __init__(self, periodic_queue, storage):
        super().__init__(periodic_queue, storage)
    
    @override
    def scrap(self):
        print("Implemente o Scraper para o Letterboxd")
