from typing import TypeAlias
import networkx as nx
import requests
from dataclasses import dataclass
from staticmap import StaticMap, CircleMarker, Line

import matplotlib.pyplot as plt


Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)
BusesGraph : TypeAlias = nx.Graph

URL = "https://www.ambmobilitat.cat/OpenData/ObtenirDadesAMB.json"


@dataclass (frozen = True)
class Parada:
    nom: str
    coord: Coord


def get_data_from_url():
    '''returns a dictionary of the buses data from the URL. The URL is a constant.'''
    response = requests.get(URL)
    assert response, "Error with URL"
    return response.json()


def get_linies():
    '''returns a list of bus lines'''
    data = get_data_from_url()
    data = data[list(data.keys())[0]]

    linies = data[list(data.keys())[1]]
    return linies[list(linies.keys())[0]] #llista de diccionaris

def get_weight():
    return 10

def get_buses_graph() -> BusesGraph:
    '''downloads the data of the AMB and returns an undirected graph of buses'''

    #nota: una linia comença i acaba amb la mateixa parada (pel que he vist en les tres primeres)
    #nota2: he suposat que CodAMB és un identificador únic per a cada parada (poden haver parades diferents a pl cat per exemple)
    #nota3: afegir un node preexistent no en modifica les arestes, la llibreria ho ignora
    #nota4: ignorem les parades de fora de Barcelona

    '''
    maneres d'implementar els nodes:
    - node: id, nom, codi, adreça, coordenades
    - node: id, Parada(elements que vulguem)
    - node: Parada() -> per crear les arestes hauríem de fer una llista amb les parades i anar-les connectant
    '''


    buses: BusesGraph = BusesGraph()

    linies = get_linies() #llista de diccionaris


    for linia in linies:
        parades_linia = linia['Parades']['Parada'] #llista de diccionaris (parades duna mateixa línia)

        for i, parada in enumerate(parades_linia):
            if parada['Municipi'] == 'Barcelona':

                buses.add_node(parada['CodAMB'], nom = parada['Nom'], coord = (parada['UTM_X'], parada['UTM_Y']))

                if i != 0 and parades_linia[i-1]['Municipi'] == 'Barcelona' and parada['CodAMB'] != parades_linia[i-1]['CodAMB']:
                    if (parada['CodAMB'], parades_linia[i-1]['CodAMB']) in buses.edges:
                        buses[parada['CodAMB']][parades_linia[i-1]['CodAMB']]['linies'].append(linia['Id'])
                    else:
                        buses.add_edge(parada['CodAMB'], parades_linia[i-1]['CodAMB'], linies = [linia['Id']], pes = get_weight())

    return buses


def show(g: BusesGraph) -> None:
    '''shows the graph interactively using network.draw'''
    #nota: hi ha nodes no connexos pq pertanyen a linies dhospitalet, sant adria etc

    positions = nx.get_node_attributes(g, "coord")

    #print(set(g.nodes) - {x[0] for x in g.edges} - {x[1] for x in g.edges}) nodes no connexos

    nx.draw(g, pos=positions, with_labels = False, node_size=10)
    plt.show()


def plot(g: BusesGraph, nom_fitxer: str) -> None:
    '''saves the graph as an image with the map of the city in the background
    in the file nom_fitxer using staticmaps'''
    url = "http://a.tile.osm.org/13/41.3968/2.1564.png"
    url_ = "http://a.tile.osm.org/{z}/{x}/{y}.png"
    url2 = "https://www.openstreetmap.org/relation/347950#map=13/41.3968/2.1564"

    map = StaticMap(500, 500, url_template = url_)

    #draw nodes
    for pos in nx.get_node_attributes(g, "coord").values():
        map.add_marker(CircleMarker(pos, 'green', 6))

    #draw edges
    for edge in g.edges:
        map.add_line(Line([g.nodes[edge[0]]['coord'], g.nodes[edge[1]]['coord']], 'blue', 3))

    image = map.render()
    image.save(nom_fitxer)


#show(get_buses_graph())
#print(nx.complete_graph(5).nodes)
#plot(get_buses_graph(), "hola.png")
