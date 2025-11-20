import matplotlib.pyplot as plt
from collections import defaultdict, Counter
from urllib.parse import urlparse
import numpy as np
import json

class DataAnalyzer:
    def __init__(self, movies_list: list[dict]):
        self.movies_list = movies_list["filmes"]
        plt.rcParams['figure.figsize'] = (10, 5)

    def extract_source(self, url):
        try:
            domain = urlparse(url).netloc
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except:
            return "desconhecida"


    def run_structure_anaysis(self):
        sources = set()
        fields = set()

        sources = set()
        fields = set()

        # 1.1, 1.3 Disponibilidade dos campos (checa onde os campos não são nulos)

        for movie in self.movies_list:
            src = self.extract_source(movie.get("url", ""))
            movie["__source__"] = src   # salvar temporariamente
            sources.add(src)
            fields.update(movie.keys())

        # remover campos internos
        fields.discard("__source__")
        fields.discard("url")

        sources = sorted(list(sources))
        fields = sorted(list(fields))

        counts = defaultdict(lambda: {src: 0 for src in sources})

        for movie in self.movies_list:
            src = movie["__source__"]
            for field in fields:
                if field in movie and movie[field] not in ("", None):
                    counts[field][src] += 1

        x = np.arange(len(fields))
        width = 0.8 / len(sources) 

        plt.figure(figsize=(14, 6))

        # Cada fonte vira um conjunto de barras
        for i, src in enumerate(sources):
            plt.bar(
                x + i * width, 
                [counts[field][src] for field in fields],
                width=width,
                label=src
            )

        plt.xticks(x + width * len(sources) / 2, fields, rotation=45, ha="right")
        plt.ylabel("Contagem de Filmes")
        plt.title("Disponibilidade de Campos")
        plt.legend(title="Fontes")
        plt.tight_layout()
        plt.savefig("graphs/disponibilidade_por_fonte.png", dpi=300, bbox_inches="tight")

        field_types = defaultdict(list)

        for movie in self.movies_list:
            for key, value in movie.items():
                field_types[key].append(type(value).__name__)

        for field, types in field_types.items():
            type_counts = Counter(types)
            print(f"{field}: {dict(type_counts)}")


    def run_descripteve_analysis(self):
        pass

    def run_quality_analysis(self):
        pass

    def run_all(self):
        self.run_structure_anaysis()
        self.run_descripteve_analysis()

if __name__ == "__main__":
    with open("filmes.json", "r", encoding="utf-8") as file:
        movies_data = json.load(file)

    analyzer = DataAnalyzer(movies_data)
    analyzer.run_structure_anaysis()