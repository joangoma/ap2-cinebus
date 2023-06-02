import heapq
import itertools
import math
import os
import pickle
from random import randint
from typing import TypeAlias, TypeVar

import networkx as nx
import osmnx as ox
from haversine import haversine

from buses import *

T = TypeVar("T")

OsmnxGraph: TypeAlias = nx.MultiDiGraph
CityGraph: TypeAlias = nx.Graph
# Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)
Path: TypeAlias = tuple[list[T], int]

WALK_SPEED = 5  # km/h
BUS_SPEED = 15  # km/h

BUS_WAIT_TIME = 8.0  # minutes

FILE_OSMNX_NAME = "OSMNX_GRAPH"
FILE_CITY_NAME = "CITY_GRAPH"

"""
OSM -> 41, 2 latitud y longitud
STATICMAP -> 2, 41 (LON- LAT)
BUSES -> 41, 2 UTM
ox.distance.nearest_nodes -> 2, 41 LON - LAT
"""


def get_only_first_edge_and_del_geometry(g: OsmnxGraph) -> OsmnxGraph:
    # for each node and its neighbours' information ...
    for u, nbrs_dict in g.adjacency():
        # print(u, nbrs_dict)
        # for each adjacent node v and its (u, v) edges' information ...
        for v, edges_dict in nbrs_dict.items():
            # print('   ', v)
            # ox graphs are multigraphs but we just consider their first edge
            e_attr = edges_dict[0]  # eattr contains attrib of the first edge
            # geometry information is unnecessary and takes a lot of space
            if "geometry" in e_attr:
                del e_attr["geometry"]
            # print('        ', e_attr)


def get_osmnx_graph() -> OsmnxGraph:
    """Returns a graph of the streets of Barcelona.
    Get_only_first_edge should be tested"""
    path = os.getcwd() + "\\" + FILE_OSMNX_NAME
    if os.path.exists(path):
        return load_graph(FILE_OSMNX_NAME)
    else:
        g: OsmnxGraph = ox.graph_from_place(
            "Barcelona", network_type="walk", simplify=True
        )

        get_only_first_edge_and_del_geometry(g)

        save_graph(g, FILE_OSMNX_NAME)
        return g


def save_graph(g: OsmnxGraph | CityGraph, filename: str) -> None:
    """Saves graph g in file {filename}"""

    pickle_out = open(filename, "wb")
    pickle.dump(g, pickle_out)
    pickle_out.close()


def load_graph(filename: str) -> OsmnxGraph | CityGraph:
    """Returns the graph stored in file filename"""

    pickle_in = open(filename, "rb")
    return pickle.load(pickle_in)


def join_parada_cruilla(city, buses, cruilles) -> None:
    """Each stop is joined with the closest crosswalk. For simplicity, the
    type of the edges between them is Carrer. ox.distance.nearest_nodes uses
    lon-lat, so we swap the coordinates
    """

    parades = sorted(buses.nodes(data=True))
    X = [parada[1]["coord"][1] for parada in parades]
    Y = [parada[1]["coord"][0] for parada in parades]

    city.add_edges_from(
        zip(
            [parada[0] for parada in parades],
            ox.distance.nearest_nodes(cruilles, X, Y, return_dist=False),
        ),
        type="Carrer",
    )


def get_weight(a, b, attr):
    """Used to estimate the time taken to go from one bus stop to another."""
    return attr["weight"] * WALK_SPEED / BUS_SPEED


def add_weights(city: CityGraph) -> None:
    """The attribute weight of each edge is set.

    parada1-liniaA i parada1-liniaB tenen weight = delay
    parada1-liniaA i parada2-liniaA tenen weight = distancia

    NO hi ha una aresta entre parada1-liniaA i parada2-liniaB

    Primer es calculen els pesos dels carrers ja que es necessiten per
    calcular els pesos dels busos
    """

    # Per calcular dist entre parades es necessita dist entre cruilles
    for edge in city.edges(data=True):
        if edge[2]["type"] == "Carrer":
            # haversine returns the distance in km
            city.edges[edge[0], edge[1]]["weight"] = (
                haversine(city.nodes[edge[0]]["coord"],
                          city.nodes[edge[1]]["coord"]) / WALK_SPEED * 60
            )

    # add weight betwen stops of the same line
    for edge in city.edges(data=True):
        if edge[2]["type"] == "Bus":
            # we get the closest crosswalk to the stop (it was previously found)
            #from all the edges of the stops is the only one of type Carrer
            cruilla1 = list(
                filter(
                    lambda edge_parada: edge_parada[2]["type"] == "Carrer",
                    city.edges(edge[0], data=True),
                )
            )[0][1]
            cruilla2 = list(
                filter(
                    lambda edge_parada: edge_parada[2]["type"] == "Carrer",
                    city.edges(edge[1], data=True),
                )
            )[0][1]

            city.edges[edge[0], edge[1]]["weight"] = nx.shortest_path_length(
                city, source=cruilla1, target=cruilla2, weight=get_weight
            )

    # edges between substops of a same stop are added with weight = delay
    parades: dict[str, list[str]] = {}  # substops are grouped by stops
    for node in city.nodes(data=True):
        if node[1]["type"] == "Parada":
            parada = node[0].split("-")[0]
            if parada not in parades.keys():
                parades[parada] = [node[0]]
            else:
                parades[parada].append(node[0])

    for subparades in parades.values():
        city.add_edges_from(itertools.combinations(subparades, 2),
                            weight=BUS_WAIT_TIME)


def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph:
    """If the citygraph is stored in FILE_CITY_NAME, it is loaded. Otherwise,
    g1 and g2 are merged to build a Citygraph and it is saved in FILE_CITY_NAME

    Types of nodes and edges are added
    (nodes: Cruilla/Parada, edges: Carrer/Bus)
    Coordinates of osmnxgraph nodes are swapped. We also ignore street count.
    {'y': 41.4259553, 'x': 2.1866781, 'street_count': 3}) -> format anterior
    """

    path = os.getcwd() + "\\" + FILE_CITY_NAME
    if os.path.exists(path):
        return load_graph(FILE_CITY_NAME)

    city: CityGraph = CityGraph()  # ns si es pot escriure així

    # nodes g1:
    for node in g1.nodes(data=True):
        city.add_node(node[0], coord=(node[1]["y"], node[1]["x"]),
                      type="Cruilla")

    # nodes g2:
    city.add_nodes_from(g2.nodes(data=True), type="Parada")

    # edges g1:
    for edge in g1.edges(data=True):
        if edge[0] != edge[1]:  # there were loops in city
            city.add_edge(
                edge[0],
                edge[1],
                name=edge[2].get("name", None),
                type="Carrer",
                weight=float("inf"),
            )

    # edges g2:
    city.add_edges_from(
        g2.edges(data=True), type="Bus", weight=float("inf")
    )  # conservem totes les dades

    join_parada_cruilla(city, g2, g1)

    # PODRIEM AFEGIR EL WEIGHT DELS CARRERS QUAN AFEGIM ELS EDGES I Q LA FUNCIO ES DIGUI ADD_WEIGHTS_BUSES
    add_weights(city)  # com mes valors poguem tenir precalculats millor

    save_graph(city, FILE_CITY_NAME)

    return city


def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:
    """Returns a tuple with the list of nodes ids of the shortest path from
    src to dst and the minutes it takes.

    shortest_path: If the source and target are both specified, returns
     a single list of nodes in a shortest path from the source to the target.
    """
    # distance.nearest_nodes uses lon-lat coordinates, so we need to swap them
    cruilla_src, cruilla_dst = ox.distance.nearest_nodes(
        ox_g, [src[1], dst[1]], [src[0], dst[0]], return_dist=False
    )

    nodes_path: list[str] = nx.shortest_path(
        g, source=cruilla_src, target=cruilla_dst, weight="weight"
    )

    return (nodes_path, nx.path_weight(g, nodes_path, "weight"))


def show(g: CityGraph) -> None:
    """Shows the graph g interactively using network.draw"""

    positions = nx.get_node_attributes(g, "coord")
    nx.draw(g, pos=positions, with_labels=False, node_size=10)
    plt.show()


def plot(g: CityGraph, filename: str) -> None:
    """Saves the graph g as an image with the city map in the
    background in the file filename"""

    map = StaticMap(300, 300)

    # draw nodes
    for node in g.nodes(data=True):
        if node[1]["type"] == "Parada":
            color = "red"

        elif node[1]["type"] == "Cruilla":
            color = "blue"

        map.add_marker(CircleMarker(g[1]["coord"], color, 3))

    # draw edges
    for edge in g.edges(data=True):
        if edge[2]["type"] == "Carrer":
            color = "orange"

        elif edge[2]["type"] == "Bus":
            color = "green"

        # we swap the components (staticmap works  with lon-lat coordinates
        coord_1 = (g.nodes[edge[0]]["coord"][1], g.nodes[edge[0]]["coord"][0])
        coord_2 = (g.nodes[edge[1]]["coord"][1], g.nodes[edge[1]]["coord"][0])
        map.add_line(Line([coord_1, coord_2], color, 2))

    image = map.render()
    image.save(filename)


def get_colors_from_path(g: CityGraph, p: Path) -> dict[str | int, tuple[int, int, int]]:
    """Returns a dictionary with the colors of each line. The colors
    are set randomly."""

    # p[0] is a list
    linies = {g.nodes[node].get("linia", None) for node in p[0]}

    return {
        linia: (randint(0, 255), randint(0, 255), randint(0, 255))
        for linia in linies
        if linia is not None
    }


def plot_path(g: CityGraph, p: Path, filename: str, *args) -> None:
    map = StaticMap(300, 300)

    colors_linies: dict[str, tuple[int, int, int]] = get_colors_from_path(g, p)

    # draw nodes
    for i, id_node in enumerate(p[0]):
        node = g.nodes[id_node]  # dict with attributes
        if node["type"] == "Parada":
            color = "red"

        elif node["type"] == "Cruilla":
            color = "blue"

        map.add_marker(CircleMarker((node["coord"][1], node["coord"][0]),
                                    color, 3))

        if i != 0:  # draw edges
            prev_node = g.nodes[p[0][i - 1]]

            coord_1 = (node["coord"][1], node["coord"][0])
            coord_2 = (prev_node["coord"][1], prev_node["coord"][0])

            # if one of the nodes is a crosswalk -> walk -> color blau
            if node["type"] == "Cruilla" or prev_node["type"] == "Cruilla":
                color = "blue"
            else:
                color = colors_linies[node["linia"]]

            map.add_line(Line([coord_1, coord_2], color, 2))

    image = map.render()
    image.save(filename)


osmx_g = get_osmnx_graph()

city = build_city_graph(osmx_g, get_buses_graph())

plot_path(
    city,
    find_path(
        osmx_g, city, (41.3794930124305, 2.121040855869), (41.360067, 2.138944)
    ),
    "path_delay.png",
)
