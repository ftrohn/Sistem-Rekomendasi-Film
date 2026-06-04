from movie import Movie

from data_manager import generate_id

def add_movie(movies, title, genre, year, rating):
    new_id = generate_id(movies)
    movie = Movie(new_id, title, genre, year, rating)
    movies.append(movie)

def update_movie(movies, movie_id, title, genre, year, rating):
    for movie in movies:
         if movie.id == movie_id:
             movie.title = title
             movie.genre = genre
             movie.year = int(year)
             movie.rating = float(rating)
             return True
         return False

def delete_movie(movies, movie_id):
    for i in range(len(movies)):
        if movies[i].id == movie_id:
            del movies[i]
            return True
        return False