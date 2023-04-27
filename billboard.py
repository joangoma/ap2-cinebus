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
    """Reads the movie"""
    billboard: Billboard = Billboard(list(), list(), list())

    URL: str = "https://www.sensacine.com/cines/cines-en-72480/?page=1"
    page = requests.get(URL)

    soup = BeautifulSoup(page.content, "html.parser")

    films = soup.find_all("div", {"class": "item_resa"})

    for film in films:
        film_info_div = film.find("div", {"class": "j_w"})

        film_info_str = film_info_div["data-movie"]
        film_info = json.loads(film_info_str)

        list_film_sessions_str = film.find("ul", {"class": "list_hours"})
        sessions_str = list_film_sessions_str.find_all("em")

        film: Film = Film(
            film_info["title"],
            film_info["genre"],
            film_info["directors"],
            film_info["actors"],
        )
        # LES DADES DEL CINEMA NO ESTAN CARREGADES, PER TANT, NO FUNCIONA AIXÒ
        cinema: Cinema = Cinema(film_info["name"], film_info["adress"])

        billboard.add_film(film)
        billboard.add_cinema(cinema)

        # DIRIA QUE FUNCIONA PERÒ NO ESTÀ AL 100 TESTEJAT
        for session in sessions_str:
            session_time_str = session["data-times"][1:-1]
            session_time = [int(t) for t in session_time_str.split(",")]

            projection: Projection = Projection(
                film, cinema, session_time, film_info["language"]
            )
            billboard.add_projection(projection)


if __name__ == "__main__":
    read()
