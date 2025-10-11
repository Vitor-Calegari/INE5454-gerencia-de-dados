from abc import ABC, abstractmethod
from src.data_structures.periodic_queue import PeriodicQueue
from src.storage import Storage

class Scraper(ABC):
    
    def __init__(self, periodic_queue: PeriodicQueue, storage: Storage) -> None:
        self.periodic_queue = periodic_queue
        self.storage = storage
        self.running = True
    
    def stop(self) -> None:
        self.periodic_queue.put("ScraperEnded!")
        self.runnning = False
    
    def run(self) -> None:
        while self.running:
            self.scrap()

    @abstractmethod
    def scrap(self):
        """ Implemente aqui o que deve ser executado no loop do scraper """
        pass