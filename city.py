import networkx as nx
import osmnx as ox
from typing import TypeAlias, TypeVar
import os
import pickle
from buses import *

T = TypeVar("T")

OsmnxGraph : TypeAlias = nx.MultiDiGraph
CityGraph : TypeAlias = nx.Graph
Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)
Path: TypeAlias = list[T]

WALK_SPEED = 2
BUS_SPEED = 40

BUS_WAIT_TIME = 5 #minutes

FILE_GRAPH_NAME = "graph"

def delete_geometry_from_edges(g: OsmnxGraph) -> OsmnxGraph:
    for u, v, key, geom in g.edges(data = "geometry", keys = True):
        if geom is not None:
            del(g[u][v][key]["geometry"])


def get_only_first_edge(g: OsmnxGraph) -> OsmnxGraph:
    # for each node and its neighbours' information ...
    for u, nbrs_dict in g.adjacency():
        print(u, nbrsdict)
        # for each adjacent node v and its (u, v) edges' information ...
        for v, edges_dict in nbrsdict.items():
            print('   ', v)
            # osmnx graphs are multigraphs, but we will just consider their first edge
            e_attr = edges_dict[0]    # eattr contains the attributes of the first edge
            # we remove geometry information from eattr because we don't need it and take a lot of space
            if 'geometry' in e_attr:
                del(e_attr['geometry'])
            print('        ', e_attr)


def get_osmnx_graph() -> OsmnxGraph:
    '''returns a graph of the streets of Barcelona'''
    path = os.getcwd() + '\\' + FILE_GRAPH_NAME
    if os.path.exists(path):
        return load_osmnx_graph(FILE_GRAPH_NAME)
    else:
        g: OsmnxGraph = ox.graph_from_place("Barcelona", network_type='walk', simplify=True)

        #Si voleu eliminar aquesta informació de totes les arestes (potser abans de guardar el graf en un fitxer) podeu fer:
        delete_geometry_from_edges(g)
        get_only_first_edge(g)
        save_osmnx_graph(g, FILE_GRAPH_NAME)
        return g


def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
    '''Saves multigraph g in file {filename}'''

    pickle_out = open(filename, "wb")
    pickle.dump(g, pickle_out)
    pickle_out.close()


def load_osmnx_graph(filename: str) -> OsmnxGraph:
    '''Returns the multigraph stored in file filename'''

    pickle_in = open(filename, "rb")
    return pickle.load(pickle_in)


def join_parada_cruilla(city, buses, cruilles) -> None:
    '''each stop is joined with its closest crosswalk'''

    parades = sorted(buses.nodes(data = True))
    X = [parada[1]['coord'][0] for parada in parades] #(id, coord[0], coord[1])
    Y = [parada[1]['coord'][1] for parada in parades]

    city.add_edges_from(zip([parada[0] for parada in parades], ox.distance.nearest_nodes(cruilles, X, Y, return_dist=False)))


def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph:
    '''Merges g1 and g2 to build a Citygraph'''
    city: CityGraph = CityGraph() #ns si es pot escriure així

    #nodes g1:
    for node in g1.nodes(data = True):
        city.add_node(node[0], coord = (node[1]['y'], node[1]['x']), type = "Cruilla")
        #afegir atribut type = "Cruilla", canviar y x per una tupla coord,  #eliminar street count
        # {'y': 41.4259553, 'x': 2.1866781, 'street_count': 3}) -> format anterior

    #nodes g2:
    city.add_nodes_from(g2.nodes(data = True), type = "Parada")

    #arestes g1:
    for edge in g1.edges(data = True):
        if edge[0] != edge[1]: #hi havia loops a city
            city.add_edge(edge[0], edge[1], name = edge[2].get('name', None), type = "Carrer")

    #arestes g2:
    city.add_edges_from(g2.edges(data = True), type = "Bus") #conservem totes les dades

    join_parada_cruilla(city, g2, g1)

    return city


def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path: ...
    #path llista ordenada de nodes?

    #hem de guardar la linia de bus de la que venim per si cal fer transbord.

def show(g: CityGraph) -> None:
    # mostra g de forma interactiva en una finestra
    #shows the graph interactively using network.draw

    positions = nx.get_node_attributes(g, "coord")
    nx.draw(g, pos=positions, with_labels = False, node_size=10)
    plt.show()


def plot(g: CityGraph, filename: str) -> None:
    # desa g com una imatge amb el mapa de la cuitat de fons en l'arxiu filename
    map = StaticMap(300, 300)

    # draw nodes
    for node in g.nodes(data = True):
        if node[1]['type'] == "Parada":
            color = "red"

        elif node[1]['type'] == "Cruilla":
            color = "blue"

        map.add_marker(CircleMarker(g[1]['coord'], color, 3))

    # draw edges
    for edge in g.edges(data = True):
        if edge[2]['type'] == "Carrer":
            color = 'orange'

        elif edge[2]['type'] == "Bus":
            color = "green"

        #we swap the components
        coord_1 = (g.nodes[edge[0]]["coord"][1], g.nodes[edge[0]]["coord"][0])
        coord_2 = (g.nodes[edge[1]]["coord"][1], g.nodes[edge[1]]["coord"][0])
        map.add_line(Line([coord_1, coord_2], color, 2))

    image = map.render()
    image.save(nom_fitxer)


def plot_path(g: CityGraph, p: Path, filename: str, *args) -> None:
    pass
    # mostra el camí p en l'arxiu filename


show(build_city_graph(get_osmnx_graph(), get_buses_graph()))
