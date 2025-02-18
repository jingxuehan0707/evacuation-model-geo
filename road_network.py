import networkx as nx
import geopandas as gpd
from shapely.geometry import LineString, Point
from scipy.spatial import KDTree
import pickle
import os
import matplotlib.pyplot as plt
import logging
import time

# Set up logging
log_dir = "log"
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(filename=os.path.join(log_dir, 'road_network.log'), level=logging.WARNING,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Set matplotlib logger to WARNING level to ignore debug messages
matplotlib_logger = logging.getLogger('matplotlib')
matplotlib_logger.setLevel(logging.WARNING)

class RoadNetwork:
    def __init__(self, geo_series: gpd.GeoSeries = None, cache_dir="cache", use_cache=True):
        self.graph = nx.Graph()
        self.nodes = []
        self.kdtree = None
        self.cache_dir = cache_dir
        self.use_cache = use_cache
        self.shortest_paths = {}
        
        if use_cache and self._cache_exists():
            self.load_from_cache()
        elif geo_series is not None:
            self.clear_cache()
            self._build_graph(geo_series)
            self.kdtree = KDTree(self.nodes)
            self.save_to_cache()

    def _cache_exists(self):
        return (os.path.exists(os.path.join(self.cache_dir, 'nodes.pkl')) and
                os.path.exists(os.path.join(self.cache_dir, 'edges.pkl')) and
                os.path.exists(os.path.join(self.cache_dir, 'kdtree.pkl')) and
                os.path.exists(os.path.join(self.cache_dir, 'shortest_paths.pkl')))

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
        logging.debug(f"Calculating shortest path from {start_point} to {end_point}")
        start_point = self.snap_to_network(start_point)
        end_point = self.snap_to_network(end_point)
        path_key = (start_point, end_point)
        
        # Check if the path is already cached
        if path_key in self.shortest_paths:
            logging.debug(f"Path retrieved from cache: {path_key}")
            return self.shortest_paths[path_key]
        
        # Calculate the path if not cached
        try:
            path = nx.astar_path(self.graph, source=start_point, target=end_point, heuristic=self.heuristic, weight='weight')
            self.shortest_paths[path_key] = path
            
            logging.debug(f"Path calculated and cached: {path_key}")
                
            return path
        except nx.NetworkXNoPath as e:
            logging.warning(f"No path found from {start_point} to {end_point}: {e}")
            return []
        except Exception as e:
            logging.warning(f"An error occurred while calculating the shortest path: {e}")
            return []

    def save_to_cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(os.path.join(self.cache_dir, 'nodes.pkl'), 'wb') as f:
            pickle.dump(self.nodes, f)
        with open(os.path.join(self.cache_dir, 'edges.pkl'), 'wb') as f:
            pickle.dump(self.graph.edges(data=True), f)
        with open(os.path.join(self.cache_dir, 'kdtree.pkl'), 'wb') as f:
            pickle.dump(self.kdtree, f)

    def save_shortest_paths_cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(os.path.join(self.cache_dir, 'shortest_paths.pkl'), 'wb') as f:
            pickle.dump(self.shortest_paths, f)

    def load_from_cache(self):
        with open(os.path.join(self.cache_dir, 'nodes.pkl'), 'rb') as f:
            self.nodes = pickle.load(f)
        with open(os.path.join(self.cache_dir, 'edges.pkl'), 'rb') as f:
            edges = pickle.load(f)
            self.graph.add_edges_from(edges)
        with open(os.path.join(self.cache_dir, 'kdtree.pkl'), 'rb') as f:
            self.kdtree = pickle.load(f)
        with open(os.path.join(self.cache_dir, 'shortest_paths.pkl'), 'rb') as f:
            self.shortest_paths = pickle.load(f)

    def clear_cache(self):
        if os.path.exists(os.path.join(self.cache_dir, 'nodes.pkl')):
            os.remove(os.path.join(self.cache_dir, 'nodes.pkl'))
        if os.path.exists(os.path.join(self.cache_dir, 'edges.pkl')):
            os.remove(os.path.join(self.cache_dir, 'edges.pkl'))
        if os.path.exists(os.path.join(self.cache_dir, 'kdtree.pkl')):
            os.remove(os.path.join(self.cache_dir, 'kdtree.pkl'))
        if os.path.exists(os.path.join(self.cache_dir, 'shortest_paths.pkl')):
            os.remove(os.path.join(self.cache_dir, 'shortest_paths.pkl'))

    def batch_calculate_shortest_paths(self, start_points, end_points):
        for start_point in start_points:
            for end_point in end_points:
                self.get_shortest_path((start_point.x, start_point.y), (end_point.x, end_point.y))
        self.save_shortest_paths_cache()

def example():
    # Example usage:
    geo_series = gpd.GeoSeries([LineString([(0, 0), (1, 1), (2, 2)]), LineString([(2, 2), (3, 3)])])
    road_network = RoadNetwork(geo_series)
    shortest_path = road_network.get_shortest_path((0.5, 0.5), (3, 3))
    print(shortest_path)

    # Loading from cache
    road_network_cached = RoadNetwork(use_cache=True)
    road_network_cached.load_from_cache()
    shortest_path_cached = road_network_cached.get_shortest_path((0.5, 0.5), (3, 3))
    print(shortest_path_cached)

def demo():
    # Demo usage using shapefile
    geo_series = gpd.read_file('data/gcs/road_network.shp')['geometry']
    road_network = RoadNetwork(geo_series, use_cache=True)
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

def demo_multiple_points():
    # Read start points from population_distribution.shp
    start_points_gdf = gpd.read_file('data/pcs/population_distribution.shp')
    start_points = [Point(xy) for xy in zip(start_points_gdf.geometry.x, start_points_gdf.geometry.y)]
    
    # Read end points from shelters.shp
    end_points_gdf = gpd.read_file('data/pcs/shelters.shp')
    end_points = [Point(xy) for xy in zip(end_points_gdf.geometry.x, end_points_gdf.geometry.y)]
    
    # Read road network from shapefile
    geo_series = gpd.read_file('data/pcs/road_network.shp')['geometry']
    road_network = RoadNetwork(geo_series, use_cache=False)
    
    # Batch calculate shortest paths
    road_network.batch_calculate_shortest_paths(start_points, end_points)
    
    # Plot shortest paths
    # fig, ax = plt.subplots()
    # geo_series.plot(ax=ax)
    # for start_point in start_points:
    #     for end_point in end_points:
    #         shortest_path = road_network.get_shortest_path((start_point.x, start_point.y), (end_point.x, end_point.y))
    #         if shortest_path:
    #             shortest_path_line = LineString(shortest_path)
    #             print(shortest_path_line.length)
    #             ax.plot(*shortest_path_line.xy, color='red')
    #         ax.scatter(start_point.x, start_point.y, color='green')
    #         ax.scatter(end_point.x, end_point.y, color='blue')
    
    # plt.show()

def demo_clear_cache():
    road_network = RoadNetwork(use_cache=True)
    road_network.clear_cache()

if __name__ == "__main__":
    start_time = time.time()
    
    # example()
    # demo()
    # demo_clear_cache()
    demo_multiple_points()
    # demo_multiple_points()
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")