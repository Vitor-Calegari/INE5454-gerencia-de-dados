import time
from abc import ABC, abstractmethod
from threading import Lock
from src.data_structures.periodic_queue import PeriodicQueue
from src.data_structures.url import URL, URLType
from src.storage import Storage


class Scraper(ABC):
    
    def __init__(self, periodic_queue: PeriodicQueue, storage: Storage) -> None:
        self.periodic_queue = periodic_queue
        self.storage = storage
        self.running = True
        self._lock = Lock()

        # Métricas
        self.name = ""
        self._scrap_times = []
        self._start_time = None
        self._end_time = None
        self._phase_times = {}
        self._new_urls_count = 0
        self._errors = 0
    
    def stop(self) -> None:
        with self._lock:
            self.running = False
        self.periodic_queue.put(URL("ScraperEnded!", URLType.END))
    
    def run(self) -> None:
        # Marca o início do crawler
        self._start_time = time.perf_counter()

        while True:
            with self._lock:
                if not self.running:
                    break
            
            # mede tempo por filme
            start = time.perf_counter()
            resposta = self.scrap()
            if resposta == 0:
                end = time.perf_counter()
                elapsed = end - start

                # salva o tempo do filme atual
                with self._lock:
                    self._scrap_times.append(elapsed)

        # fim do crawler
        self._end_time = time.perf_counter()

    def get_total_runtime(self) -> float:
        """Retorna o tempo total de execução do crawler."""
        if self._start_time is None:
            return 0.0
        if self._end_time is None:
            return time.perf_counter() - self._start_time
        return self._end_time - self._start_time

    def get_scrap_times(self):
        """Retorna o vetor com o tempo gasto em cada filme."""
        with self._lock:
            return list(self._scrap_times)

    def get_average_scrap_time(self) -> float:
        """Retorna a média dos tempos por filme."""
        with self._lock:
            if not self._scrap_times:
                return 0.0
            return sum(self._scrap_times) / len(self._scrap_times)
    
    def end_phase(self, name, t0):
        dt = time.time() - t0
        self._phase_times.setdefault(name, []).append(dt)
    
    def print_metrics(self) -> None:
        """Imprime métricas gerais sobre o crawler."""
        with self._lock:
            scrap_times = list(self._scrap_times)

        total_runtime = self.get_total_runtime()
        total_movies = len(scrap_times)
        avg = self.get_average_scrap_time() if total_movies > 0 else 0.0
        
        new_urls = self._new_urls_count
        errors = self._errors
        phase_times = {k: list(v) for k, v in self._phase_times.items()}

        print(f"\n========== MÉTRICAS DO {self.name} ==========")
        if total_movies > 0:
            print(f"Tempo total executado: {total_runtime:.4f} s")
            print(f"Número de filmes obtidos: {total_movies}")
            print(f"Tempo médio/filme:        {avg:.4f} s")
            print(f"Tempo mínimo:             {min(scrap_times):.4f} s")
            print(f"Tempo máximo:             {max(scrap_times):.4f} s")
            print(f"URLs coletadas:           {new_urls}")
            print(f"Erros durante scraping:   {errors}")
            print("\n--- Tempo médio por etapa ---")
            for phase, times in phase_times.items():
                print(f"{phase:40s} {sum(times)/len(times):.4f} s (amostras={len(times)})")
        else:
            print(f"Nenhum filme coletado.")    
        print("==========================================\n")

    @abstractmethod
    def scrap(self):
        """Implementação do scraping."""
        pass