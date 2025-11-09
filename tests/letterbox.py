from src.data_structures.periodic_queue import PeriodicQueue
from src.storage import Storage
from src.scrapers.lettr_scraper import LettrScraper
from src.data_structures.url import URL, URLType
import logging


if __name__ == "__main__":
    lettr_url_queue = PeriodicQueue(0)
    lettr_url_queue.put(URL("https://letterboxd.com/film/the-matrix/", URLType.LTTR))
    lettr_scraper = LettrScraper(lettr_url_queue, Storage())
    lettr_scraper.scrap()
