def quick_sort_rating(movies):
    if len(movies) <= 1:
        return movies
    
    pivot = movies[0]
    higher = []
    lower = []

    for movie in movies[1:]:
        if movie.rating >= pivot.rating:
            higher.append(movie)
        else:
            lower.append(movie)
    
    return quick_sort_rating(higher) + [pivot] + quick_sort_rating(lower)

def quick_sort_year(movies):
    if len(movies) <= 1:
        return movies
    
    pivot = movies[0]
    newer = []
    older = []

    for movie in movies[1:]:
        if movie.year >= pivot.year:
            newer.append(movie)
        else:
            older.append(movie)
    return quick_sort_year(newer) + [pivot] + quick_sort_year(older)