import networkx as nx
import osmnx as ox
from typing import TypeAlias
import os
from buses import *


OsmnxGraph : TypeAlias = nx.MultiDiGraph
CityGraph : TypeAlias = nx.Graph
Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)

WALK_SPEED = 2
BUS_SPEED = 40


print(os.getcwd())

def get_osmnx_graph() -> OsmnxGraph:
    '''returns a graph of the streets of Barcelona'''
    if os.path.exists(os.getcwd()+"graph"):
        pass
    graph: OsmnxGraph = ox.graph_from_place("Barcelona", network_type='walk', simplify=True)

    return graph

def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
    ...
    # guarda el graf g al fitxer filename


def load_osmnx_graph(filename: str) -> OsmnxGraph:
    ...
    # retorna el graf guardat al fitxer filename

def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph: ...
    # retorna un graf fusió de g1 i g2

def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path: ...


def show(g: CityGraph) -> None: ...
    # mostra g de forma interactiva en una finestra
def plot(g: CityGraph, filename: str) -> None: ...
    # desa g com una imatge amb el mapa de la cuitat de fons en l'arxiu filename

#def plot_path(g: CityGraph, p: Path, filename: str, ...) -> None: ...
    # mostra el camí p en l'arxiu filename
