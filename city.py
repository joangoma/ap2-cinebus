import math
import os
import pickle
from typing import TypeAlias, TypeVar

import networkx as nx
import osmnx as ox
from haversine import haversine

from buses import *

T = TypeVar("T")

OsmnxGraph: TypeAlias = nx.MultiDiGraph
CityGraph: TypeAlias = nx.Graph
Path: TypeAlias = tuple[list[T], int]

WALK_SPEED = 2  # km/h
BUS_SPEED = 40  # km/h

BUS_WAIT_TIME = 5  # minutes

FILE_GRAPH_NAME = "graph"


def delete_geometry_from_edges(g: OsmnxGraph) -> OsmnxGraph:
    for u, v, key, geom in g.edges(data="geometry", keys=True):
        if geom is not None:
            del g[u][v][key]["geometry"]


def get_only_first_edge_and_del_geometry(g: OsmnxGraph) -> OsmnxGraph:
    # for each node and its neighbours' information ...
    for u, nbrs_dict in g.adjacency():
        # print(u, nbrs_dict)
        # for each adjacent node v and its (u, v) edges' information ...
        for v, edges_dict in nbrs_dict.items():
            # print('   ', v)
            # osmnx graphs are multigraphs, but we will just consider their first edge
            e_attr = edges_dict[0]  # eattr contains the attributes of the first edge
            # we remove geometry information from eattr because we don't need it and take a lot of space
            if "geometry" in e_attr:
                del e_attr["geometry"]
            # print('        ', e_attr)


"""
OSM -> 41, 2 latitud y longitud
STATICMAP -> 2, 41 (LON- LAT)
BUSES -> 41, 2 UTM
ox.distance.nearest_nodes -> 2, 41 LON - LAT
"""


def get_osmnx_graph() -> OsmnxGraph:
    """returns a graph of the streets of Barcelona"""
    path = os.getcwd() + "\\" + FILE_GRAPH_NAME
    if os.path.exists(path):
        return load_osmnx_graph(FILE_GRAPH_NAME)
    else:
        g: OsmnxGraph = ox.graph_from_place(
            "Barcelona", network_type="walk", simplify=True
        )

        # Si voleu eliminar aquesta informació de totes les arestes (potser abans de guardar el graf en un fitxer) podeu fer:
        # delete_geometry_from_edges(g)
        for edge in g.edges:
            print(edge)
            break

        get_only_first_edge_and_del_geometry(g)
        for edge in g.edges:
            print(edge)
            break
        save_osmnx_graph(g, FILE_GRAPH_NAME)
        return g


def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
    """Saves multigraph g in file {filename}"""

    pickle_out = open(filename, "wb")
    pickle.dump(g, pickle_out)
    pickle_out.close()


def load_osmnx_graph(filename: str) -> OsmnxGraph:
    """Returns the multigraph stored in file filename"""

    pickle_in = open(filename, "rb")
    return pickle.load(pickle_in)


def join_parada_cruilla(city, buses, cruilles) -> None:
    """each stop is joined with the closest crosswalk"""

    parades = sorted(buses.nodes(data=True))
    X = [parada[1]["coord"][1] for parada in parades]  # (id, coord[0], coord[1])
    Y = [parada[1]["coord"][0] for parada in parades]

    # no tinc molt clar que el type sigui carrer, li podríem dir enllaç
    city.add_edges_from(
        zip(
            [parada[0] for parada in parades],
            ox.distance.nearest_nodes(cruilles, X, Y, return_dist=False),
        ),
        type="Carrer",
    )


def get_weight(a, b, attributes):
    """returns the minutes to travel between to adjacent nodes"""

    dist = haversine(a["coord"], b["coord"])  # km

    # print(a, b, attributes)

    if attributes["type"] == "Carrer":  # un carrer es travessa en línia recta
        return dist / WALK_SPEED * 60

    elif attributes["type"] == "Bus":  # fem rotacio de 45º i calculem norma manhattan
        """
        1/sqrt(2)  - 1/sqrt(2)
        1/sqrt(2)   1/sqrt(2)
        """
        a_x_rotat, a_y_rotat = 1 / math.sqrt(2) * (
            a["coord"][0] - a["coord"][1]
        ), 1 / math.sqrt(2) * (a["coord"][0] + a["coord"][1])
        b_x_rotat, b_y_rotat = 1 / math.sqrt(2) * (
            b["coord"][0] - b["coord"][1]
        ), 1 / math.sqrt(2) * (b["coord"][0] + b["coord"][1])

        return (
            (abs(a_x_rotat - b_x_rotat) + abs(a_y_rotat - b_y_rotat)) / BUS_SPEED * 60
        )


def add_weights(city: CityGraph):
    for edge in city.edges(data=True):
        edge[2]["weight"] = get_weight(
            city.nodes[edge[0]], city.nodes[edge[1]], edge[2]
        )


def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph:
    """Merges g1 and g2 to build a Citygraph"""
    city: CityGraph = CityGraph()  # ns si es pot escriure així

    # nodes g1:
    for node in g1.nodes(data=True):
        city.add_node(node[0], coord=(node[1]["y"], node[1]["x"]), type="Cruilla")
        # afegir atribut type = "Cruilla", canviar y x per una tupla coord,  #eliminar street count
        # {'y': 41.4259553, 'x': 2.1866781, 'street_count': 3}) -> format anterior

    # nodes g2:
    city.add_nodes_from(g2.nodes(data=True), type="Parada")

    # arestes g1:
    for edge in g1.edges(data=True):
        if edge[0] != edge[1]:  # hi havia loops a city
            city.add_edge(
                edge[0], edge[1], name=edge[2].get("name", None), type="Carrer"
            )

    # arestes g2:
    city.add_edges_from(g2.edges(data=True), type="Bus")  # conservem totes les dades

    join_parada_cruilla(city, g2, g1)

    add_weights(city)

    return city


def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:
    # path llista ordenada de nodes?

    # ox.distance.nearest_nodes necessita coordenades girades
    cruilla_src, cruilla_dst = ox.distance.nearest_nodes(
        ox_g, [src[1], dst[1]], [src[0], dst[0]], return_dist=False
    )
    # nodes_path: list[T] = nx.shortest_path(g, source = cruilla_src, target = cruilla_dst, weight = get_weight)
    nodes_path: list[T] = nx.shortest_path(
        g, source=cruilla_src, target=cruilla_dst, weight="weight"
    )

    # print((nodes_path, nx.path_weight(g, nodes_path, 'weight')))
    return (nodes_path, nx.path_weight(g, nodes_path, "weight"))
    # If the source and target are both specified, return a single list of nodes in a shortest path from the source to the target.

    # plot cruilles i posicio original
    """
    h = nx.Graph()
    print(cruilles)
    print(g.nodes[cruilles[0]])
    h.add_nodes_from([(cruilles[0], g.nodes[cruilles[0]]), (cruilles[1], g.nodes[cruilles[1]])])
    h.add_node(1, coord = src)
    h.add_node(2, coord = dst)

    positions = nx.get_node_attributes(h, "coord")
    nx.draw(h, pos=positions, with_labels = False, node_size=10)
    plt.show()"""

    # hem de guardar la linia de bus de la que venim per si cal fer transbord.


def show(g: CityGraph) -> None:
    # mostra g de forma interactiva en una finestra
    # shows the graph interactively using network.draw

    positions = nx.get_node_attributes(g, "coord")
    nx.draw(g, pos=positions, with_labels=False, node_size=10)
    plt.show()


def plot(g: CityGraph, filename: str) -> None:
    # desa g com una imatge amb el mapa de la cuitat de fons en l'arxiu filename
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

        # we swap the components
        coord_1 = (g.nodes[edge[0]]["coord"][1], g.nodes[edge[0]]["coord"][0])
        coord_2 = (g.nodes[edge[1]]["coord"][1], g.nodes[edge[1]]["coord"][0])
        map.add_line(Line([coord_1, coord_2], color, 2))

    image = map.render()
    image.save(nom_fitxer)


def plot_path(g: CityGraph, p: Path, filename: str, *args) -> None:
    # desa g com una imatge amb el mapa de la ciutat de fons en l'arxiu filename
    map = StaticMap(300, 300)

    # draw nodes
    for i, node in enumerate(p[0]):
        print(g.nodes[node])

        if g.nodes[node]["type"] == "Parada":
            color = "red"

        elif g.nodes[node]["type"] == "Cruilla":
            color = "blue"

        map.add_marker(
            CircleMarker(
                (g.nodes[node]["coord"][1], g.nodes[node]["coord"][0]), color, 3
            )
        )

        if i != 0:
            coord_1 = (g.nodes[node]["coord"][1], g.nodes[node]["coord"][0])
            coord_2 = (
                g.nodes[p[0][i - 1]]["coord"][1],
                g.nodes[p[0][i - 1]]["coord"][0],
            )
            map.add_line(Line([coord_1, coord_2], "red", 2))

    image = map.render()
    image.save(filename)
    # mostra el camí p en l'arxiu filename


#osmx_g = get_osmnx_graph()
#city = build_city_graph(osmx_g, get_buses_graph())

#plot_path(city, find_path(osmx_g, city, (41, 2), (42, 2.5)), "hola.png")

# find_path(get_osmnx_graph(), build_city_graph(get_osmnx_graph(), get_buses_graph()), (41.3860832,2.1627945), (41.4158589,2.1482698))
