def linear_search_genre(movies, genre):
    result = []
    for movie in movies:
        if genre.lower() in movie.genre.lower():
            result.append(movie)
    return result

def linear_search_title(movies, keyword):
    result = []
    for movie in movies:
        if keyword.lower() in movie.title.lower():
            result.append
    return result