class Review:
    
    def __init__(self):
        self.rating = None
        self.text = None
        self.date = None
        self.link = None
    
    def get_rating(self) -> float | None:
        return self.rating

    def set_rating(self, rating: float):
        self.rating = rating

    def get_text(self) -> str | None:
        return self.text

    def set_text(self, text: str):
        self.text = text

    def get_date(self) -> str | None:
        return self.date
    
    def get_link(self) -> str | None:
        return self.link

    def set_date(self, date: str):
        self.date = date

    def __str__(self):
        return f"Rating: {self.rating},\n\
                 Text: {self.text},\n\
                 Date: {self.date}"