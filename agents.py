import mesa_geo as mg
from pyproj import Transformer
import rasterio
import shapely
from shapely.geometry import Point, LineString, Polygon
from road_network import RoadNetwork
import networkx as nx
import geopandas as gpd
import math
from traffic import GMModel, GMModelLegacy
from geopandas import GeoDataFrame, GeoSeries
import pandas as pd
import dask_geopandas as dgpd
import numpy as np

class Resident(mg.GeoAgent):

    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)
        
        # Initialize agent properties
        self.origin = self.model.road_network.snap_to_network((self.geometry.x, self.geometry.y))
        self.destination = ()  # Placeholder for a test shelter location
        self.shelters = self.model.agents_by_type[Shelter]
        self.path = LineString()
        self.path_index = 0
        self.speed = 0  # Speed in m/s
        self.heading = 0  # Heading in degrees (north=0, east=90, south=180, west=270)
        self.viewshed = None
        self.mode = "drive"  # Travel mode
        self.decision_time = 0  # Decision-making time in seconds
        self.distance_to_dest = 0  # Distance to destination
        self.status = "waiting"  # Possible statuses: "waiting", "evacuating", "evacuated", "dead"

        # Choose the nearest shelter and calculate the path
        self.choose_shelter()

        # Calculate the decision-making time using a Rayleigh distribution
        self.decision_time = (np.random.rayleigh(self.model.Rsig) + self.model.Rtau) * 60

        # Initialize evacuation time (infinity until evacuation is complete)
        self.evacuation_time = np.inf

        # Calculate the initial heading between the agent's current position and origin
        self.heading = self.calculate_heading(
            self.geometry, Point(self.origin[0], self.origin[1])
        )
        
        # Calculate the initial viewshed based on the heading
        self.viewshed = self.calculate_viewshed(self.heading)

    def calculate_heading(self, from_point: Point, to_point: Point):
        """
        Calculate the heading from one point to another.
        This method calculates the heading angle from `from_point` to `to_point` 
        and converts it to a compass bearing.
        :param from_point: The starting point.
        :type from_point: Point
        :param to_point: The destination point.
        :type to_point: Point
        :return: The heading in degrees as a compass bearing.
        :rtype: float
        """
        
        delta_x = to_point.x - from_point.x
        delta_y = to_point.y - from_point.y
        
        angle = math.atan2(delta_x, delta_y)
        heading = math.degrees(angle)
        
        # Convert heading to compass bearing
        heading = (heading + 360) % 360
        
        return heading
    
    def calculate_viewshed(self, heading, angle=20, radius=100):
        """
        Calculate the viewshed triangle based on the agent's heading, angle, and radius.
        The viewshed is represented as a triangle polygon with the agent's current position
        as the apex and the left and right points calculated based on the given heading, angle, 
        and radius.
        :param heading: The direction the agent is facing in degrees (0-360).
        :type heading: float
        :param angle: The angle of the viewshed in degrees, defaults to 20.
        :type angle: float, optional
        :param radius: The radius of the viewshed, defaults to 100.
        :type radius: float, optional
        :return: A Polygon representing the viewshed triangle.
        :rtype: shapely.geometry.Polygon
        """
        
        
        # Calculate the left and right angles
        left_angle = (heading - angle / 2) % 360
        right_angle = (heading + angle / 2) % 360
        
        # Convert angles to radians
        left_angle_rad = math.radians(left_angle)
        right_angle_rad = math.radians(right_angle)
        
        # Calculate the left and right points of the viewshed triangle
        left_point = Point(self.geometry.x + radius * math.sin(left_angle_rad), 
                           self.geometry.y + radius * math.cos(left_angle_rad))
        right_point = Point(self.geometry.x + radius * math.sin(right_angle_rad), 
                            self.geometry.y + radius * math.cos(right_angle_rad))
        
        # Create the viewshed triangle polygon
        viewshed = Polygon([self.geometry, left_point, right_point])
    
        return viewshed
    
    def get_agents_in_viewshed(self, agents):
        """
        Get the agents that are within the viewshed of the current agent.
        :param agents: A list of agents to check.
        :type agents: list
        :return: A list of agents that are within the viewshed.
        :rtype: list
        """
        
        # Calculate the viewshed triangle
        viewshed = self.calculate_viewshed(self.heading)
        
        # Get the agents that are within the viewshed
        agents_in_viewshed = [agent for agent in agents if agent.geometry.within(viewshed)]
        
        return agents_in_viewshed
    
    def get_nearest_agent(self, agents):
        """
        Get the nearest agent from a GeoDataFrame of agents using spatial index.
        :param agents: A GeoDataFrame of agents.
        :type agents: GeoDataFrame
        :return: A GeoSeries containing the nearest agent.
        :rtype: GeoSeries
        """
        
        # Use spatial index to find the nearest agent
        nearest_idx = agents.sindex.nearest(self.geometry, max_distance=100)[0,0]
        
        # Return the nearest agent as a GeoSeries
        nearest_agent = agents.iloc[nearest_idx]
        
        return nearest_agent

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
        
        if self.model.time_elapsed < self.decision_time:
            self.status = "waiting"

        elif (self.distance_to_dest >= 0) and (self.model.time_elapsed >= self.decision_time):
            self.status = "evacuating"

            # Find the nearest agent in viewshed
            # TODO: performance issue
            # agents_in_viewshed = self.get_agents_in_viewshed(self.model.agents_by_type[Resident])
            residents = self.model.agents_by_type[Resident].get(["unique_id", "status", "geometry"])
            residents_df = pd.DataFrame(residents, columns=["unique_id","status", "geometry"])
            residents_df = residents_df[residents_df["status"] == "evacuating"]
            residents_gdf = GeoDataFrame(residents_df, geometry="geometry", crs=self.crs)
            residents_sindex = residents_gdf.sindex
            # viewshed_gdf = GeoDataFrame(geometry=[self.viewshed], crs=self.crs)
            # Get the agents in the viewshed
            # agents_in_viewshed = gpd.sjoin(residents_gdf, viewshed_gdf, predicate="within", how="inner")
            agents_in_viewshed = residents_gdf.iloc[residents_sindex.intersection(self.viewshed.bounds)]
            if agents_in_viewshed.shape[0] > 0:
                nearest_agent = self.get_nearest_agent(agents_in_viewshed)
                if nearest_agent.unique_id == self.unique_id:
                    nearest_agent = None
                else:
                    # Convert nearest_agent to Resident type, there is a bug here TODO
                    nearest_agent = self.model.agents_by_type[Resident][nearest_agent.unique_id - 4]
                    # nearest_agent = next(agent for agent in self.model.agents_by_type[Resident] if agent.unique_id == nearest_agent.unique_id)
            else:
                nearest_agent = None

            # Update speed using car following model
            gm_model = GMModelLegacy(self.model, nearest_agent, self)
            self.speed = gm_model.update_speed()

            # Calculate the distance to travel in this step (speed in km/h, step_interval in seconds)
            distance_to_travel = self.speed * self.model.step_interval  # convert speed to m/s
            
            # Calculate the next point based on the distance to travel
            current_point = self.geometry
            next_point = self.path.interpolate(self.path.project(current_point) + distance_to_travel)
            if next_point is None:
                # TODO, minor bug here. For some reason, we can't get the next point.
                next_point = current_point
            
            # Update the geomety
            self.geometry = Point(next_point.x, next_point.y)

            # Update the heading
            self.heading = self.calculate_heading(current_point, next_point)
            self.viewshed = self.calculate_viewshed(self.heading)

            # Update the distance to destination
            self.distance_to_dest -= distance_to_travel
        else:
            self.status = "evacuated"
            if self.evacuation_time > self.model.time_elapsed:
                self.evacuation_time = self.model.time_elapsed / 60
                self.model.evacuation_time_list.append(self.evacuation_time)

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
