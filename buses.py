from typing import TypeAlias
import networkx as nx
import requests
from dataclasses import dataclass
from staticmap import StaticMap, CircleMarker

import matplotlib as plt


Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)
BusesGraph : TypeAlias = nx.Graph

URL = "https://www.ambmobilitat.cat/OpenData/ObtenirDadesAMB.json"

@dataclass
class Parada:
    nom: str
    coord: Coord


def get_data():
    response = requests.get(URL)
    assert response, "Error with URL"
    return response.json()


def get_linies() -> list[dict[str, str | float]]:
        data = get_data()
        data = data[list(data.keys())[0]]

        linies = data[list(data.keys())[1]]
        return linies[list(linies.keys())[0]] #llista de diccionaris


def get_buses_graph() -> BusesGraph:
    '''downloads the data of the AMB and returns an undirected graph of buses'''

    buses: BusesGraph = BusesGraph()

    linies: list[dict[str, str | float]] = get_linies() #llista amb


    for linia in linies:
        parades_linia = linia['Parades']['Parada'] #llista de diccionaris (parades duna mateixa línia)

        for i, parada in enumerate(parades_linia):
            if parada['Municipi'] == 'Barcelona':
                print(type(parada['Nom']))
                #ignora si ja existien
                buses.add_node(parada['Nom'], parada= Parada(parada['Nom'], (parada['UTM_X'], parada['UTM_Y'])))
                buses.add_edge(parada['Nom'], parades_linia[i-1])

                break
            else:
                break
        print(buses.nodes)
            #afegir aresta ultim - primer

            #node = (id, {"nom": nom, "coord": coord})

    return buses


def show(g: BusesGraph) -> None:
    '''shows the graph interactively using network.draw'''
    nx.draw(g)
    print("f")


def plot(g: BusesGraph, nom_fitxer: str) -> None:
    '''saves the graph as an image with the map of the city in the background
    in the file nom_fitxer using staticmaps'''
    m = StaticMap(200, 200, url_template="https://www.openstreetmap.org/relation/347950#map=13/41.3968/2.1564")
    marker_outline = CircleMarker((10, 47), 'white', 18)
    marker = CircleMarker((10, 47), '#0036FF', 12)

    m.add_marker(marker_outline)
    m.add_marker(marker)

    image = m.render(zoom=5)
    image.save('marker.png')

#print(nx.complete_graph(5).nodes)
get_buses_graph()
#show(nx.petersen_graph())
