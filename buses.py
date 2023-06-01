from dataclasses import dataclass
from typing import TypeAlias

import matplotlib.pyplot as plt
import networkx as nx
import requests
from staticmap import CircleMarker, Line, StaticMap

Coord: TypeAlias = tuple[float, float]  # (latitude, longitude)
BusesGraph: TypeAlias = nx.Graph

URL = "https://www.ambmobilitat.cat/OpenData/ObtenirDadesAMB.json"


def get_data_from_url():
    """returns a dictionary of the buses data from the URL. The URL is a constant."""
    response = requests.get(URL)
    assert response, "Error with URL"
    return response.json()


def get_linies():
    """returns a list of bus lines"""
    data = get_data_from_url()
    data = data[list(data.keys())[0]]

    linies = data[list(data.keys())[1]]
    return linies[list(linies.keys())[0]]  # llista de diccionaris


def get_buses_graph() -> BusesGraph:
    """downloads the data of the AMB and returns an undirected graph of buses"""

    # nota: no totes les linies comencen i acaben amb la mateixa parada, pero per simplicitat hem considerat que totes ho son
    # nota2: he suposat que CodAMB és un identificador únic per a cada parada (poden haver parades diferents a pl cat per exemple)
    # nota3: afegir un node preexistent no en modifica les arestes, la llibreria ho ignora
    # nota4: ignorem les parades de fora de Barcelona
    # nota5: les subparades duna mateixa parada encara no estan unides entre si

    buses: BusesGraph = BusesGraph()

    linies = get_linies()  # llista de diccionaris

    for linia in linies:
        parades_linia = linia["Parades"][
            "Parada"
        ]  # llista de diccionaris (parades duna mateixa línia)

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


def show(g: BusesGraph) -> None:
    """shows the graph interactively using network.draw"""
    # nota: hi ha nodes no connexos pq pertanyen a linies dhospitalet, sant adria etc

    positions = nx.get_node_attributes(g, "coord")
    nx.draw(g, pos=positions, with_labels=False, node_size=10)
    plt.show()


def plot(g: BusesGraph, nom_fitxer: str) -> None:
    """saves the graph as an image with the map of the city in the background
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
