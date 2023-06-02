from dataclasses import dataclass
from typing import TypeAlias, TypeVar

import matplotlib.pyplot as plt
import networkx as nx
import requests
from staticmap import CircleMarker, Line, StaticMap

Coord: TypeAlias = tuple[float, float]  # (latitude, longitude)
BusesGraph: TypeAlias = nx.Graph

T = TypeVar('T')

URL = "https://www.ambmobilitat.cat/OpenData/ObtenirDadesAMB.json"


def get_data_from_url() -> dict[str, dict[str, 'T']]:
    """Returns a dictionary of the buses data from the URL.
    The URL is a constant."""

    response = requests.get(URL)
    assert response, "Error with URL"
    return response.json()


def get_linies() -> list[dict[str, 'T']]:
    """Returns a list of bus lines"""
    
    data: dict[str, dict[str, 'T']] = get_data_from_url()
    data = data[list(data.keys())[0]]

    linies = data[list(data.keys())[1]]
    return linies[list(linies.keys())[0]]  # llista de diccionaris


def get_buses_graph() -> BusesGraph:
    """Downloads the data of the AMB and returns an undirected graph of buses.
    There is a different node for each line in each stop.

    The format of nodes ids is "{CodiAMB}-{linia}"

    note1: CodAMB is a unique id of each stop
        (there may be different stops with the same name so Nom is a bad id)
    note2: stops out of Barcelona are ignored
    note3: substops from the same stop are not connected yet
    """

    buses: BusesGraph = BusesGraph()

    linies: list[dict[str, 'T']] = get_linies()  # llista de diccionaris

    for linia in linies:
        parades_linia: list[dict[str, 'T']] = linia["Parades"]["Parada"]

        for i, parada in enumerate(parades_linia):
            if parada["Municipi"] == "Barcelona":
                buses.add_node(
                    parada["CodAMB"] + "-" + linia["Nom"],
                    nom=parada["Nom"],
                    coord=(parada["UTM_X"], parada["UTM_Y"]),
                    linia=linia["Nom"],
                )

                prev_parada = parades_linia[i - 1]

                if (
                    i != 0
                    and prev_parada["Municipi"] == "Barcelona"
                    and parada["CodAMB"] + "-" + linia["Nom"]
                    != prev_parada["CodAMB"] + "-" + linia["Nom"]
                ):
                    buses.add_edge(
                        parada["CodAMB"] + "-" + linia["Nom"],
                        prev_parada["CodAMB"] + "-" + linia["Nom"],
                        linia=linia["Nom"],
                    )

    return buses


def show_buses(g: BusesGraph) -> None:
    """Shows the graph interactively using network.draw

    note: some nodes are not connected because they belong to lines outside BCN
    """

    positions = nx.get_node_attributes(g, "coord")
    nx.draw(g, pos=positions, with_labels=False, node_size=10)
    plt.show()


def plot_buses(g: BusesGraph, nom_fitxer: str) -> None:
    """Saves the graph as an image with the map of the city in the background
    in the file nom_fitxer using staticmaps"""

    map = StaticMap(300, 300)

    # draw nodes
    for pos in nx.get_node_attributes(g, "coord").values():
        map.add_marker(CircleMarker((pos[1], pos[0]), "green", 3))

    # draw edges
    for edge in g.edges:
        coord_1 = (g.nodes[edge[0]]["coord"][1], g.nodes[edge[0]]["coord"][0])
        coord_2 = (g.nodes[edge[1]]["coord"][1], g.nodes[edge[1]]["coord"][0])
        map.add_line(Line([coord_1, coord_2], "blue", 2))

    image = map.render()
    image.save(nom_fitxer)
