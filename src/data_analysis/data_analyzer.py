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

        size_metrics = ["reviews de usuários", "sinopse"]
        metric_values = {metric: {src: [] for src in sources} for metric in size_metrics}

        for movie in self.movies_list:
            src = movie["__source__"]
            if "reviews de usuários" in movie:
                review_values = []
                for review in movie["reviews de usuários"]:
                    if review['texto'] and review.get("texto"):
                        review_values.append(len(review['texto']))
                metric_values["reviews de usuários"][src].append(np.mean(review_values) if review_values else 0)
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

    def run_quality_analysis(self, movies):
        """
        Analisa a qualidade dos dados de filmes com foco em:
        - Valores inconsistentes
        - Outliers
        - Completude
        - Duplicadas
        """
        
        print("=" * 60)
        print("ANÁLISE DE QUALIDADE DOS DADOS DE FILMES")
        print("=" * 60)
        
        # Preparar figura com subplots
        fig = plt.figure(figsize=(16, 12))
        
        # 1. ANÁLISE DE COMPLETUDE
        print("\n1. ANÁLISE DE COMPLETUDE")
        print("-" * 60)
        
        campos = [
            'titulo', 'generos', 'data de lançamento', 'sinopse', 
            'duracao', 'diretor', 'elenco', 'nota média dos criticos',
            'nota média dos usuários', 'reviews de críticos', 'reviews de usuários'
        ]
        
        completude = {}
        for campo in campos:
            count = 0
            for movie in movies:
                valor = movie.get(campo)
                if valor is not None and valor != [] and valor != "":
                    count += 1
            completude[campo] = (count / len(movies)) * 100
            print(f"{campo:30s}: {completude[campo]:5.1f}%")
        
        # Gráfico de Completude
        ax1 = plt.subplot(3, 3, 1)
        campos_curtos = [c[:15] + '...' if len(c) > 15 else c for c in campos]
        colors = ['#2ecc71' if v >= 90 else '#f39c12' if v >= 70 else '#e74c3c' 
                for v in completude.values()]
        bars = ax1.barh(campos_curtos, list(completude.values()), color=colors)
        ax1.set_xlabel('Completude (%)')
        ax1.set_title('Completude dos Campos', fontweight='bold')
        ax1.set_xlim(0, 100)
        ax1.axvline(90, color='green', linestyle='--', alpha=0.3, label='90%')
        ax1.axvline(70, color='orange', linestyle='--', alpha=0.3, label='70%')
        
        # 2. ANÁLISE DE VALORES INCONSISTENTES
        print("\n2. ANÁLISE DE VALORES INCONSISTENTES")
        print("-" * 60)
        
        # Analisar notas (devem estar entre 0 e 10)
        notas_criticos_invalidas = 0
        notas_usuarios_invalidas = 0
        
        for movie in movies:
            # Nota dos críticos
            nota_c = movie.get('nota média dos criticos')
            if nota_c is not None and (nota_c < 0 or nota_c > 10):
                notas_criticos_invalidas += 1
            
            # Nota dos usuários
            nota_u = movie.get('nota média dos usuários')
            if nota_u is not None and (nota_u < 0 or nota_u > 10):
                notas_usuarios_invalidas += 1
        
        print(f"Notas de críticos inválidas (fora de 0-10): {notas_criticos_invalidas}")
        print(f"Notas de usuários inválidas (fora de 0-10): {notas_usuarios_invalidas}")
        
        # Analisar datas de lançamento
        datas_invalidas = 0
        anos = []
        for movie in movies:
            data = movie.get('data de lançamento')
            if data:
                try:
                    dt = datetime.strptime(data, '%Y-%m-%d')
                    ano = dt.year
                    if ano < 1888 or ano > datetime.now().year:  # Cinema começou em 1888
                        datas_invalidas += 1
                    else:
                        anos.append(ano)
                except:
                    datas_invalidas += 1
        
        print(f"Datas de lançamento inválidas: {datas_invalidas}")
        
        # Gráfico de Inconsistências
        ax2 = plt.subplot(3, 3, 2)
        inconsistencias = {
            'Notas\nCríticos': notas_criticos_invalidas,
            'Notas\nUsuários': notas_usuarios_invalidas,
            'Datas': datas_invalidas
        }
        ax2.bar(inconsistencias.keys(), inconsistencias.values(), color='#e74c3c')
        ax2.set_ylabel('Quantidade')
        ax2.set_title('Valores Inconsistentes', fontweight='bold')
        ax2.set_ylim(0, max(inconsistencias.values()) * 1.2 if max(inconsistencias.values()) > 0 else 1)
        
        # 3. ANÁLISE DE OUTLIERS - NOTAS
        print("\n3. ANÁLISE DE OUTLIERS - NOTAS")
        print("-" * 60)
        
        notas_criticos = [m.get('nota média dos criticos') for m in movies 
                        if m.get('nota média dos criticos') is not None]
        notas_usuarios = [m.get('nota média dos usuários') for m in movies 
                        if m.get('nota média dos usuários') is not None]
        
        if notas_criticos:
            q1_c = np.percentile(notas_criticos, 25)
            q3_c = np.percentile(notas_criticos, 75)
            iqr_c = q3_c - q1_c
            outliers_c = [n for n in notas_criticos if n < q1_c - 1.5*iqr_c or n > q3_c + 1.5*iqr_c]
            print(f"Outliers em notas de críticos: {len(outliers_c)} ({len(outliers_c)/len(notas_criticos)*100:.1f}%)")
        
        if notas_usuarios:
            q1_u = np.percentile(notas_usuarios, 25)
            q3_u = np.percentile(notas_usuarios, 75)
            iqr_u = q3_u - q1_u
            outliers_u = [n for n in notas_usuarios if n < q1_u - 1.5*iqr_u or n > q3_u + 1.5*iqr_u]
            print(f"Outliers em notas de usuários: {len(outliers_u)} ({len(outliers_u)/len(notas_usuarios)*100:.1f}%)")
        
        # Boxplot de Notas
        ax3 = plt.subplot(3, 3, 3)
        data_box = [notas_criticos, notas_usuarios]
        bp = ax3.boxplot(data_box, tick_labels=['Críticos', 'Usuários'], patch_artist=True)
        for patch, color in zip(bp['boxes'], ['#3498db', '#9b59b6']):
            patch.set_facecolor(color)
        ax3.set_ylabel('Nota (0-10)')
        ax3.set_title('Distribuição de Notas (Outliers)', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        
        # 4. ANÁLISE DE OUTLIERS - QUANTIDADE DE REVIEWS
        print("\n4. ANÁLISE DE OUTLIERS - QUANTIDADE DE REVIEWS")
        print("-" * 60)
        
        qtd_reviews_criticos = [m.get('quantidade de reviews de críticos') or 0 for m in movies]
        qtd_reviews_usuarios = [m.get('quantidade de reviews de usuários') or 0 for m in movies]
        
        print(f"Reviews de críticos - Média: {np.mean(qtd_reviews_criticos):.0f}, "
            f"Mediana: {np.median(qtd_reviews_criticos):.0f}, "
            f"Max: {max(qtd_reviews_criticos)}")
        print(f"Reviews de usuários - Média: {np.mean(qtd_reviews_usuarios):.0f}, "
            f"Mediana: {np.median(qtd_reviews_usuarios):.0f}, "
            f"Max: {max(qtd_reviews_usuarios)}")
        
        # Histograma de Reviews
        ax4 = plt.subplot(3, 3, 4)
        ax4.hist(qtd_reviews_criticos, bins=20, alpha=0.7, label='Críticos', color='#3498db')
        ax4.set_xlabel('Quantidade de Reviews')
        ax4.set_ylabel('Frequência')
        ax4.set_title('Distribuição - Reviews de Críticos', fontweight='bold')
        ax4.legend()
        
        ax5 = plt.subplot(3, 3, 5)
        # Usar escala logarítmica para reviews de usuários devido à grande variação
        if max(qtd_reviews_usuarios) > 1000:
            ax5.hist(qtd_reviews_usuarios, bins=20, alpha=0.7, label='Usuários', color='#9b59b6')
            ax5.set_yscale('log')
        else:
            ax5.hist(qtd_reviews_usuarios, bins=20, alpha=0.7, label='Usuários', color='#9b59b6')
        ax5.set_xlabel('Quantidade de Reviews')
        ax5.set_ylabel('Frequência')
        ax5.set_title('Distribuição - Reviews de Usuários', fontweight='bold')
        ax5.legend()
        
        # 5. ANÁLISE DE DUPLICADAS
        print("\n5. ANÁLISE DE DUPLICATAS")
        print("-" * 60)
        
        # Verificar URLs duplicadas
        urls = [m.get('url') for m in movies if m.get('url')]
        urls_duplicadas = [url for url, count in Counter(urls).items() if count > 1]
        print(f"URLs duplicadas: {len(urls_duplicadas)}")
        
        # Verificar títulos duplicados
        titulos = [m.get('titulo') for m in movies if m.get('titulo')]
        titulos_duplicados = [t for t, count in Counter(titulos).items() if count > 1]
        print(f"Títulos duplicados: {len(titulos_duplicados)}")
        if titulos_duplicados:
            print(f"  Títulos: {', '.join(titulos_duplicados[:5])}")
        
        # Gráfico de Duplicatas
        ax6 = plt.subplot(3, 3, 6)
        duplicatas = {
            'URLs': len(urls_duplicadas),
            'Títulos': len(titulos_duplicados)
        }
        ax6.bar(duplicatas.keys(), duplicatas.values(), color='#e67e22')
        ax6.set_ylabel('Quantidade')
        ax6.set_title('Registros Duplicados', fontweight='bold')
        
        # 6. ANÁLISE DE DURAÇÃO
        print("\n6. ANÁLISE DE DURAÇÃO DOS FILMES")
        print("-" * 60)
        
        duracoes_min = []
        for movie in movies:
            duracao = movie.get('duracao')
            if duracao:
                try:
                    # Converter formato HH:MM:SS para minutos
                    parts = duracao.split(':')
                    minutos = int(parts[0]) * 60 + int(parts[1])
                    duracoes_min.append(minutos)
                except:
                    pass
        
        if duracoes_min:
            print(f"Duração média: {np.mean(duracoes_min):.0f} minutos")
            print(f"Duração mediana: {np.median(duracoes_min):.0f} minutos")
            print(f"Duração mínima: {min(duracoes_min)} minutos")
            print(f"Duração máxima: {max(duracoes_min)} minutos")
            
            # Outliers de duração
            q1_d = np.percentile(duracoes_min, 25)
            q3_d = np.percentile(duracoes_min, 75)
            iqr_d = q3_d - q1_d
            outliers_d = [d for d in duracoes_min if d < q1_d - 1.5*iqr_d or d > q3_d + 1.5*iqr_d]
            print(f"Outliers de duração: {len(outliers_d)}")
        
        ax7 = plt.subplot(3, 3, 7)
        ax7.hist(duracoes_min, bins=20, color='#1abc9c', alpha=0.7)
        ax7.axvline(np.mean(duracoes_min), color='red', linestyle='--', 
                    label=f'Média: {np.mean(duracoes_min):.0f} min')
        ax7.set_xlabel('Duração (minutos)')
        ax7.set_ylabel('Frequência')
        ax7.set_title('Distribuição de Duração', fontweight='bold')
        ax7.legend()
        
        # 7. ANÁLISE DE GÊNEROS
        print("\n7. ANÁLISE DE GÊNEROS")
        print("-" * 60)
        
        todos_generos = []
        for movie in movies:
            generos = movie.get('generos', [])
            todos_generos.extend(generos)
        
        generos_count = Counter(todos_generos)
        print(f"Total de gêneros únicos: {len(generos_count)}")
        print("Top 5 gêneros mais frequentes:")
        for genero, count in generos_count.most_common(5):
            print(f"  {genero}: {count} filmes")
        
        ax8 = plt.subplot(3, 3, 8)
        top_generos = dict(generos_count.most_common(8))
        ax8.barh(list(top_generos.keys()), list(top_generos.values()), color='#34495e')
        ax8.set_xlabel('Quantidade de Filmes')
        ax8.set_title('Gêneros Mais Frequentes', fontweight='bold')
        
        # 8. DISTRIBUIÇÃO POR ANO
        if anos:
            ax9 = plt.subplot(3, 3, 9)
            ax9.hist(anos, bins=30, color='#e74c3c', alpha=0.7)
            ax9.set_xlabel('Ano')
            ax9.set_ylabel('Quantidade de Filmes')
            ax9.set_title('Distribuição por Ano de Lançamento', fontweight='bold')
            ax9.grid(True, alpha=0.3)
        
        # RESUMO FINAL
        print("\n" + "=" * 60)
        print("RESUMO DA QUALIDADE DOS DADOS")
        print("=" * 60)
        
        total_issues = (notas_criticos_invalidas + notas_usuarios_invalidas + 
                    datas_invalidas + len(urls_duplicadas) + len(titulos_duplicados))
        
        completude_media = np.mean(list(completude.values()))
        
        if completude_media >= 90 and total_issues == 0:
            qualidade = "EXCELENTE"
            cor = "verde"
        elif completude_media >= 75 and total_issues <= 5:
            qualidade = "BOA"
            cor = "amarelo"
        else:
            qualidade = "REQUER ATENÇÃO"
            cor = "vermelho"
        
        print(f"Qualidade Geral: {qualidade}")
        print(f"Completude Média: {completude_media:.1f}%")
        print(f"Total de Problemas Identificados: {total_issues}")
        
        plt.tight_layout()
        plt.show()

    def run_descriptive_analysis(self):
        # 2.1 Valores mais comuns (top gêneros, top atores???)
        genres = []
        actors = []
        diretors = []

        for movie in self.movies_list:
            if movie["generos"]:
                g = movie["generos"]
                if isinstance(g, list):
                    genres.extend(g)
                elif isinstance(g, str) and g.strip():
                    genres.append(g)
            
            if movie["diretor"]:
                d = movie["diretor"]
                if isinstance(d, list):
                    diretors.extend(d)
                elif isinstance(d, str) and d.strip():
                    diretors.append(d)

            if movie["elenco"] and isinstance(movie["elenco"], list):
                for actor in movie["elenco"]:
                    if isinstance(actor, str) and actor.strip():
                        actors.append(actor)

        genre_counts = Counter(genres)
        actor_counts = Counter(actors)
        diretors_counts = Counter(diretors)

        top_genres = genre_counts.most_common(5)
        top_actors = actor_counts.most_common(5)
        top_diretors = diretors_counts.most_common(5)

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

        self.plot_bar_simple(
            labels=[a for a, _ in top_diretors],
            values=[c for _, c in top_diretors],
            title="Top 10 Diretores Mais Frequentes",
            xlabel="Contagem",
            save_path="graphs/top_diretores.png"
        )

        # 2.2 Média, mediana, moda, desvio padrão, mínimo e máximo
        # Avaliaçao geral ou por filme..? 
        # Campos: duração, data de lançamento, nota média dos criticos, nota média dos usuários
        fields = {
            "duracao": [],
            "nota média dos criticos": [],
            "nota média dos usuários": [],
            "data de lançamento": []
        }

        for movie in self.movies_list:

            if "duracao" in movie and isinstance(movie["duracao"], (int, float)):
                fields["duracao"].append(movie["duracao"])

            if "nota média dos criticos" in movie and isinstance(movie["nota média dos criticos"], (int, float)):
                fields["nota média dos criticos"].append(movie["nota média dos criticos"])

            if "nota média dos usuários" in movie and isinstance(movie["nota média dos usuários"], (int, float)):
                fields["nota média dos usuários"].append(movie["nota média dos usuários"])

            if "data de lançamento" in movie and movie["data de lançamento"] is not None:
                try:
                    dt = datetime.strptime(movie["data de lançamento"], "%Y-%m-%d")
                    fields["data de lançamento"].append(dt.timestamp())
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
        # Correalação da avaliação (nota média dos criticos, nota média dos usuários) e a data de lançamento e duração

        correlation_data = {
            "duracao": [],
            "nota média dos criticos": [],
            "nota média dos usuários": [],
            "data de lançamento": []
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

            if "nota média dos criticos" in movie and isinstance(movie["nota média dos criticos"], (int, float)):
                temp_data["nota média dos criticos"] = float(movie["nota média dos criticos"])
            else:
                all_data = False

            if "nota média dos usuários" in movie and isinstance(movie["nota média dos usuários"], (int, float)):
                temp_data["nota média dos usuários"] = float(movie["nota média dos usuários"])
            else:
                all_data = False

            if "data de lançamento" in movie and movie["data de lançamento"] is not None:
                dt = datetime.strptime(movie["data de lançamento"], "%Y-%m-%d")
                temp_data["data de lançamento"] = dt.year
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
                y=correlation_data["nota média dos criticos"],
                title="Correlação: Duração vs Média Crítica",
                xlabel="Duração (min)",
                ylabel="Média Crítica",
                save_path="graphs/scatter_duracao_nota_media_dos_criticos.png"
            )

            # Media usuário vs duração
            self.plot_scatter(
                x=correlation_data["duracao"],
                y=correlation_data["nota média dos usuários"],
                title="Correlação: Duração vs Média Usuário",
                xlabel="Duração (min)",
                ylabel="Média Usuário",
                save_path="graphs/scatter_duracao_nota_media_dos_media_usuarios.png"
            )

            # Media crítica vs ano de lançamento
            self.plot_scatter(
                x=correlation_data["data de lançamento"],
                y=correlation_data["nota média dos criticos"],
                title="Correlação: Ano de Lançamento vs Média Crítica",
                xlabel="Ano de Lançamento",
                ylabel="Média Crítica",
                save_path="graphs/scatter_ano_nota_media_dos_criticos.png"
            )

            # Media usuário vs ano de lançamento
            self.plot_scatter(
                x=correlation_data["data de lançamento"],
                y=correlation_data["nota média dos usuários"],
                title="Correlação: Ano de Lançamento vs Média Usuário",
                xlabel="Ano de Lançamento",
                ylabel="Média Usuário",
                save_path="graphs/scatter_ano_nota_media_dos_media_usuarios.png"
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
        self.run_quality_analysis(self.movies_list)

if __name__ == "__main__":
    with open("filmes.json", "r", encoding="utf-8") as file:
        movies_data = json.load(file)

    analyzer = DataAnalyzer(movies_data)
    analyzer.run_all()