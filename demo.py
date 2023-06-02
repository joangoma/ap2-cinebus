import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from rich import emoji
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.style import Style
from rich.table import Table

from billboard import *
from buses import *
from city import *

console = Console()


def draw_menu():
    """Shows the main menu."""

    console.clear()
    MARKDOWN = """
# CINE BUS 🚌 🎥
## Autors: Laia Mogas i Joan Gomà
"""

    md = Markdown(MARKDOWN)
    console.print(md)
    options = [
        "1 Show billboard",
        "2 Find film",
        "3 Show buses graph",
        "4 Show city graph",
        "5 Go to the cinema!",
        "6 Exit",
    ]
    console.print()
    console.print(
        Panel(
            "\n".join(options),
            title="Options:",
            expand=False,
            border_style="cyan",
        ),
    )


def show_projections(projections: list[Projection]) -> None:
    """Show a set of films to the user"""

    table = Table(show_header=True)
    table.add_column("Cinema", justify="left", style="bright_cyan")
    table.add_column("Film", style="bright_magenta")
    table.add_column("Duration")
    table.add_column("Genre")
    table.add_column("Language")
    table.add_column("Schedule", style="green")

    for i, projection in enumerate(sorted(projections, key=lambda x: x.time)):
        table.add_row(
            projection.cinema.name,
            projection.film.title,
            str(projection.duration),
            projection.film.genre[0],
            str(projection.language),
            "{:<02d}".format(projection.time[0])
            + ":"
            + "{:<02d}".format(projection.time[1]),
        )

    console.print("\nBillboard in increasing order by schedule\n")
    console.print(table)


def search_billboard(billboard: Billboard) -> None:
    """Show the films that fulfill the given constraints by the user"""

    key = Prompt.ask(
        "Filter film by ",
        choices=["title", "starting time", "duration"],
    )

    projections: list[Projection] = list()

    if key == "title":
        word = Prompt.ask("Introduce the title of the film.")
        projections = billboard.search_projection_by_word(word)

    if key == "starting time":
        hour, minute = get_valid_time(
            "Introduce the time from which you can see the film."
        )
        projections = billboard.search_projection_by_time((hour, minute))

    if key == "duration":
        durada = get_valid_duration()
        projections = billboard.search_projection_by_duration(durada)

    show_projections(projections)


def show_film_titles(
    billboard: Billboard, osmx_g: OsmnxGraph, city_g: CityGraph
) -> None:
    """Show all film titles from the films that are available."""

    for title in billboard.films_titles:
        console.print(title.capitalize())
    Prompt.ask("\nPress enter to continue...")
    search_closest_cinema(billboard, osmx_g, city_g)


def get_valid_duration() -> int:
    """Returns the time input given by the user."""

    try:
        durada = int(
            Prompt.ask("Introduce the maximimum duration of the film you want to watch")
        )
        return durada
    except Exception as error:
        console.print("An error ocurred: ", type(error).__name__)
        return get_valid_duration()


def get_valid_film_title(billboard: Billboard) -> str | None:
    """Returns the title given by the user, in case it's from a film t'hat exists."""

    film = Prompt.ask("Introduce the film you want to see")

    if film.lower() not in billboard.films_titles:
        Prompt.ask("This film does not exist, press enter to continue")
        console.clear()
        return None

    return film


def get_valid_coordinates() -> Coord:
    """Asks the user their current coordinates and, if well introduced, they
    are returned. Otherwise the user is asked again"""

    ubi = Prompt.ask(
        "Introduce your location (latitude, longitude) ex: 41.38173, 2.12550"
    )

    try:
        ubi_l = ubi.split(",")
        lat, long = float(ubi_l[0]), float(ubi_l[1])
        return lat, long

    except Exception as error:
        console.print("An error ocurred: ", type(error).__name__)
        Prompt.ask("Please, enter the correct format, press enter to continue")
        return get_valid_coordinates()


def get_valid_time(question: str) -> tuple[int, int]:
    """Asks the time they want to leave. If it's given in a correct format it's returned.
    Otherwise the user is asked again"""

    leave_time = Prompt.ask("{0}, ex: 19:30".format(question))
    try:
        hour, minute = leave_time.split(":")
        leaving_time: tuple[int, int] = (int(hour), int(minute))
        return leaving_time
    except Exception as error:
        console.print("An error ocurred: ", type(error).__name__)
        Prompt.ask("Please, enter the correct format, press enter to continue")
        return get_valid_time(question)


def find_valid_projections(
    billboard: Billboard, osmx_g: OsmnxGraph, city_g: CityGraph
) -> list[tuple[Projection, Path]] | None:
    """Returns a list of all the projections of a given film that you
    can arrive given a starting time"""

    film = get_valid_film_title(billboard)
    if film is None:
        return None
    else:
        starting_coord: Coord = get_valid_coordinates()

        leaving_time: tuple[int, int] = get_valid_time(
            "At which time do you want to leave?"
        )

        projections = billboard.search_projection_by_time(leaving_time)

        valid_projections: list[tuple[Projection, Path]] = list()

        for projection in projections:
            if projection.film.title.lower() != film:
                continue

            path = find_path(
                osmx_g, city_g, starting_coord, CINEMAS_LOCATION[projection.cinema.name]
            )
            if path[1] <= calculate_time(leaving_time, projection.time):
                valid_projections.append((projection, path))

        return valid_projections


def show_find_closest_cinema_menu() -> None:
    """Shows the menu from 4th option (choose a cinema)."""

    console.clear()
    options = ["1 Show films available", "2 Choose film", "3 Exit"]
    console.print(
        Panel(
            "\n".join(options),
            title="Options:",
            expand=False,
            border_style="cyan3",
        )
    )


def show_projections_path_info(
    valid_projections: list[tuple[Projection, Path]]
) -> None:
    """Shows in a table the possible projections given the user constraints and
    the time to get there"""

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Num")
    table.add_column("Cinema", justify="left")
    table.add_column("Projection time")
    table.add_column("Time to get there")

    for i, (projection, path) in enumerate(valid_projections):
        table.add_row(
            str(i + 1),
            projection.cinema.name,
            "starts at {0}:{1}".format(projection.time[0], projection.time[1]),
            "{0} minutes".format(str(round(path[1], 1))),
        )

    console.print("\nCartellera en horari creixent en temps d'arribada\n")
    console.print(table)


def search_closest_cinema(
    billboard: Billboard, osmx_g: OsmnxGraph, city_g: CityGraph
) -> None:
    """Driver code of the funcionality about finding the closest cinema
    from a given position, film and schedule."""

    show_find_closest_cinema_menu()

    key = Prompt.ask("Select the option that you want")

    if key == "1":
        show_film_titles(billboard, osmx_g, city_g)

    elif key == "2":
        valid_projections: list[
            tuple[Projection, Path]
        ] | None = find_valid_projections(billboard, osmx_g, city_g)

        # Wrong title
        if valid_projections is None:
            search_closest_cinema(billboard, osmx_g, city_g)

        # No matching projections
        elif len(valid_projections) == 0:
            Prompt.ask(
                "Sorry, there are no projections available given these constraints"
            )
            search_closest_cinema(billboard, osmx_g, city_g)

        else:
            valid_projections.sort(key=lambda p: p[1][1])

            show_projections_path_info(valid_projections)

            num_projection = int(Prompt.ask("Choose the projection that you like!"))

            plot_path(city_g, valid_projections[num_projection - 1][1], "path.png")

            path_img = mpimg.imread("path.png")
            plt.imshow(path_img)
            plt.show()

    else:
        draw_menu()


def handle_input(
    key: str,
    billboard: Billboard,
    buses_g,
    osmx_g,
    city_g,
) -> None:
    """Function that handles user input."""

    if key == "1":
        show_projections(billboard.projections)
    elif key == "2":
        search_billboard(billboard)
    elif key == "3":
        show_buses(buses_g)
    elif key == "4":
        show_city(city_g)
    elif key == "5":
        search_closest_cinema(billboard, osmx_g, city_g)

    Prompt.ask("\nPress any key to return to the main page")


def main() -> None:
    billboard: Billboard = read_billboard()
    buses_g: BusesGraph = get_buses_graph()
    osmx_g: OsmnxGraph = get_osmnx_graph()
    city_g: CityGraph = build_city_graph(osmx_g, buses_g)

    while True:
        draw_menu()
        key = Prompt.ask("Select a valid option")
        if key == "6":
            console.print(
                Panel(
                    "See you soon! 👋 \nPlease rate our app in: https://newskit.social/blog/posts/cinebusfeedback",
                    expand=False,
                ),
            )
            return

        handle_input(key, billboard, buses_g, osmx_g, city_g)


if __name__ == "__main__":
    main()
