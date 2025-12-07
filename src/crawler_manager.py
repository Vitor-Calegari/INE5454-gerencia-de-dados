import threading

from src.data_structures.periodic_queue import PeriodicQueue
from src.storage import Storage
from src.scrapers.imdb_scraper import IMDBScraper
from src.scrapers.lettr_scraper import LettrScraper
from src.scrapers.rott_scraper import RottScraper
from src.observers import Observer
from typing import override
from src.data_structures.url import URL, URLType

from src.data_structures.url import URL, URLType


class CrawlerManager(Observer):

    def __init__(self) -> None:
        super().__init__()
        self.imdb_url_queue = PeriodicQueue(0)
        self.lettr_url_queue = PeriodicQueue(0)
        self.rott_url_queue = PeriodicQueue(0)
        self.imdb_url_queue.put(URL("https://www.imdb.com/title/tt0133093/", URLType.IMDB))
        self.lettr_url_queue.put(URL("https://letterboxd.com/film/the-matrix/", URLType.LTTR))
        self.rott_url_queue.put( URL("https://www.rottentomatoes.com/m/matrix", URLType.ROTT))
        self.storage = Storage()
        self.storage.attach(self)
        self.mutex = threading.Lock()
        self.mutex.acquire()

    @override
    def update(self) -> None:
        if self.mutex.locked():
            self.mutex.release()

    def run(self):
        # Creates all scrapers
        imdb_scraper = IMDBScraper(self.imdb_url_queue, self.storage)
        lettr_scraper = LettrScraper(self.lettr_url_queue, self.storage)
        rott_scraper = RottScraper(self.rott_url_queue, self.storage)

        self.storage.enroll_new_scraper(URLType.IMDB)
        self.storage.enroll_new_scraper(URLType.LTTR)
        self.storage.enroll_new_scraper(URLType.ROTT)

        # Creates a thread for each scraper
        imdb_thread = threading.Thread(target=imdb_scraper.run)
        lettr_thread = threading.Thread(target=lettr_scraper.run)
        rott_thread = threading.Thread(target=rott_scraper.run)

        # Start all threads
        imdb_thread.start()
        lettr_thread.start()
        rott_thread.start()

        # Wait for storage notification
        self.mutex.acquire()

        # Request scrapers to stop
        imdb_scraper.stop()
        lettr_scraper.stop()
        rott_scraper.stop()

        # Espera a thread for each scraper
        imdb_thread.join()
        lettr_thread.join()
        rott_thread.join()
        
        imdb_scraper.print_metrics()
        lettr_scraper.print_metrics()
        rott_scraper.print_metrics()
        
        self.storage.dump_to_json()
