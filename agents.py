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
        self.destination = () # A test shelter location
        self.shelters = self.model.agents_by_type[Shelter]
        self.path = []
        self.path_index = 0
        self.status = "waiting" # "waiting", "evacuating", "sheltered"

        # self._calculate_path()
        self.choose_shelter()

    def _calculate_path(self):

        self.path = self.model.road_network.get_shortest_path((self.geometry.x, self.geometry.y), self.destination)
        self.path_index = 0

    def choose_shelter(self):
        # Choose the nearest shelter based on the shortest path
        min_distance = float('inf')
        nearest_shelter = None
        nearest_shelter_path = None
        for shelter in self.shelters:
            path = self.model.road_network.get_shortest_path((self.geometry.x, self.geometry.y), (shelter.geometry.x, shelter.geometry.y))
            distance = LineString(path).length
            if distance < min_distance:
                min_distance = distance
                nearest_shelter = shelter
                nearest_shelter_path = path
        # print("Nearest shelter: ", nearest_shelter.geometry)
        self.destination = (nearest_shelter.geometry.x, nearest_shelter.geometry.y)
        self.path = nearest_shelter_path
        self.path_index = 0

    
    def step(self):
        if self.path_index < len(self.path):
            self.status = "evacuating"
            next_point = self.path[self.path_index]
            self.geometry = Point(next_point)
            self.path_index += 1
        else: # TODO: there is bug here
            self.status = "sheltered"

class Shelter(mg.GeoAgent):

    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)