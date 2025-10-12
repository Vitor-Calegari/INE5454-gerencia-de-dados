from abc import ABC, abstractmethod
from src.data_structures.periodic_queue import PeriodicQueue
from src.data_structures.url import URL, URLType
from src.storage import Storage
from threading import Lock

class Scraper(ABC):
    
    def __init__(self, periodic_queue: PeriodicQueue, storage: Storage) -> None:
        self.periodic_queue = periodic_queue
        self.storage = storage
        self.running = True
        self._lock = Lock()
    
    def stop(self) -> None:
        with self._lock:
            self.running = False
        self.periodic_queue.put(URL("ScraperEnded!", URLType.END))
    
    def run(self) -> None:
        while True:
            with self._lock:
                if not self.running:
                    break
            self.scrap()

    @abstractmethod
    def scrap(self):
        """ Implemente aqui o que deve ser executado no loop do scraper """
        pass