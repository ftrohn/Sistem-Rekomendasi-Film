class Movie:
    def __init__(self, movie_id, title, genre, year, rating):
        self.id = int(movie_id)
        self.title = title
        self.genre = genre
        self.year = int(year)
        self.rating = float(rating)

    def to_csv(self):
        return f"{self.id},{self.title},{self.genre},{self.year},{self.rating}"

    def __str__(self):
        return f"{self.id} | {self.title} | {self.genre} | {self.year} | {self.rating}"