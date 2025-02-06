import networkx as nx
import geopandas as gpd
from shapely.geometry import LineString
from scipy.spatial import KDTree
import pickle
import os
import matplotlib.pyplot as plt

class RoadNetwork:
    def __init__(self, geo_series: gpd.GeoSeries = None, cache_dir="cache"):
        self.graph = nx.Graph()
        self.nodes = []
        self.kdtree = None
        self.cache_dir = cache_dir
        if geo_series is not None:
            self._build_graph(geo_series)
            self.kdtree = KDTree(self.nodes)
            self.save_to_cache()

    def _build_graph(self, geo_series: gpd.GeoSeries):
        for line in geo_series:
            if isinstance(line, LineString):
                coords = list(line.coords)
                self.nodes.extend(coords)
                for i in range(len(coords) - 1):
                    start = coords[i]
                    end = coords[i + 1]
                    distance = LineString([start, end]).length
                    self.graph.add_edge(start, end, weight=distance)

    def heuristic(self, n1, n2):
        # Using Euclidean distance as heuristic
        return LineString([n1, n2]).length

    def snap_to_network(self, point):
        distance, idx = self.kdtree.query(point)
        nearest_node = self.nodes[idx]
        return nearest_node

    def get_shortest_path(self, start_point, end_point):
        start_point = self.snap_to_network(start_point)
        end_point = self.snap_to_network(end_point)
        return nx.astar_path(self.graph, source=start_point, target=end_point, heuristic=self.heuristic, weight='weight')

    def save_to_cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(os.path.join(self.cache_dir, 'nodes.pkl'), 'wb') as f:
            pickle.dump(self.nodes, f)
        with open(os.path.join(self.cache_dir, 'edges.pkl'), 'wb') as f:
            pickle.dump(self.graph.edges(data=True), f)
        with open(os.path.join(self.cache_dir, 'kdtree.pkl'), 'wb') as f:
            pickle.dump(self.kdtree, f)

    def load_from_cache(self):
        with open(os.path.join(self.cache_dir, 'nodes.pkl'), 'rb') as f:
            self.nodes = pickle.load(f)
        with open(os.path.join(self.cache_dir, 'edges.pkl'), 'rb') as f:
            edges = pickle.load(f)
            self.graph.add_edges_from(edges)
        with open(os.path.join(self.cache_dir, 'kdtree.pkl'), 'rb') as f:
            self.kdtree = pickle.load(f)

def example():
    # Example usage:
    geo_series = gpd.GeoSeries([LineString([(0, 0), (1, 1), (2, 2)]), LineString([(2, 2), (3, 3)])])
    road_network = RoadNetwork(geo_series)
    shortest_path = road_network.get_shortest_path((0.5, 0.5), (3, 3))
    print(shortest_path)

    # Loading from cache
    road_network_cached = RoadNetwork()
    road_network_cached.load_from_cache()
    shortest_path_cached = road_network_cached.get_shortest_path((0.5, 0.5), (3, 3))
    print(shortest_path_cached)

def demo():
    # Demo usage using shapefile
    geo_series = gpd.read_file('data/gcs/road_network.shp')['geometry']
    road_network = RoadNetwork(geo_series)
    start_point = (-116.1264, 43.5984)
    end_point = (-116.1364, 43.5984)
    shortest_path = road_network.get_shortest_path(start_point, end_point)

    # Create a LineString from shortest_path
    shortest_path_line = LineString(shortest_path)
    
    # Plot the shortest path on the map
    fig, ax = plt.subplots()
    geo_series.plot(ax=ax)
    ax.plot(*shortest_path_line.xy, color='red')
    ax.scatter(*start_point, color='green')
    ax.scatter(*end_point, color='blue')
    plt.show()

if __name__ == "__main__":
    # example()
    demo()