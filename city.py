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

FILE_GRAPH_NAME = "graph"


def get_osmnx_graph() -> OsmnxGraph:
    '''returns a graph of the streets of Barcelona'''
    path = os.getcwd() + '\\' + FILE_GRAPH_NAME
    if os.path.exists(path):
        return load_osmx_graph(FILE_GRAPH_NAME)
    else:
        g: OsmnxGraph = ox.graph_from_place("Barcelona", network_type='walk', simplify=True)
        save_osmnx_graph(g, FILE_GRAPH_NAME)
        return g


def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
    '''Saves g in file {filename}'''
    # guarda el graf g al fitxer filename

    pickle_out = open(filename, "wb")
    pickle.dump(g, pickle_out)
    pickle_out.close()


def load_osmnx_graph(filename: str) -> OsmnxGraph:
    '''Returns the graph stored in file filename'''
    pickle_in = open(filename, "rb")
    return pickle.load(pickle_in)


def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph:
    '''Merges g1 and g2 to build a citygraph'''
    city: CityGraph = CityGraph() #ns si es pot escriure així

    #manera de recorrer totes les arestes dun OsmnxGraph

    # for each node and its neighbours' information ...
    for u, nbrsdict in graph.adjacency():
        print(u, nbrsdict)
        # for each adjacent node v and its (u, v) edges' information ...
        for v, edgesdict in nbrsdict.items():
            print('   ', v)
            # osmnx graphs are multigraphs, but we will just consider their first edge
            eattr = edgesdict[0]    # eattr contains the attributes of the first edge
            # we remove geometry information from eattr because we don't need it and take a lot of space
            if 'geometry' in eattr:
                del(eattr['geometry'])
            print('        ', eattr)


    city.add_nodes_from(g1.nodes(data = True))
    city.add_nodes_from(g2.nodes(data = True))
    city.add_edges_from(g1.edges(data = True))
    city.add_edges_from(g2.edges(data = True))

    return city


def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path: ...
    #path llista ordenada de nodes?

def show(g: CityGraph) -> None: ...
    # mostra g de forma interactiva en una finestra

def plot(g: CityGraph, filename: str) -> None: ...
    # desa g com una imatge amb el mapa de la cuitat de fons en l'arxiu filename

def plot_path(g: CityGraph, p: Path, filename: str, *args) -> None: ...
    # mostra el camí p en l'arxiu filename

g = nx.Graph()
g.add_node(1)
g.add_node(2)
g.add_node(3)
g.add_edge(1,2)
g.add_edge(1,3)

for u, neighbors in g.adjacency():
    print(u, neighbors)

for u, neighbors in g.adj.items():
    print(u, neighbors)
