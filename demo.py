from rich import emoji
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from billboard import *

console = Console()


# Function to draw the menu
def draw_menu():
    console.clear()
    console.print("CINE BUS :bus: 🎥", style="bold")
    console.print("Autors: Laia Mogas i Joan Gomà 😎", style="bold")
    console.print("\nOpcions:\n")

    console.print(":one:  Mostra la cartellera")
    console.print(":two:  Cercar en la cartellera")
    console.print(":three:  Mostra el graf de busos")
    console.print(":four:  Mostra el graf de la ciutat")
    console.print(":five:  Tria cine i ubicació")

    console.print()


def draw_billboard(billboard: Billboard) -> None:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Cinema", justify="left")
    table.add_column("Pel·lícula")
    table.add_column("Durada")
    table.add_column("Horari")

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


# Function to handle user input
def handle_input(key: str, billboard: Billboard):
    if key == "1":
        console.clear()
        draw_billboard(billboard)
    elif key == "2":
        ...
    elif key == "3":
        ...
    elif key == "4":
        ...
    elif key == "5":
        ...

    Prompt.ask("\nPress Enter to continue...")


def main() -> None:
    billboard: Billboard = read()
    while True:
        draw_menu()
        key = Prompt.ask("Selecciona el nombre de la acció que vulgui dur a terme")
        handle_input(key, billboard)


if __name__ == "__main__":
    main()
