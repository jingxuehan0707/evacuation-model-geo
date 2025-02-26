import mesa_geo as mg
from pyproj import Transformer
import rasterio
import shapely
from shapely.geometry import Point, LineString
from road_network import RoadNetwork
import networkx as nx
import geopandas as gpd
import math

class Resident(mg.GeoAgent):

    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)
        self.origin = self.model.road_network.snap_to_network((self.geometry.x, self.geometry.y))
        self.destination = () # A test shelter location
        self.shelters = self.model.agents_by_type[Shelter]
        self.path = LineString()
        self.path_index = 0
        self.speed = 1 # km/h
        self.mode = "drive "# travel mode
        self.distance_to_dest = 0 # distance to destination
        self.status = "waiting" # "waiting", "evacuating", "sheltered"

        # self._calculate_path()
        self.choose_shelter()

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
                nearest_shelter_path = LineString(path)
        # print("Nearest shelter: ", nearest_shelter.geometry)
        self.destination = (nearest_shelter.geometry.x, nearest_shelter.geometry.y)
        self.path = nearest_shelter_path
        self.path_index = 0
        self.distance_to_dest = nearest_shelter_path.length

    def update_speed(self):
        """Update the speed using the sin wave between 0 - 25, every 10 steps"""
        self.speed = 1 * abs(math.sin(self.model.steps / 10))

    def step(self):

        # Check if the agent is in the fire hazard area
        if self.geometry.within(self.model.agents_by_type[FireHazard][0].geometry):
            self.status = "dead"
            return

        if self.distance_to_dest >= 0:
            self.status = "evacuating"
            
            # Update the speed 
            self.update_speed()

            # Calculate the distance to travel in this step (speed in km/h, step_interval in seconds)
            distance_to_travel = (self.speed * 1000) / 3600 * self.model.step_interval  # convert speed to m/s
            
            # Calculate the next point based on the distance to travel
            current_point = self.geometry
            next_point = self.path.interpolate(self.path.project(current_point) + distance_to_travel)
            
            self.geometry = Point(next_point.x, next_point.y)
            self.distance_to_dest -= distance_to_travel
        else:
            self.status = "sheltered"

class Shelter(mg.GeoAgent):

    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)

class FireHazard(mg.GeoAgent):

    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)

    def step(self):

        # Get the fire hazard cells
        hazard_cell = self.model.space.layers[0].get_raster(attr_name="is_burnt")
        # Update the geometry using the hazard cell
        mask = hazard_cell == True
        hazard_shapes = list(rasterio.features.shapes(hazard_cell, mask=mask, transform=self.model.transform))
        hazard_geoms = [shapely.geometry.shape(geom) for geom, value in hazard_shapes if value >= 0]
        self.geometry = shapely.ops.unary_union(hazard_geoms)