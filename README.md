# INE5454-gerencia-de-dados

Para executar o código desenvolvido do crawler, prepare o ambiente:

```
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

Se for a primeira execução, também executar:

```
playwright install
```

E uma dessas opções

```
sudo playwright install-deps
sudo apt-get install libavif16
```
Para executar a aplicação desenvolvida que utiliza os dados extraídos pelo crawler, veja o README disponível no diretório destinado a aplicação.
