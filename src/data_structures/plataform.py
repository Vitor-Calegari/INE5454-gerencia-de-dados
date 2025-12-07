from rapidfuzz import fuzz

class Plataform:
    
    def __init__(self, plataform: str, link:str):
        self.plataform = plataform
        self.link = link
    
    def get_plataform(self):
        return self.plataform
    
    def get_link(self):
        return self.link
    
    def __str__(self):
        return f"{self.plataform}: {self.link}"
    
    
    def __eq__(self, other):
        if not isinstance(other, Plataform):
            return NotImplemented
        limiar = 0.8
        similarity = fuzz.ratio(self.plataform.lower(), other.plataform.lower())
        return similarity >= limiar

    def __ne__(self, other):
        if not isinstance(other, Plataform):
            return NotImplemented
        return not self.__eq__(other)