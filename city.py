import networkx as nx
import osmnx as ox
from typing import TypeAlias, TypeVar
import os
import pickle
from buses import *
import math
import heapq
from haversine import haversine
from random import randint
import itertools

T = TypeVar("T")

OsmnxGraph : TypeAlias = nx.MultiDiGraph
CityGraph : TypeAlias = nx.Graph
#Coord : TypeAlias = tuple[float, float]   # (latitude, longitude)
Path: TypeAlias = tuple[list[T], int]

WALK_SPEED = 5 #km/h
BUS_SPEED = 15 #km/h

BUS_WAIT_TIME = 8.0 #minutes

FILE_OSMNX_NAME = "OSMNX_GRAPH"
FILE_CITY_NAME = "CITY_GRAPH"


def get_only_first_edge_and_del_geometry(g: OsmnxGraph) -> OsmnxGraph:
    # for each node and its neighbours' information ...
    for u, nbrs_dict in g.adjacency():
        #print(u, nbrs_dict)
        # for each adjacent node v and its (u, v) edges' information ...
        for v, edges_dict in nbrs_dict.items():
            #print('   ', v)
            # osmnx graphs are multigraphs, but we will just consider their first edge
            e_attr = edges_dict[0]    # eattr contains the attributes of the first edge
            # we remove geometry information from eattr because we don't need it and take a lot of space
            if 'geometry' in e_attr:
                del(e_attr['geometry'])
            #print('        ', e_attr)

'''
OSM -> 41, 2 latitud y longitud
STATICMAP -> 2, 41 (LON- LAT)
BUSES -> 41, 2 UTM
ox.distance.nearest_nodes -> 2, 41 LON - LAT
'''

def get_osmnx_graph() -> OsmnxGraph:
    '''Returns a graph of the streets of Barcelona. Get_only_first_edge should be debugged'''
    path = os.getcwd() + '\\' + FILE_OSMNX_NAME
    if os.path.exists(path):
        return load_graph(FILE_OSMNX_NAME)
    else:
        g: OsmnxGraph = ox.graph_from_place("Barcelona", network_type='walk', simplify=True)

        get_only_first_edge_and_del_geometry(g)

        save_graph(g, FILE_OSMNX_NAME)
        return g


def save_graph(g: OsmnxGraph, filename: str) -> None:
    '''Saves multigraph g in file {filename}'''

    pickle_out = open(filename, "wb")
    pickle.dump(g, pickle_out)
    pickle_out.close()


def load_graph(filename: str) -> OsmnxGraph | CityGraph:
    '''Returns the multigraph stored in file filename'''

    pickle_in = open(filename, "rb")
    return pickle.load(pickle_in)


def join_parada_cruilla(city, buses, cruilles) -> None:
    '''Each stop is joined with the closest crosswalk. For simplicity, the type of the edges
    between them is Carrer. ox.distance.nearest_nodes uses lon-lat, so we swap the coordinates'''

    parades = sorted(buses.nodes(data = True))
    X = [parada[1]['coord'][1] for parada in parades] #(id, (coord[0], coord[1]))
    Y = [parada[1]['coord'][0] for parada in parades]

    city.add_edges_from(zip([parada[0] for parada in parades], ox.distance.nearest_nodes(cruilles, X, Y, return_dist=False)), type = "Carrer")


def get_weight(a, b, attr):
    return attr['weight'] * WALK_SPEED / BUS_SPEED


def add_weights(city: CityGraph) -> None:
    '''Per calcular la distancia entre parades necessito distancia entre cruilles'''
    for edge in city.edges(data = True):
        if edge[2]['type'] == 'Carrer':
            #haversine retorna distancia en km
            city.edges[edge[0], edge[1]]['weight'] = haversine(city.nodes[edge[0]]['coord'], city.nodes[edge[1]]['coord'])/WALK_SPEED*60

    for edge in city.edges(data = True):
        if edge[2]['type'] == 'Bus':
            #aconsegueixo la cruilla mes propera al bus (de tots els edges de la parada es lunic del tipus carrer)
            cruilla1 = list(filter(lambda edge_parada: edge_parada[2]['type'] == "Carrer", city.edges(edge[0], data = True)))[0][1]
            cruilla2 = list(filter(lambda edge_parada: edge_parada[2]['type'] == "Carrer", city.edges(edge[1], data = True)))[0][1]

            city.edges[edge[0], edge[1]]['weight'] = nx.shortest_path_length(city, source = cruilla1, target = cruilla2, weight= get_weight)


def split_parades(city, buses):
    '''
    NECESSITO SABER ELS WEIGHTS!!

    parada1-liniaA i parada1-liniaB tenen weight = delay
    parada1-liniaA i parada2-liniaA tenen weight = distancia


    NO hi ha una aresta entre parada1-liniaA i parada2-liniaB
    '''
    #creo una subparada per cada línia. Entre subparades a partir una mateixa parada el pes es el temps despera
    for parada in buses.nodes(data = True):
        subparades = [(str(parada[0]) + str(linia), {"nom": parada[1]['nom'], "linia": linia, "type": "Parada", "coord": parada[1]['coord']}) for linia in parada[1]['linies']]
        city.add_nodes_from(subparades)
        city.add_edges_from(itertools.combinations([subparada[0] for subparada in subparades], 2), weight = BUS_WAIT_TIME)


    #uneixo les parades d'una mateixa línia (ja tenien el weight definit)
    for edge in buses.edges(data = True):
        for linia in edge[2]['linies']:
            city.add_edge(str(edge[0]) + str(linia), str(edge[1]) + str(linia), weight = city.edges[edge[0], edge[1]]['weight'], type = "Bus")


    #uneixo cada subparada amb la cruilla mes propera (cada parada ja esta unida amb una cruilla)
    #nomes he de buscar l'edge de parada del tipus carrer
    for parada in buses.nodes(data = True):
        nearest_cruilla_edge = list(filter(lambda edge: edge[2]['type'] == "Carrer" , city.edges(parada[0], data = True)))[0]
        for linia in parada[1]['linies']:
            city.add_edge(nearest_cruilla_edge[1], str(parada[0]) + str(linia), weight = nearest_cruilla_edge[2]['weight'], type = "Carrer")


    #elimino les parades originals (nomes volem subparades per calcular paths)
    city.remove_nodes_from(buses.nodes)


def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph:
    '''Merges g1 and g2 to build a Citygraph.

    Types of nodes and edges are added (nodes: Cruilla/Parada, edges: Carrer/Bus).
    Coordinates of osmnxgraph nodes are swapped. We also ignore street count. {'y': 41.4259553, 'x': 2.1866781, 'street_count': 3}) -> format anterior

    '''
    city: CityGraph = CityGraph() #ns si es pot escriure així

    #nodes g1:
    for node in g1.nodes(data = True):
        city.add_node(node[0], coord = (node[1]['y'], node[1]['x']), type = "Cruilla")

    #nodes g2:
    city.add_nodes_from(g2.nodes(data = True), type = "Parada")

    #arestes g1:
    for edge in g1.edges(data = True):
        if edge[0] != edge[1]: #hi havia loops a city
            city.add_edge(edge[0], edge[1], name = edge[2].get('name', None), type = "Carrer", weight = float('inf'))

    #arestes g2:
    city.add_edges_from(g2.edges(data = True), type = "Bus", weight = float('inf')) #conservem totes les dades

    join_parada_cruilla(city, g2, g1)

    add_weights(city) #com mes valors poguem tenir precalculats millor

    split_parades(city, g2) #necessito els weights

    return city


def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:
    '''nota: ox.distance.nearest_nodes necessita coordenades girades
        shortest_path: If the source and target are both specified, return a single list of nodes in a shortest path from the source to the target.
    '''

    cruilla_src, cruilla_dst = ox.distance.nearest_nodes(ox_g, [src[1], dst[1]], [src[0], dst[0]], return_dist=False)

    #tots els edges tenen pes
    nodes_path: list[T] = nx.shortest_path(g, source = cruilla_src, target = cruilla_dst, weight = 'weight')

    return (nodes_path, nx.path_weight(g, nodes_path, 'weight'))


def show(g: CityGraph) -> None:
    '''mostra g de forma interactiva en una finestra
    shows the graph interactively using network.draw'''

    positions = nx.get_node_attributes(g, "coord")
    nx.draw(g, pos=positions, with_labels = False, node_size=10)
    plt.show()


def plot(g: CityGraph, filename: str) -> None:
    '''desa g com una imatge amb el mapa de la ciutat de fons en l'arxiu filename'''

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
    image.save(filename)


def get_colors_from_path(g, p: Path) -> dict[str|int, tuple[int, int, int]]:
    '''Returns a dictionary with the colors of each line. The colors are set randomly.'''

    linies = {g.nodes[node].get('linia', None) for node in p[0]} #p[0] es una llista

    return {linia: (randint(0, 255), randint(0,255), randint(0,255)) for linia in linies if linia is not None}


def plot_path(g: CityGraph, p: Path, filename: str, *args) -> None:

    map = StaticMap(300, 300)

    colors_linies: dict[str, tuple[int, int, int]] = get_colors_from_path(g, p)


    # draw nodes
    for i, node in enumerate(p[0]):

        if g.nodes[node]['type'] == "Parada":
            color = "red"

        elif g.nodes[node]['type'] == "Cruilla":
            color = "blue"

        map.add_marker(CircleMarker((g.nodes[node]['coord'][1], g.nodes[node]['coord'][0]), color, 3))

        if i != 0: #draw edges
            prev_node = p[0][i-1]

            coord_1 = (g.nodes[node]['coord'][1], g.nodes[node]['coord'][0])
            coord_2 = (g.nodes[prev_node]['coord'][1], g.nodes[prev_node]['coord'][0])


            #si un dels dos es cruilla s'ha d'anar a peu
            if g.nodes[node]['type'] == "Cruilla" or g.nodes[prev_node]['type'] == "Cruilla":
                color = "blue"
            else:
                color = colors_linies[g.nodes[node]['linia']]

            map.add_line(Line([coord_1, coord_2], color, 2))

    image = map.render()
    image.save(filename)


def pred_to_list(src, dst, pred):
    '''pred es dict de tuples'''
    nodes_and_linies = []
    dst = (dst, None)
    src = (src, None)

    while dst[0] != src[0]:
        nodes_and_linies.append(dst)
        dst = pred[dst[0]]

    nodes_and_linies.append(src)
    nodes_and_linies.reverse()
    print(nodes_and_linies)
    return nodes_and_linies


def find_path_delay_picat(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:
    '''requisits: els nodes de buses han de tenir una llista amb les parades
        nota: g.neigbors i nearest_nodes retornen només ids'''

    cruilla_src, cruilla_dst = ox.distance.nearest_nodes(ox_g, [src[1], dst[1]], [src[0], dst[0]], return_dist=False)

    cost = {node: float('inf') for node in g.nodes}
    cost[cruilla_src] = 0
    pred: dict[str | int, 'T'] = {}
    cuap: list[tuple[float, tuple[str | int, dict[str, 'T']], str | None]] = [] #(time, (id, attr), linia actual)
    used = {node: False for node in g.nodes}
    heapq.heappush(cuap, (0, (cruilla_src, g.nodes[cruilla_src]), None))

    while cuap:
        cost_v, v, linia_actual = heapq.heappop(cuap)

        if v[0] == cruilla_dst:
            return (pred_to_list(cruilla_src, cruilla_dst, pred), int(cost[cruilla_dst]))

        if v[1]['type'] == "Cruilla": #nomes cruilles pq he dexplorar totes les linies de les parades
            if used[v[0]]:
                continue
            used[v[0]] = True


        for nbor_id in g.neighbors(v[0]):
            nbor = g.nodes[nbor_id]
            edge = g.edges[v[0], nbor_id]

            if nbor['type'] == 'Cruilla' and cost[nbor_id] > cost[v[0]] + edge['weight']:
                cost[nbor_id] = cost[v[0]] + edge['weight']
                pred[nbor_id] = (v[0], None)
                heapq.heappush(cuap, (cost[nbor_id], (nbor_id, nbor), None))

            elif nbor['type'] == 'Parada': #this condition is not indispensable but perhaps in a future more types of nodes are added
                if linia_actual is None or linia_actual not in nbor['linies']: #sumo delay i exploro totes les linies
                    if cost[nbor_id] > cost[v[0]] + edge['weight'] + BUS_WAIT_TIME:
                        cost[nbor_id] = cost[v[0]] + edge['weight'] + BUS_WAIT_TIME
                        pred[nbor_id] = (v[0], linia_actual)

                        for linia in nbor['linies']: #he dexplorar la resta de linies
                            heapq.heappush(cuap, (cost[nbor_id], (nbor_id, nbor), linia))

                elif cost[nbor_id] > cost[v[0]] + edge['weight']:
                    cost[nbor_id] = cost[v[0]] + edge['weight']
                    pred[nbor_id] = (v[0], linia_actual)
                    heapq.heappush(cuap, (cost[nbor_id], (nbor_id, nbor), linia_actual))

    return (pred_to_list(cruilla_src, cruilla_dst, pred), int(cost[cruilla_dst]))


def plot_path_picat(g: CityGraph, p: Path, filename: str, *args) -> None:
    '''mostra el camí p en l'arxiu filename. desa g com una imatge amb el mapa de la ciutat de fons en l'arxiu filename'''

    map = StaticMap(300, 300)

    colors_linies: dict[str | int, tuple[int, int, int]] = get_colors_from_path(p)


    # draw nodes
    for i, (node, linia) in enumerate(p[0]):

        if g.nodes[node]['type'] == "Parada":
            color = "red"

        elif g.nodes[node]['type'] == "Cruilla":
            color = "blue"

        map.add_marker(CircleMarker((g.nodes[node]['coord'][1], g.nodes[node]['coord'][0]), color, 3))

        if i != 0: #draw edges
            prev_node = p[0][i-1][0]

            coord_1 = (g.nodes[node]['coord'][1], g.nodes[node]['coord'][0])
            coord_2 = (g.nodes[prev_node]['coord'][1], g.nodes[prev_node]['coord'][0])

            #si un dels dos es cruilla s'ha d'anar a peu

            if g.nodes[node]['type'] == "Cruilla" or g.nodes[prev_node]['type'] == "Cruilla":
                color = "blue"
            else:
                color = colors_linies[linia]


            map.add_line(Line([coord_1, coord_2], color, 2))

    image = map.render()
    image.save(filename)



'''
g = nx.Graph()
g.add_node(1, type="d")
g.add_node(2, type="ss")
g.add_edge(1,2)
g.add_node(3)
g.add_node(4)

nodes = [(i, {'nom' : "hola"}) for i in range(5)]
h = nx.Graph()
h.add_nodes_from(nodes)
h.add_edges_from(itertools.combinations([node[0] for node in nodes], 2), weight = 10)

print(h.edges(2, data = True))'''



osmx_g = get_osmnx_graph()
for node in osmx_g.nodes:
    print(type(node))
    break
city = build_city_graph(osmx_g, get_buses_graph())

plot_path(city, find_path(osmx_g, city, (41.37949301243075, 2.121040855869357), (41.360067, 2.138944)), "path_delay.png")

#find_path(get_osmnx_graph(), build_city_graph(get_osmnx_graph(), get_buses_graph()), (41.3860832,2.1627945), (41.4158589,2.1482698))
