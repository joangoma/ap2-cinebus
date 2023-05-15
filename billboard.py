import json
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


@dataclass
class Film:
    title: str
    genre: list[str]
    directors: list[str]
    actors: list[str]

    def __init__(self, data_film_str) -> None:
        """Initializes Film class given it's data in html format."""

        data_film = json.loads(data_film_str)

        self.title = data_film["title"]
        self.genre = data_film["genre"]
        self.directors = data_film["directors"]
        self.actors = data_film["actors"]


@dataclass
class Cinema:
    name: str
    address: str

    def __init__(self, data_cinema_str) -> None:
        """Initializes Cinema class given it's data in html format."""

        data_cinema = json.loads(data_cinema_str)
        self.name = data_cinema["name"]
        # no trobo la puta adreça del teatre en el fitxer html.
        self.address = "----"


@dataclass
class Projection:
    film: Film
    cinema: Cinema
    time: tuple[int, int]  # hora:minut
    duration: int  # minuts
    language: str

    def __init__(self, session_data: str, film: Film, cinema: Cinema) -> None:
        """Initializes Projection dataclass given it's data in html format."""

        session_time_str = session_data["data-times"][1:-1]

        starting_time_str = session_time_str.split(",")[0][1:-1]
        ending_time_str = session_time_str.split(",")[-1][1:-1]

        starting_time: tuple[int, int] = (
            int(starting_time_str.split(":")[0]),
            int(starting_time_str.split(":")[1]),
        )

        ending_time: tuple[int, int] = (
            int(ending_time_str.split(":")[0]),
            int(ending_time_str.split(":")[1]),
        )

        self.film = film
        self.cinema = cinema
        self.time = starting_time
        self.duration = self.calculate_duration(starting_time, ending_time)
        self.language = "----"

    def calculate_duration(
        self, starting_time: tuple[int, int], ending_time: tuple[int, int]
    ) -> int:
        start_minutes = starting_time[0] * 60 + starting_time[1]
        end_minutes = ending_time[0] * 60 + ending_time[1]

        if ending_time[0] < starting_time[0]:
            end_minutes += 24 * 60

        return end_minutes - start_minutes


@dataclass
class Billboard:
    films: list[Film]
    cinemas: list[Cinema]
    projections: list[Projection]
    films_titles: set[str]

    def add_film(self, film: Film) -> None:
        """Adds a film in the list that tracks the film avoiding repetitions."""

        if film.title not in self.films_titles:
            self.films.append(film)
            self.films_titles.add(film.title)

    def add_cinema(self, cinema: Cinema) -> None:
        """Adds a cinema in the list that tracks the cinemas avoiding repetitions."""

        if not self.cinemas or self.cinemas[-1] != cinema:
            self.cinemas.append(cinema)

    def add_projection(self, projection: Projection) -> None:
        self.projections.append(projection)

    def search_film_by_word(self, word: str) -> list[Film]:
        return [film for film in self.films if word.lower() in film.title.lower()]


def read() -> Billboard:
    """Scrapes the data from sensacine.com web of
    the movies and theaters of Barcelona"""

    billboard: Billboard = Billboard(list(), list(), list(), set())

    base_url: str = "https://www.sensacine.com/cines/cines-en-72480/?page="

    for idx_page in range(1, 4):
        url = base_url + str(idx_page)

        page = requests.get(url)

        soup = BeautifulSoup(page.content, "html.parser")

        movies = soup.find_all("div", {"class": "item_resa"})

        for movie in movies:
            data_theater_movie_div = movie.find("div", {"class": "j_w"})

            # We obtain and process the movie data

            data_film_str = data_theater_movie_div["data-movie"]
            film: Film = Film(data_film_str)
            billboard.add_film(film)

            # We obtain and process the theater data

            data_cinema_str = data_theater_movie_div["data-theater"]
            cinema: Cinema = Cinema(data_cinema_str)
            billboard.add_cinema(cinema)

            # We obtain and process the sessions hours data

            list_film_sessions_str = movie.find("ul", {"class": "list_hours"})

            sessions_str = list_film_sessions_str.find_all("em")

            for session in sessions_str:
                projection: Projection = Projection(session, film, cinema)

                billboard.add_projection(projection)

    return billboard


if __name__ == "__main__":
    billboard = read()
    # test code
    for f in billboard.search_film_by_word("La"):
        print(f.title)
