from enum import Enum


class URLType(Enum):
    END = -1
    IMDB = 0
    ROTT = 1
    LTTR = 2


class URL:
    def __init__(self, url_str: str, type: URLType) -> None: 
        self.url_str = url_str
        self.type = type
    
    def get_url(self) -> str:
        return self.url_str
    
    def get_type(self) -> URLType:
        return self.type
    
    def __str__(self):
        return f"URLType: {self.url_str}, {self.type}"
    
    def __eq__(self, other):
        if not isinstance(other, URL):
            return NotImplemented
        return self.url_str == other.url_str

    def __hash__(self):
        return hash(self.url_str)
