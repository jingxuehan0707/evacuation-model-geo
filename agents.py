import mesa_geo as mg
import rasterio
import shapely
from shapely.geometry import Point, LineString
import networkx as nx
import geopandas as gpd
import math
from traffic import GMModelLegacy
import numpy as np

class Resident(mg.GeoAgent):

    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)
        
        # Initialize agent properties
        self.origin = self.model.road_network.snap_to_network((self.geometry.x, self.geometry.y))
        self.destination = ()  # Placeholder for a test shelter location
        self.shelters = self.model.agents_by_type[Shelter]
        self.path = LineString()
        self.path_to_origin = LineString()
        self.speed = 0  # Speed in m/s
        self.heading = 0  # Heading in degrees (north=0, east=90, south=180, west=270)
        self.mode = "walk"  # Travel mode [walk, drive]
        self.decision_time = 0  # Decision-making time in seconds
        self.distance_to_dest = 0  # Distance to destination
        self.distance_to_origin = 0 # Distance to origin, agent needs to walk to origin first
        self.next_point = self.geometry  # Next point along the path
        self.status = "waiting"  # Possible statuses: "waiting", "evacuating", "evacuated", "dead"
        self.neighbors_ids = ""  # List of neighboring agent IDs

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

    def get_nearest_agent(self, agents):
        """
        Get the nearest agent from a list of agents.
        :param agents: A list of agents.
        :type agents: list
        :return: The nearest agent.
        :rtype: Agent
        """
        
        min_distance = float('inf')
        nearest_agent = None
        
        for agent in agents:
            distance = self.model.space.distance(self, agent)
            if distance == 0: # In case the other agent is identical to self.
                return nearest_agent
            if distance < min_distance:
                min_distance = distance
                nearest_agent = agent
        
        return nearest_agent
    
    def get_fov_agents(self, agents, angle=20):
        """
        Calculate the vectors from self to each agent, and only keep agents within certian angle of heading.
        """
        fov_agents = []
        for agent in agents:
            vector_to_agent = (agent.geometry.x - self.geometry.x, agent.geometry.y - self.geometry.y)
            angle_to_agent = math.degrees(math.atan2(vector_to_agent[0], vector_to_agent[1]))
            angle_diff = (angle_to_agent - self.heading + 360) % 360
            if angle_diff <= angle / 2 or angle_diff >= 360 - angle / 2:
                fov_agents.append(agent)
        return fov_agents

    def choose_shelter(self):
        # Choose the nearest shelter based on the shortest path
        min_distance = float('inf')
        nearest_shelter = None
        nearest_shelter_path = None
        for shelter in self.shelters:
            path = self.model.road_network.get_shortest_path((self.geometry.x, self.geometry.y), (shelter.geometry.x, shelter.geometry.y))
            if path:
                distance = LineString(path).length
                if distance < min_distance:
                    min_distance = distance
                    nearest_shelter = shelter
                    nearest_shelter_path = LineString(path)
            else:
                continue
        if nearest_shelter:
            self.destination = (nearest_shelter.geometry.x, nearest_shelter.geometry.y)
            self.path = nearest_shelter_path
            self.distance_to_dest = nearest_shelter_path.length
            self.path_to_origin = LineString([self.geometry, Point(self.origin[0], self.origin[1])])
            self.distance_to_origin = self.path_to_origin.length
        else: # If no shelter is reachable, set destination to None and path to empty
            # print(f"Agent {self.unique_id} could not find a path to any shelter.")
            self.destination = None
            self.path = LineString()
            self.distance_to_dest = 0

    def update_speed(self):
        """Update the speed using the sin wave between 0 - 25, every 10 steps"""
        self.speed = 1 * abs(math.sin(self.model.steps / 10))

    def move_to_next_point(self):
        """Update the geometry to the next point."""
        self.geometry = self.next_point

    def step(self):

        # Check if the agent is in the fire hazard area
        if self.geometry.within(self.model.agents_by_type[FireHazard][0].geometry):
            self.status = "dead"
            return
        
        # Mark the agent as dead if it has no destination or path
        if self.destination is None:
            self.status = "dead"
            return
        
        # Agent starts evacuation after the decision time has passed
        if self.model.time_elapsed < self.decision_time:
            self.status = "waiting"

        # Agent walks to orgin first
        elif (self.distance_to_origin > 0) and (self.model.time_elapsed >= self.decision_time):
            self.speed = self.model.ped_speed / self.model.meter_to_feet  # convert to m/s

            # Calculate the distance to travel in this step
            distance_to_travel = self.speed * self.model.step_interval
            
            # Calculate the next point based on the distance to travel
            current_point = self.geometry
            next_point = self.path_to_origin.interpolate(self.path_to_origin.project(current_point) + distance_to_travel)
            if next_point is None:
                # TODO, minor bug here. For some reason, we can't get the next point.
                self.next_point = current_point
            
            # Update the geomety
            self.next_point = Point(next_point.x, next_point.y)

            # Update the distance to origin
            self.distance_to_origin -= distance_to_travel

        # Agent start evacuating after the decision time has passed and there is still distance to destination
        elif (self.distance_to_dest > 0) and (self.model.time_elapsed >= self.decision_time):
            self.status = "evacuating"
            self.mode = "drive"

            # Use GeoSpace native search, the source code uses rtree.
            neighbors_agents = list(self.model.space.get_neighbors_within_distance(self, distance=20)) # it also gets the agent itself, we will filter it out later
            self.neighbors_ids = ",".join([str(agent.unique_id) for agent in neighbors_agents])
            neighbors_residents = [agent for agent in neighbors_agents if isinstance(agent, Resident) and agent.unique_id != self.unique_id]
            neighbors_resident_in_fov = self.get_fov_agents(neighbors_residents, angle=20)
            if len(neighbors_resident_in_fov) > 0:
                nearest_agent = self.get_nearest_agent(neighbors_resident_in_fov)
                if nearest_agent:
                    # print(f"Agent {self.unique_id} found nearest agent {nearest_agent.unique_id} in FOV")
                    pass
            else:
                nearest_agent = None

            # Update speed using car following model
            gm_model = GMModelLegacy(self.model, nearest_agent, self)
            self.speed = gm_model.update_speed()

            # Calculate the distance to travel in this step
            distance_to_travel = self.speed * self.model.step_interval
            
            # Calculate the next point based on the distance to travel
            current_point = self.geometry
            next_point = self.path.interpolate(self.path.project(current_point) + distance_to_travel)
            if next_point is None:
                # TODO, minor bug here. For some reason, we can't get the next point.
                self.next_point = current_point
            
            # Update the next point, however we will update geometry after we finish processing all other agents to avoid interference.
            self.next_point = Point(next_point.x, next_point.y)

            # Update the heading
            self.heading = self.calculate_heading(current_point, next_point)
            # self.viewshed = self.calculate_viewshed(self.heading)

            # Update the distance to destination
            self.distance_to_dest -= distance_to_travel
        else: # Agent has reached the destination
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
