def recommend_movies(movies, genre, min_year, min_rating):
  result = []
  for movie in movies:
    if genre.lower() in movie.genre.lower():
      if movie.year >= min_year:
        if movie.rating >= min_rating:
          result.append(movie)
  return result
