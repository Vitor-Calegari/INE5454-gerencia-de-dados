class Plataform:
    
    def __init__(self, plataform: str, link:str):
        self.plataform = plataform
        self.link = link
    
    def __str__(self):
        return f"{self.plataform}: {self.link}"