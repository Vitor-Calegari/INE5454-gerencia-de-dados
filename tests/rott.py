import requests   # para requisições HTTP
import json       # para gerar JSON
from bs4 import BeautifulSoup  # para parsear HTML


url = 'https://www.rottentomatoes.com/m/the_conjuring_last_rites'

# adiciona cabeçalhos para imitar um navegador real
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36"
}

def scrapRottTitles():
    # Faz a requisição da página
    resposta = requests.get(url, headers=headers)

    if (not resposta.ok):
        print(f"Nao foi possivel obter o html de {url}")
        print(f"Conteudo retornado:")
        print(site)
    
    site = BeautifulSoup(resposta.content, "html.parser")

    title_tag = site.find("rt-text", {"slot": "title", "context":"heading"})
    title = title_tag.text.strip()
    
    data = {
        "title": title,
        "url": url
    }

    # salva
    with open("rott.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print("Arquivo rott.json criado com sucesso!")
    return


if __name__ == "__main__":
    scrapRottTitles()
