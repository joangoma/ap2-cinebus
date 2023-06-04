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


OsmnxGraph: TypeAlias = nx.MultiDiGraph
CityGraph: TypeAlias = nx.Graph
Path: TypeAlias = tuple[list[T], int]

WALK_SPEED = 5  # km/h
BUS_SPEED = 15  # km/h

BUS_WAIT_TIME = 8.0  # minutes

FILE_OSMNX_NAME = "barcelona.grf"
FILE_CITY_NAME = "CITY_GRAPH"

"""
COORDINATES SYSTEMS

OSM -> 41, 2 lat - lon
BUSES -> 41, 2 UTM
haversine -> lat - lon
STATICMAP -> 2, 41 lon - lat
ox.distance.nearest_nodes -> 2, 41 lon - lat
"""


def delete_geometry(g: OsmnxGraph) -> None:
    '''Deletes the attribute geometry, as we are not interested
    and takes a lot of space.
    '''
    for u, v, key, geom in g.edges(data="geometry", keys=True):
        if geom is not None:
            del (g[u][v][key]["geometry"])


def get_osmnx_graph() -> OsmnxGraph:
    """Returns a graph of the streets of Barcelona. If it is in a file
    in the current directory, it is loaded. Otherwise it is downloaded from
    internet and saved in FILE_OSMNX_NAME.

    The graph returned has no geometry attribute nor self loops.
    """
    path = os.getcwd() + "\\" + FILE_OSMNX_NAME
    if os.path.exists(path):
        return load_graph(FILE_OSMNX_NAME)
    else:
        g: OsmnxGraph = ox.graph_from_place(
            "Barcelona", network_type="walk", simplify=True
        )

        delete_geometry(g)

        # there were self loops in g
        g.remove_edges_from(nx.selfloop_edges(g))

        save_graph(g, FILE_OSMNX_NAME)
        return g


def save_graph(g: OsmnxGraph | CityGraph, filename: str) -> None:
    """Saves graph g in file filename"""

    pickle_out = open(filename, "wb")
    pickle.dump(g, pickle_out)
    pickle_out.close()


def load_graph(filename: str) -> OsmnxGraph | CityGraph:
    """Returns the graph stored in file filename"""

    path = os.getcwd() + "\\" + FILE_OSMNX_NAME
    assert os.path.exists(path), f'Error: {filename} does not exist'

    pickle_in = open(filename, "rb")
    return pickle.load(pickle_in)


def join_stop_crosswalk(city, buses, cruilles) -> None:
    """Each stop is joined with the closest crosswalk. The
    type of the edges between them is "Carrer". The weight is also set.
    """

    parades = sorted(buses.nodes(data=True))
    X = [parada[1]["coord"][1] for parada in parades]
    Y = [parada[1]["coord"][0] for parada in parades]

    # ox.distance.nearest_nodes uses lon-lat, so we swap the coordinates
    nearest_cruilles = ox.distance.nearest_nodes(cruilles, X, Y,
                                                 return_dist=False)
    weights = [haversine(parada[1]["coord"], city.nodes[cruilla]["coord"])
               / WALK_SPEED * 60
               for parada, cruilla in zip(parades, nearest_cruilles)]

    city.add_weighted_edges_from(list(
                                      zip([parada[0] for parada in parades],
                                          nearest_cruilles, weights)
                                     ), type="Carrer")


def get_weight_buses(a, b, attr):
    """Used to estimate the time taken to go from one bus stop to another.

    Initially, the edges of type="Bus" have a weight=float('inf').
    When calculating the shortest path between stops, this path can
    go through:
    - "Carrers", whose weight is different because is the distance
    on foot
    - "Buses", whose weight is float('inf') (not processed yet) or
    a valid weight previously set that can be used
    """

    if attr["type"] == "Carrer":
        return attr["weight"] * WALK_SPEED / BUS_SPEED

    elif attr["type"] == "Bus":
        return attr["weight"]


def group_substops(city: CityGraph) -> dict[str, list[str]]:
    """Returns a dictionary where the keys are the stops and the values
    are the substops of that stop which correspond to each line"""

    parades: dict[str, list[str]] = {}
    for node in city.nodes(data=True):
        if node[1]["type"] == "Parada":
            parada = node[0].split("-")[0]
            if parada not in parades.keys():
                parades[parada] = [node[0]]
            else:
                parades[parada].append(node[0])

    return parades


def add_weights_buses(city: CityGraph) -> None:
    """The attribute weight of edges connecting stops is set.

    stop1-lineA and stop1-lineB edge has weight = BUS_WAIT_TIME
    stop1-lineA and stop2-lineA edge has weight = distance

    There is NO edge between stop1-lineA and stop2-lineB,
    although one can travel between them with the route:
    stop1-lineA -> stop1-lineB -> stop2-lineB or
    stop1-lineA -> stop2-lineA -> stop2-lineB
    """

    # add weight betwen stops of the same line
    for edge in city.edges(data=True):
        if edge[2]["type"] == "Bus":
            # we get the closest crosswalk to the stop (it is already found)
            # from all the edges of the stops is the only one of type Carrer
            cruilla1 = list(
                            filter(lambda edge_parada:
                                   edge_parada[2]["type"] == "Carrer",
                                   city.edges(edge[0], data=True)
                                   )
            )[0][1]
            cruilla2 = list(
                            filter(lambda edge_parada:
                                   edge_parada[2]["type"] == "Carrer",
                                   city.edges(edge[1], data=True),
                                   )
            )[0][1]

            city.edges[edge[0], edge[1]]["weight"] = nx.shortest_path_length(
                city, source=cruilla1, target=cruilla2, weight=get_weight_buses
            )

    # edges between substops of the same stop are added (weight=BUS_WAIT_TIME)
    # substops are grouped by stops
    parades: dict[str, list[str]] = group_substops(city)

    # an edge with weight = BUS_WAIT_TIME is added between every pair of
    # substops of the same stop
    for subparades in parades.values():
        city.add_edges_from(itertools.combinations(subparades, 2),
                            weight=BUS_WAIT_TIME, type="Transbord")


def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph:
    """If the citygraph is stored in FILE_CITY_NAME, it is loaded. Otherwise,
    g1 and g2 are merged to build a Citygraph and it is saved in FILE_CITY_NAME

    ------------------------
    Graph returned:
    - Types of nodes and edges are added
        nodes: "Cruilla" or "Parada"
        edges: "Carrer" or "Bus"

    - The nodes coordinates are in lat - lon format (the coordinates
    of nodes from osmnxgraph are swapped)
    - Every edge has a weight (the estimated time taken to travel it)
    - The edges of type="Carrer" have the attribute name or None
    - Each stop is connected to the closest crosswalk

    """

    path = os.getcwd() + "\\" + FILE_CITY_NAME
    if os.path.exists(path):
        return load_graph(FILE_CITY_NAME)

    city: CityGraph = CityGraph()

    # nodes g1:
    for node in g1.nodes(data=True):
        city.add_node(node[0], coord=(node[1]["y"], node[1]["x"]),
                      type="Cruilla")

    # nodes g2:
    city.add_nodes_from(g2.nodes(data=True), type="Parada")

    # edges g1 (weight is set):
    for edge in g1.edges(data=True):

        city.add_edge(edge[0], edge[1],
                      name=edge[2].get("name", None),
                      type="Carrer",
                      weight=haversine(city.nodes[edge[0]]["coord"],
                                       city.nodes[edge[1]]["coord"])
                      / WALK_SPEED * 60
                      )

    # edges g2:
    city.add_edges_from(g2.edges(data=True), type="Bus", weight=float("inf"))

    join_stop_crosswalk(city, g2, g1)

    add_weights_buses(city)

    save_graph(city, FILE_CITY_NAME)

    return city


def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:
    """Returns a tuple whose first element is a list of nodes ids from the
    shortest path from src to dst and the second element are the minutes taken.
    """

    # distance.nearest_nodes uses lon-lat coordinates, so we need to swap them
    cruilla_src, cruilla_dst = ox.distance.nearest_nodes(
        ox_g, [src[1], dst[1]], [src[0], dst[0]], return_dist=False
    )

    nodes_path: list[str] = nx.shortest_path(
        g, source=cruilla_src, target=cruilla_dst, weight="weight"
    )

    return (nodes_path, nx.path_weight(g, nodes_path, "weight"))


def show_city(g: CityGraph) -> None:
    """Shows the graph g interactively using network.draw"""

    positions = nx.get_node_attributes(g, "coord")
    nx.draw(g, pos=positions, with_labels=False, node_size=10)
    plt.show()


def plot_city(g: CityGraph, filename: str) -> None:
    """Saves the graph g as an image with the city map in the
    background in the file filename"""

    map = StaticMap(300, 300)

    # draw nodes
    for node in g.nodes(data=True):
        if node[1]["type"] == "Parada":
            color = "red"

        elif node[1]["type"] == "Cruilla":
            color = "blue"

        # we swap the components (staticmap works with lon-lat coordinates)
        map.add_marker(CircleMarker([node[1]["coord"][1], node[1]["coord"][0]],
                                    color, 3)
                       )
    # draw edges
    for edge in g.edges(data=True):
        if edge[2]["type"] == "Carrer":
            color = "orange"

        elif edge[2]["type"] == "Bus":
            color = "green"

        # we swap the components (staticmap works with lon-lat coordinates
        coord_1 = (g.nodes[edge[0]]["coord"][1], g.nodes[edge[0]]["coord"][0])
        coord_2 = (g.nodes[edge[1]]["coord"][1], g.nodes[edge[1]]["coord"][0])
        map.add_line(Line([coord_1, coord_2], color, 2))

    image = map.render()
    image.save(filename)


def get_colors_from_path(
        g: CityGraph, p: Path) -> dict[str, tuple[int, int, int]]:
    """Returns a dictionary with the colors of each bus line. The colors
    are set randomly."""

    # p[0] is a list
    linies = {g.nodes[node].get("linia", None) for node in p[0]}

    return {
        linia: (randint(0, 255), randint(0, 255), randint(0, 255))
        for linia in linies
        if linia is not None
    }


def plot_path(g: CityGraph, p: Path, filename: str, *args) -> None:
    '''Saves the path p as an image with the city map in the
    background in the file filename.

    The sections of the path that are on foot are blue.
    Each bus line is in a random color.
    '''

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

            # if one of the nodes is a crosswalk the user has to walk
            if node["type"] == "Cruilla" or prev_node["type"] == "Cruilla":
                color = "blue"
            else:
                color = colors_linies[node["linia"]]

            map.add_line(Line([coord_1, coord_2], color, 2))
    try:
        image = map.render()
        image.save(filename)
    except Exception:
        print("Could not render or save the image")
