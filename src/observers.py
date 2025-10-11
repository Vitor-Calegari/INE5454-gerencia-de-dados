from abc import ABC, abstractmethod
from typing import List

class Observer(ABC):
    """Abstract Observer class"""
    @abstractmethod
    def update(self) -> None:
        pass

class Observed(ABC):
    """Abstract Observed class"""
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        """Attach an observer to the Observed"""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """Detach an observer from the Observed"""
        self._observers.remove(observer)

    def notify(self) -> None:
        """Notify all observers about state change"""
        for observer in self._observers:
            observer.update()
