import mesa_geo as mg
from pyproj import Transformer
from shapely.geometry import Point, LineString
from road_network import RoadNetwork
import networkx as nx
import geopandas as gpd

class Resident(mg.GeoAgent):

    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)
        self.origin = self.model.road_network.snap_to_network((self.geometry.x, self.geometry.y))
        self.destination = (-116.15188, 43.57599)  # A test shelter location
        self.path = []
        self.path_index = 0

        self._calculate_path()

    def _calculate_path(self):
        try:
            self.path = self.model.road_network.get_shortest_path((self.geometry.x, self.geometry.y), self.destination)
            self.path_index = 0
        except nx.NetworkXNoPath:
            # Do nothing if the node is not reachable
            self.path = []
            self.path_index = 0

    def step(self):
        if self.path_index < len(self.path):
            next_point = self.path[self.path_index]
            self.geometry = Point(next_point)
            self.path_index += 1