from typing import TypeAlias
import networkx
import requests, json



BusesGraph : TypeAlias = networkx.Graph

def get_buses_graph() -> BusesGraph:
    '''downloads the data of the AMB and returns an undirected graph'''
    #graf

    #aresta entre parades adjacents duna mateixa línia
        #atributs: linia
    #nodes són parades
        #atributs: nom, coordenades

    buses: BusesGraph = BusesGraph()

    content = requests.get("https://www.ambmobilitat.cat/OpenData/ObtenirDadesAMB.json")
    jason = json.loads(content.content)


    #buses.add_nodes_from([llista])

    
    return buses

def show(g: BusesGraph) -> None:
    '''shows the graph interactively using network.draw'''
    networkx.draw(g)


def plot(g: BusesGraph, nom_fitxer: str) -> None:
    '''saves the graph as an image with the map of the city in the background
    in the filed nom_fitxer using staticmaps'''

get_buses_graph()
