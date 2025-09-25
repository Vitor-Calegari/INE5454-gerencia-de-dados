import requests   # para requisições HTTP
import json       # para gerar JSON
from bs4 import BeautifulSoup  # para parsear HTML


url = 'https://www.imdb.com/chart/top/'

# adiciona cabeçalhos para imitar um navegador real
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36"
}

def scrapImdbTitles():
    # Faz a requisição da página
    resposta = requests.get(url, headers=headers)

    if (not resposta.ok):
        print(f"Nao foi possivel obter o html de {url}")
        print(f"Conteudo retornado:")
        print(site)
    
    site = BeautifulSoup(resposta.content, "html.parser")

    # encontra o JSON-LD
    script_tag = site.find("script", type="application/ld+json")
    data = json.loads(script_tag.string)

    # pega todos os títulos
    titulos = [item["item"]["name"] for item in data["itemListElement"]]

    # salva
    with open("imdb_top250.json", "w", encoding="utf-8") as f:
        json.dump(titulos, f, indent=4, ensure_ascii=False)
    
    print("Arquivo imdb_top250.json criado com sucesso!")
    return