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
    # guarda el graf g al fitxer filename

    pickle_out = open(filename, "wb")
    pickle.dump(g, pickle_out)
    pickle_out.close()


def load_osmnx_graph(filename: str) -> OsmnxGraph: # retorna el graf guardat al fitxer filename
    '''Create a graph from data in a .osm formatted XML file'''
    pickle_in = open(filename, "rb")
    return pickle.load(pickle_in)


def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph: ...
    g = 

def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path: ...


def show(g: CityGraph) -> None: ...
    # mostra g de forma interactiva en una finestra
def plot(g: CityGraph, filename: str) -> None: ...
    # desa g com una imatge amb el mapa de la cuitat de fons en l'arxiu filename

def plot_path(g: CityGraph, p: Path, filename: str, *args) -> None: ...
    # mostra el camí p en l'arxiu filename
