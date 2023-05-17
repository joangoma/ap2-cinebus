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
        """Initializes Film class given its data in html format."""

        data_film = json.loads(data_film_str)

        self.title = data_film["title"]
        self.genre = data_film["genre"]
        self.directors = data_film["directors"]
        self.actors = data_film["actors"]


@dataclass
class Cinema:
    name: str
    address: str
    coord: tuple[float, float]

    def __init__(
        self, data_cinema_str, cinemas_location: dict[str, tuple[float, float]]
    ) -> None:
        """Initializes Cinema class given its data in html format."""

        data_cinema = json.loads(data_cinema_str)
        self.name = data_cinema["name"]
        # no trobo la puta adreça del teatre en el fitxer html.
        self.address = "----"
        self.coord = cinemas_location[self.name]
        # obtenir coordenades a partir de https://www.sensacine.com/cines/cine/{E0764}/mapa/


@dataclass
class Projection:
    film: Film
    cinema: Cinema
    time: tuple[int, int]  # hora:minut
    duration: int  # minuts
    language: str

    def __init__(self, session_data: str, film: Film, cinema: Cinema) -> None:
        """Initializes Projection dataclass given its data in html format."""

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
        self.language = "----"  # posa si es VO o doblada

    def calculate_duration(
        self, starting_time: tuple[int, int], ending_time: tuple[int, int]
    ) -> int:
        # afegir docstring
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


def read_billboard() -> Billboard:
    """Scrapes the data from sensacine.com web of
    the movies and theaters of Barcelona"""

    billboard: Billboard = Billboard(list(), list(), list(), set())

    base_url: str = "https://www.sensacine.com/cines/cines-en-72480/?page="

    cinemas_location: dict[str, tuple[float, float]] = {
        "Arenas Multicines 3D": (41.37645873603848, 2.1492467400941715),
        "Aribau Multicines": (41.38622954118975, 2.1625393383857823),
        "Bosque Multicines": (41.40161248569297, 2.151937970358723),
        "Cinema Comedia": (41.38963905352764, 2.1677083550158467),
        "Cinemes Girona": (41.39976219340622, 2.1646021126874433),
        "Cines Verdi Barcelona": (41.404123503674946, 2.1569592746060673),
        "Cinesa Diagonal 3D": (41.3939571456629, 2.136310199194024),
        "Cinesa Diagonal Mar 18": (41.4104066884377, 2.2165577979125546),
        "Cinesa La Maquinista 3D": (41.43968702910417, 2.1983860838534364),
        "Cinesa SOM Multiespai": (41.435576596290986, 2.1807710685108392),
        "Glòries Multicines": (41.4053995786576, 2.1927300415232907),
        "Gran Sarrià Multicines": (41.39497626938792, 2.1340554979084074),
        "Maldá Arts Forum": (41.38335521981628, 2.1739034685088092),
        "Renoir Floridablanca": (41.38181932245526, 2.162600741522349),
        "Sala Phenomena Experience": (41.40916923817682, 2.171972029879437),
        "Yelmo Cines Icaria 3D": (41.39081534652564, 2.198733496795877),
        "Boliche Cinemes": (41.39540740361847, 2.153624068509293),
        "Zumzeig Cinema": (41.37754018596865, 2.1450699973441822),
        "Balmes Multicines": (41.40736701577023, 2.138718385701353),
        "Cinesa La Farga 3D ": (41.36324361629017, 2.104830226735673),
        "Filmax Gran Via 3D": (41.358458853930166, 2.12835815131626),
        "Full HD Cinemes Centre Splau": (41.34757656010739, 2.0790624624109917),
        "Cine Capri": (41.325897166270195, 2.0953815132325104),
        "Ocine Màgic": (41.44390419188643, 2.2306844298807826),
        "Cinebaix": (41.38204532152056, 2.0451188433715655),
        "Cinemes Can Castellet": (41.345363870736016, 2.0405710690597574),
        "Cinemes Sant Cugat": (41.469755698209426, 2.0905412796073817),
        "Cines Montcada": (41.49435241992408, 2.180264296085647),
    }

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
            cinema: Cinema = Cinema(data_cinema_str, cinemas_location)
            billboard.add_cinema(cinema)

            # We obtain and process the sessions hours data

            list_film_sessions_str = movie.find("ul", {"class": "list_hours"})

            sessions_str = list_film_sessions_str.find_all("em")

            for session in sessions_str:
                projection: Projection = Projection(session, film, cinema)

                billboard.add_projection(projection)

    return billboard


if __name__ == "__main__":
    billboard = read_billboard()
