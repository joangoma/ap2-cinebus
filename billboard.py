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
    ...


@dataclass
class Cinema:
    name: str
    address: str
    ...


@dataclass
class Projection:
    film: Film
    cinema: Cinema
    time: tuple[int, int]  # hora:minut
    language: str
    ...


@dataclass
class Billboard:
    films: list[Film]
    cinemas: list[Cinema]
    projections: list[Projection]

    def add_film(self, film: Film) -> None:
        self.films.append(film)

    def add_cinema(self, cinema: Cinema) -> None:
        self.cinemas.append(cinema)

    def add_projection(self, projection: Projection) -> None:
        self.projections.append(projection)

    def search_film_by_word(self, word: str) -> list[Film]:
        ...


def read() -> Billboard:
    """Scrapes the data from sensacine.com web of
    the movies and theaters of Barcelona    """

    # NOTA LAIA:
    # Perque et facis la idea, tal com diu l'enunciat, i ha els containers aquests
    # de nom item_resa que contenen dos diccionaris de nom data movie i data_theater.
    # Estan com a dins d'un container (div d'html) per aixo accediexo al j_w aquest random.
    # També hi ha una unordered list que conté tots els horaris però com que tot
    # el accedim ho fem com en format string, he hagut de fer un codi poxo
    # per passar les llistes de numeros en str a nombres normals.
    # Com que els altres son diccionaris, hi ha el json aquest sexy que ens ho
    # fa directament.
    # Per veuere-ho bé, inspecciona la pagina i ja està

    billboard: Billboard = Billboard(list(), list(), list())

    URL: str = "https://www.sensacine.com/cines/cines-en-72480/?page=1"

    for idx_page in range(1, 4):
        # URL[-1] = str(idx_page)

        page = requests.get(URL)

        soup = BeautifulSoup(page.content, "html.parser")

        movies = soup.find_all("div", {"class": "item_resa"})

        for film in movies:
            data_thater_movie_div = film.find("div", {"class": "j_w"})

            # Accedim a la info que necessitem
            data_film_str = data_thater_movie_div["data-movie"]
            data_cinema_str = data_thater_movie_div["data-theater"]
            list_film_sessions_str = film.find("ul", {"class": "list_hours"})

            data_film = json.loads(data_film_str)
            data_cinema = json.loads(data_cinema_str)

            sessions_str = list_film_sessions_str.find_all("em")

            film: Film = Film(
                data_film["title"],
                data_film["genre"],
                data_film["directors"],
                data_film["actors"],
            )

            cinema: Cinema = Cinema(data_cinema["name"], "hola")

            billboard.add_film(film)
            billboard.add_cinema(cinema)

            # DIRIA QUE FUNCIONA PERÒ NO ESTÀ AL 100% TESTEJAT
            for session in sessions_str:
                session_time_str = session["data-times"][1:-1]
                session_time = [int(t) for t in session_time_str.split(",")]

                projection: Projection = Projection(
                    film, cinema, session_time, data_film["language"]
                )
                billboard.add_projection(projection)

    return billboard


if __name__ == "__main__":
    read()
