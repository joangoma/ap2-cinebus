from rich import emoji
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table

from billboard import *

console = Console()


# Function to draw the menu
def draw_menu():
    console.clear()
    MARKDOWN = """
# CINE BUS 🚌 🎥
## Autors: Laia Mogas i Joan Gomà 
Opcions:

1. Mostra la cartellera
2. Cerca en la cartellera
3. Mostra el graf de busos
4. Mostra el graf de la ciutat
5. Tria peli i ubicació
"""

    md = Markdown(MARKDOWN)
    console.print(md)
    console.print()


def show_billboard(billboard: Billboard) -> None:
    """Shows the billboard info in a table format."""

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Cinema", justify="left")
    table.add_column("Pel·lícula")
    table.add_column("Durada")
    table.add_column("Horari")

    time = 18
    for i, projection in enumerate(sorted(billboard.projections, key=lambda x: x.time)):
        table.add_row(
            projection.cinema.name,
            projection.film.title,
            str(projection.duration),
            "{:<02d}".format(projection.time[0])
            + ":"
            + "{:<02d}".format(projection.time[1]),
        )

    console.print("\nCartellera en horari no decreixent:\n")
    console.print(table)


def show_projections(projections: list[Projection]) -> None:
    """Show a set of films to the user"""

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Cinema", justify="left")
    table.add_column("Pel·lícula")
    table.add_column("Durada")
    table.add_column("Horari")

    time = 18
    for i, projection in enumerate(sorted(projections, key=lambda x: x.time)):
        table.add_row(
            projection.cinema.name,
            projection.film.title,
            str(projection.duration),
            "{:<02d}".format(projection.time[0])
            + ":"
            + "{:<02d}".format(projection.time[1]),
        )

    console.print("\nCartellera en horari no decreixent:\n")
    console.print(table)


def search_billboard(billboard: Billboard) -> None:
    """Show the films that fulfill the given constraints by the user"""

    key = Prompt.ask(
        "Filtra la busca de la pel·lícula per:",
        choices=["title", "starting time", "duration"],
    )

    projections: list[Projection] = list()
    if key == "title":
        word = Prompt.ask("Introdueixi el títol de la seva pel·lícula")
        projections = billboard.search_projection_by_word(word)
    if key == "starting time":
        start_time = Prompt.ask(
            "Introdueixi a partir de quina hora vol anar a veure la pel·lícula (ex: 12:30))"
        )
        hour, minute = start_time.split(":")
        projections = billboard.search_projection_by_time((int(hour), int(minute)))

    if key == "duration":
        durada = int(
            Prompt.ask("Introdueixi la durada que vol que duri la seva pel·lícula")
        )
        projections = billboard.search_projection_by_duration(durada)

    show_projections(projections)


def handle_input(key: str, billboard: Billboard) -> None:
    """Function that handles user input."""
    if key == "1":
        show_billboard(billboard)
    elif key == "2":
        search_billboard(billboard)
    elif key == "3":
        ...
    elif key == "4":
        ...
    elif key == "5":
        ...

    Prompt.ask("\nPress Enter to continue...")


def main() -> None:
    billboard: Billboard = read_billboard()
    while True:
        draw_menu()
        key = Prompt.ask("Selecciona el nombre de la acció que vulgui dur a terme")
        handle_input(key, billboard)


if __name__ == "__main__":
    main()
