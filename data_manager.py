from movie import Movie

def load_movies(filename):
    movies = []
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    for i in range(1, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
    
        data = line.split(",")
        if len(data) >= 5:
            movie = Movie(data[0], data[1], data[2], data[3], data[4])
            movies.append(movie)

    return movies

def save_movies(filename, movies):
    with open(filename, "w", encoding="utf-8") as file:
        file.write("id,title,genre,year,users_rating\n")

        for movie in movies:
            file.write(movie.to_csv() + "\n")

def generate_id(movies):
    max_id = 0
    
    for movie in movies:
        if movie.id > max_id:
            max_id = movie.id
    return max_id + 1