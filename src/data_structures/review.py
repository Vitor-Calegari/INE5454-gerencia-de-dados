class Review:
    
    def __init__(self):
        self.rating = 0
        self.text = ""
        self.date = ""
    
    def get_rating(self):
        return self.rating

    def set_rating(self, rating):
        self.rating = rating

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = text

    def get_date(self):
        return self.date

    def set_date(self, date):
        self.date = date

    def __str__(self):
        return f"Rating: {self.rating},\n\
                 Text: {self.text},\n\
                 Date: {self.date}"
