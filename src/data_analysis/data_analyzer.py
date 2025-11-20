from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict, Counter
from urllib.parse import urlparse
import numpy as np
import json

class DataAnalyzer:
    def __init__(self, movies_list: list[dict]):
        self.movies_list = movies_list["filmes"]
        plt.rcParams['figure.figsize'] = (10, 5)
        plt.style.use("seaborn-v0_8")
        plt.style.use("ggplot")

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

        for movie in self.movies_list:
            src = self.extract_source(movie.get("url", ""))
            movie["__source__"] = src
            sources.add(src)
            fields.update(movie.keys())

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

        data_matrix = [[counts[field][src] for field in fields] for src in sources]
        self.plot_grouped_bar(
            labels=fields,
            groups=sources,
            matrix=data_matrix,
            title="Disponibilidade de Campos",
            ylabel="Contagem de Filmes",
            save_path="graphs/disponibilidade_por_fonte.png"
        )

        field_types = []
        for movie in self.movies_list:
            for key, value in movie.items():
                field_types.append(type(value).__name__)

        type_counts = Counter(field_types)

        self.plot_pie_chart(
            labels=list(type_counts.keys()),
            values=list(type_counts.values()),
            title="Distribuição Geral de Tipos",
            save_path="graphs/tipos_geral.png"
        )

        size_metrics = ["reviews_usr", "sinopse"]
        metric_values = {metric: {src: [] for src in sources} for metric in size_metrics}

        for movie in self.movies_list:
            src = movie["__source__"]
            if "reviews_usr" in movie:
                review_values = []
                for review in movie["reviews_usr"]:
                    if review['texto'] and review.get("texto"):
                        review_values.append(len(review['texto']))
                metric_values["reviews_usr"][src].append(np.mean(review_values) if review_values else 0)
            if "sinopse" in movie and isinstance(movie["sinopse"], str):
                metric_values["sinopse"][src].append(len(movie["sinopse"]))

        avg_matrix = []
        for metric in size_metrics:
            avg_matrix.append([
                np.mean(metric_values[metric][src]) if metric_values[metric][src] else 0
                for src in sources
            ])

        self.plot_grouped_bar(
            labels=sources,
            groups=size_metrics,
            matrix=avg_matrix,
            title="Tamanho Médio das Entradas",
            ylabel="Tamanho Médio",
            save_path="graphs/tamanho_medio_entradas.png"
        )

    def run_quality_analysis(self):
        """
        Análise de qualidade dos dados
        """
        report_lines = []
        report_lines.append("="*50)
        report_lines.append("ANÁLISE DE QUALIDADE DOS DADOS")
        report_lines.append("="*50)
        report_lines.append("")
        
        total_movies = len(self.movies_list)
        
        # 3.1 Valores inconsistentes
        report_lines.append("3.1 VALORES INCONSISTENTES")
        report_lines.append("-" * 50)
        
        inconsistent_data = {
            "duracao_invalida": 0,
            "media_crit_fora_range": 0,
            "media_usr_fora_range": 0,
            "data_futura": 0,
            "data_muito_antiga": 0
        }
        
        for movie in self.movies_list:
            # Verificar duração (deve ser positiva e razoável)
            if "duracao" in movie and isinstance(movie["duracao"], str):
                try:
                    time_parts = movie["duracao"].split(":")
                    if len(time_parts) == 3:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        total_minutes = hours * 60 + minutes
                        # Filmes geralmente têm entre 1 min e 500 min
                        if total_minutes <= 0 or total_minutes > 500:
                            inconsistent_data["duracao_invalida"] += 1
                except:
                    inconsistent_data["duracao_invalida"] += 1
            
            # Verificar média crítica (geralmente 0-10 ou 0-100)
            if "media_crit" in movie and isinstance(movie["media_crit"], str):
                try:
                    media = float(movie["media_crit"].strip("<>"))
                    if media < 0 or media > 100:
                        inconsistent_data["media_crit_fora_range"] += 1
                except:
                    pass
            
            # Verificar média usuário (geralmente 0-10 ou 0-100)
            if "media_usr" in movie and isinstance(movie["media_usr"], str):
                try:
                    media = float(movie["media_usr"].strip("<>"))
                    if media < 0 or media > 100:
                        inconsistent_data["media_usr_fora_range"] += 1
                except:
                    pass
            
            # Verificar datas inconsistentes
            if "data de lançamento nos cinemas" in movie:
                try:
                    dt = datetime.strptime(movie["data de lançamento nos cinemas"], "%Y-%m-%d")
                    current_year = datetime.now().year
                    if dt.year > current_year:
                        inconsistent_data["data_futura"] += 1
                    elif dt.year < 1888:  # Primeiro filme foi em 1888
                        inconsistent_data["data_muito_antiga"] += 1
                except:
                    pass
        
        for key, value in inconsistent_data.items():
            report_lines.append(f"{key}: {value} ({value/total_movies*100:.2f}%)")
        
        # 3.2 Outliers
        report_lines.append("")
        report_lines.append("3.2 OUTLIERS")
        report_lines.append("-" * 50)
        
        # Campos numéricos para análise de outliers
        numeric_fields = {
            "duracao": [],
            "media_crit": [],
            "media_usr": []
        }
        
        for movie in self.movies_list:
            # Duração
            if "duracao" in movie and isinstance(movie["duracao"], str):
                try:
                    time_parts = movie["duracao"].split(":")
                    if len(time_parts) == 3:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        total_minutes = hours * 60 + minutes
                        numeric_fields["duracao"].append(total_minutes)
                except:
                    pass
            
            # Média crítica
            if "media_crit" in movie and isinstance(movie["media_crit"], str):
                try:
                    media = float(movie["media_crit"].strip("<>"))
                    numeric_fields["media_crit"].append(media)
                except:
                    pass
            
            # Média usuário
            if "media_usr" in movie and isinstance(movie["media_usr"], str):
                try:
                    media = float(movie["media_usr"].strip("<>"))
                    numeric_fields["media_usr"].append(media)
                except:
                    pass
        
        outliers_data = {}
        
        for field, values in numeric_fields.items():
            if not values:
                continue
            
            values_arr = np.array(values)
            
            # Método IQR (Interquartile Range)
            q1 = np.percentile(values_arr, 25)
            q3 = np.percentile(values_arr, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = values_arr[(values_arr < lower_bound) | (values_arr > upper_bound)]
            outliers_count = len(outliers)
            outliers_percent = (outliers_count / len(values_arr)) * 100
            
            outliers_data[field] = {
                "count": outliers_count,
                "percent": outliers_percent,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound
            }
            
            report_lines.append(f"\n{field}:")
            report_lines.append(f"  Total de valores: {len(values_arr)}")
            report_lines.append(f"  Outliers detectados: {outliers_count} ({outliers_percent:.2f}%)")
            report_lines.append(f"  Limite inferior: {lower_bound:.2f}")
            report_lines.append(f"  Limite superior: {upper_bound:.2f}")
        
        # Visualizar outliers
        outlier_labels = list(outliers_data.keys())
        outlier_counts = [outliers_data[k]["count"] for k in outlier_labels]
        
        if outlier_labels:
            self.plot_bar_simple(
                labels=outlier_labels,
                values=outlier_counts,
                title="Quantidade de Outliers por Campo",
                xlabel="Quantidade",
                save_path="graphs/outliers_por_campo.png"
            )
        
        # 3.3 Dados completos ou faltantes
        report_lines.append("")
        report_lines.append("3.3 DADOS FALTANTES")
        report_lines.append("-" * 50)
        
        # Campos importantes para verificar
        important_fields = [
            "titulo",
            "duracao",
            "generos",
            "data de lançamento nos cinemas",
            "media_usr",
            "cast",
            "classificacao"
        ]
        
        missing_data = {}
        
        for field in important_fields:
            missing_count = 0
            for movie in self.movies_list:
                if field not in movie or movie[field] is None or movie[field] == "" or movie[field] == []:
                    missing_count += 1
            
            missing_percent = (missing_count / total_movies) * 100
            missing_data[field] = {
                "count": missing_count,
                "percent": missing_percent
            }
            
            report_lines.append(f"{field}: {missing_count} faltantes ({missing_percent:.2f}%)")
        
        # Visualizar dados faltantes
        missing_labels = list(missing_data.keys())
        missing_percents = [missing_data[k]["percent"] for k in missing_labels]
        
        self.plot_bar_simple(
            labels=missing_labels,
            values=missing_percents,
            title="Percentual de Dados Faltantes por Campo",
            xlabel="Percentual (%)",
            save_path="graphs/dados_faltantes.png"
        )
        
        # 3.4 Duplicadas ou dados repetidos
        report_lines.append("")
        report_lines.append("3.4 DUPLICATAS")
        report_lines.append("-" * 50)
        
        # Verificar duplicatas por título
        titles = [movie.get("titulo", "") for movie in self.movies_list if movie.get("titulo")]
        title_counts = Counter(titles)
        duplicated_titles = {title: count for title, count in title_counts.items() if count > 1}
        
        report_lines.append(f"Total de títulos únicos: {len(title_counts)}")
        report_lines.append(f"Títulos duplicados: {len(duplicated_titles)}")
        
        if duplicated_titles:
            report_lines.append("\nTítulos com duplicatas:")
            for title, count in sorted(duplicated_titles.items(), key=lambda x: x[1], reverse=True)[:10]:
                report_lines.append(f"  '{title}': {count} ocorrências")
        
        # Verificar registros completamente idênticos
        import json
        movie_hashes = []
        for movie in self.movies_list:
            # Criar hash do filme (excluindo campos que podem variar)
            movie_str = json.dumps(movie, sort_keys=True, default=str)
            movie_hashes.append(movie_str)
        
        hash_counts = Counter(movie_hashes)
        exact_duplicates = sum(1 for count in hash_counts.values() if count > 1)
        
        report_lines.append(f"\nRegistros completamente idênticos: {exact_duplicates}")
        
        # Resumo geral de qualidade
        report_lines.append("")
        report_lines.append("="*50)
        report_lines.append("RESUMO DE QUALIDADE")
        report_lines.append("="*50)
        
        completeness_score = 100 - np.mean(missing_percents)
        consistency_score = 100 - (sum(inconsistent_data.values()) / total_movies * 100)
        duplicate_score = 100 - (len(duplicated_titles) / len(title_counts) * 100) if title_counts else 0
        
        report_lines.append(f"Score de Completude: {completeness_score:.2f}%")
        report_lines.append(f"Score de Consistência: {consistency_score:.2f}%")
        report_lines.append(f"Score de Unicidade: {duplicate_score:.2f}%")
        report_lines.append(f"Score Geral de Qualidade: {(completeness_score + consistency_score + duplicate_score) / 3:.2f}%")
        
        # Visualizar scores
        score_labels = ["Completude", "Consistência", "Unicidade", "Geral"]
        score_values = [
            completeness_score,
            consistency_score,
            duplicate_score,
            (completeness_score + consistency_score + duplicate_score) / 3
        ]
        
        self.plot_bar_simple(
            labels=score_labels,
            values=score_values,
            title="Scores de Qualidade dos Dados",
            xlabel="Score (%)",
            save_path="graphs/quality_scores.png"
        )
        
        # Salvar relatório em arquivo
        with open("quality_analysis_report.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

    def run_descriptive_analysis(self):
        # 2.1 Valores mais comuns (top gêneros, top atores???)
        genres = []
        actors = []

        for movie in self.movies_list:
            if movie["generos"]:
                g = movie["generos"]
                if isinstance(g, list):
                    genres.extend(g)
                elif isinstance(g, str) and g.strip():
                    genres.append(g)

            if movie["cast"] and isinstance(movie["cast"], list):
                for actor in movie["cast"]:
                    if isinstance(actor, str) and actor.strip():
                        actors.append(actor)

        genre_counts = Counter(genres)
        actor_counts = Counter(actors)

        top_genres = genre_counts.most_common(5)
        top_actors = actor_counts.most_common(5)

        self.plot_bar_simple(
            labels=[g for g, _ in top_genres],
            values=[c for _, c in top_genres],
            title="Top 10 Gêneros Mais Comuns",
            xlabel="Contagem",
            save_path="graphs/top_generos.png"
        )

        self.plot_bar_simple(
            labels=[a for a, _ in top_actors],
            values=[c for _, c in top_actors],
            title="Top 10 Atores Mais Frequentes",
            xlabel="Contagem",
            save_path="graphs/top_atores.png"
        )

        # 2.2 Média, mediana, moda, desvio padrão, mínimo e máximo
        # Avaliaçao geral ou por filme..? 
        # Campos: duração, data de lançamento nos cinemas, media_crit, media_usr
        fields = {
            "duration": [],
            "media_crit": [],
            "media_usr": [],
            "data de lançamento nos cinemas": []
        }

        for movie in self.movies_list:

            if "duracao" in movie and isinstance(movie["duracao"], (int, float)):
                fields["duracao"].append(movie["duracao"])

            if "media_crit" in movie and isinstance(movie["media_crit"], (int, float)):
                fields["media_crit"].append(movie["media_crit"])

            if "media_usr" in movie and isinstance(movie["media_usr"], (int, float)):
                fields["media_usr"].append(movie["media_usr"])

            if "data de lançamento nos cinemas" in movie:
                try:
                    dt = datetime.strptime(movie["data de lançamento nos cinemas"], "%Y-%m-%d")
                    fields["data de lançamento nos cinemas"].append(dt.timestamp())
                except ValueError as e:
                    print(e)

        for field, values in fields.items():

            if not values:
                continue

            values_arr = np.array(values)

            mean_val = float(np.mean(values_arr))
            median_val = float(np.median(values_arr))

            try:
                mode_val = float(Counter(values).most_common(1)[0][0])
            except:
                mode_val = 0

            std_val = float(np.std(values_arr))
            min_val = float(np.min(values_arr))
            max_val = float(np.max(values_arr))

            stats_labels = ["Média", "Mediana", "Moda", "Desvio Padrão", "Mínimo", "Máximo"]
            stats_values = [mean_val, median_val, mode_val, std_val, min_val, max_val]

            self.plot_bar_simple(
                labels=stats_labels,
                values=stats_values,
                title=f"Estatísticas de {field}",
                xlabel="Valor",
                save_path=f"graphs/stats_{field}.png"
            )

        # 2.3 Distribuição dde classes
        # Campos: genero, classificacao indicativa
        # Distribuição de gêneros
        if genres:
            self.plot_pie_chart(
                labels=[g for g, _ in genre_counts.most_common(10)],
                values=[c for _, c in genre_counts.most_common(10)],
                title="Distribuição dos 10 Principais Gêneros",
                save_path="graphs/distribuicao_generos.png"
            )

        # Distribuição de classificação indicativa
        classificacoes = []
        for movie in self.movies_list:
            if "classificacao indicativa" in movie and movie["classificacao indicativa"]:
                classificacoes.append(movie["classificacao indicativa"])
        
        if classificacoes:
            classificacao_counts = Counter(classificacoes)
            self.plot_pie_chart(
                labels=[c for c, _ in classificacao_counts.most_common()],
                values=[count for _, count in classificacao_counts.most_common()],
                title="Distribuição de Classificação Indicativa",
                save_path="graphs/distribuicao_classificacao.png"
            )

        # 2.4  Correlação entre atributos
        # Correalação da avaliação (media_crit, media_usr) e a data de lançamento e duração

        correlation_data = {
            "duracao": [],
            "media_crit": [],
            "media_usr": [],
            "data de lançamento nos cinemas": []
        }

        for movie in self.movies_list:
            # Só incluir filmes que tenham todos os dados necessários
            temp_data = {}
            all_data = True

            if "duracao" in movie and isinstance(movie["duracao"], str):
                time_parts = movie["duracao"].split(":")
                if len(time_parts) == 3:
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(time_parts[2])
                    # Converter para minutos totais
                    total_minutes = hours * 60 + minutes + seconds / 60
                    temp_data["duracao"] = total_minutes
            else:
                all_data = False

            if "media_crit" in movie and isinstance(movie["media_crit"], (int, float)):
                temp_data["media_crit"] = float(movie["media_crit"])
            else:
                all_data = False

            if "media_usr" in movie and isinstance(movie["media_usr"], (int, float)):
                temp_data["media_usr"] = float(movie["media_usr"])
            else:
                all_data = False

            if "data de lançamento nos cinemas" in movie:
                dt = datetime.strptime(movie["data de lançamento nos cinemas"], "%Y-%m-%d")
                temp_data["data de lançamento nos cinemas"] = dt.year
            else:
                all_data = False

            if all_data:
                for key, value in temp_data.items():
                    correlation_data[key].append(value)

        # Criar matriz de correlação
        if all(len(v) > 1 for v in correlation_data.values()):
            df_corr = pd.DataFrame(correlation_data)
            correlation_matrix = df_corr.corr()

            self.plot_heatmap(
                data=correlation_matrix.values,
                xlabels=correlation_matrix.columns.tolist(),
                ylabels=correlation_matrix.index.tolist(),
                title="Matriz de Correlação entre Atributos",
                save_path="graphs/correlacao_atributos.png"
            )

            # Gráficos de dispersão específicos
            # Media crítica vs duração
            self.plot_scatter(
                x=correlation_data["duracao"],
                y=correlation_data["media_crit"],
                title="Correlação: Duração vs Média Crítica",
                xlabel="Duração (min)",
                ylabel="Média Crítica",
                save_path="graphs/scatter_duracao_media_crit.png"
            )

            # Media usuário vs duração
            self.plot_scatter(
                x=correlation_data["duracao"],
                y=correlation_data["media_usr"],
                title="Correlação: Duração vs Média Usuário",
                xlabel="Duração (min)",
                ylabel="Média Usuário",
                save_path="graphs/scatter_duracao_media_usr.png"
            )

            # Media crítica vs ano de lançamento
            self.plot_scatter(
                x=correlation_data["data de lançamento nos cinemas"],
                y=correlation_data["media_crit"],
                title="Correlação: Ano de Lançamento vs Média Crítica",
                xlabel="Ano de Lançamento",
                ylabel="Média Crítica",
                save_path="graphs/scatter_ano_media_crit.png"
            )

            # Media usuário vs ano de lançamento
            self.plot_scatter(
                x=correlation_data["data de lançamento nos cinemas"],
                y=correlation_data["media_usr"],
                title="Correlação: Ano de Lançamento vs Média Usuário",
                xlabel="Ano de Lançamento",
                ylabel="Média Usuário",
                save_path="graphs/scatter_ano_media_usr.png"
            )


    def plot_bar_simple(self, labels, values, title, xlabel, save_path):
        plt.figure(figsize=(10, 6))
        y = np.arange(len(labels))

        plt.barh(y, values)
        plt.yticks(y, labels)
        plt.xlabel(xlabel)
        plt.title(title)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()


    def plot_pie_chart(self, labels, values, title, save_path):
        plt.figure(figsize=(8, 8))
        plt.pie(values, labels=labels, autopct='%1.1f%%')
        plt.title(title)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()


    def plot_grouped_bar(self, labels, groups, matrix, title, ylabel, save_path):
        x = np.arange(len(labels))
        width = 0.8 / len(groups)

        plt.figure(figsize=(14, 6))
        for i, group in enumerate(groups):
            plt.bar(
                x + i * width,
                matrix[i],
                width=width,
                label=group
            )

        plt.xticks(x + width * len(groups) / 2, labels, rotation=45, ha="right")
        plt.ylabel(ylabel)
        plt.title(title)
        plt.legend()
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()

    def plot_scatter(self, x, y, title, xlabel, ylabel, save_path):
        plt.figure(figsize=(10, 6))
        plt.scatter(x, y, alpha=0.5, edgecolors='k', linewidth=0.5)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.xlabel(xlabel, fontsize=12)
        plt.ylabel(ylabel, fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()


    def plot_heatmap(self, data, xlabels, ylabels, title, save_path):

        plt.figure(figsize=(10, 8))
        im = plt.imshow(data, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
        
        # Configurar os ticks e labels
        plt.xticks(range(len(xlabels)), xlabels, rotation=45, ha='right')
        plt.yticks(range(len(ylabels)), ylabels)
        
        # Adicionar barra de cores
        cbar = plt.colorbar(im)
        cbar.set_label('Correlação', rotation=270, labelpad=20)
        
        # Adicionar os valores numéricos em cada célula
        for i in range(len(ylabels)):
            for j in range(len(xlabels)):
                text = plt.text(j, i, f'{data[i, j]:.2f}',
                            ha="center", va="center", color="black", fontsize=10)
        
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()


    def run_all(self):
        self.run_structure_anaysis()
        self.run_descriptive_analysis()
        self.run_quality_analysis()

if __name__ == "__main__":
    with open("filmes.json", "r", encoding="utf-8") as file:
        movies_data = json.load(file)

    analyzer = DataAnalyzer(movies_data)
    analyzer.run_all()