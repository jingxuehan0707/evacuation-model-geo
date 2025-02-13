import mesa
import mesa_geo as mg
from shapely.geometry import Point
import geopandas as gpd
from agents import Resident, Shelter
from road_network import RoadNetwork
from space import StudyArea
import random

# Note: When using mg.AgentCreator, the agents are stored in the self.model

class EvacuationModel(mesa.Model):

    # The shapefile path
    population_distribution_shp = "data/gcs/population_distribution.shp"
    shelters_shp = "data/gcs/shelters.shp"
    road_network_shp = "data/gcs/road_network.shp"

    # Create gdf for the shapefile
    population_distribution_gdf = gpd.read_file(population_distribution_shp).sample(100)
    shelters_gdf = gpd.read_file(shelters_shp)
    road_network_gdf = gpd.read_file(road_network_shp)

    def __init__(self, num_steps=100):
        super().__init__()
        self.space = StudyArea(crs="EPSG:4326",warn_crs_conversion=True)
        self.road_network = RoadNetwork(geo_series=self.road_network_gdf['geometry'], use_cache=True)
        self.counts = {} # TODO: Agent counts by type
        self.steps = 0
        self.running = True

        # Model parameters
        self.num_steps = num_steps

        # Build shortest path cache
        start_points_gdf = self.population_distribution_gdf
        start_points = [Point(xy) for xy in zip(start_points_gdf.geometry.x, start_points_gdf.geometry.y)]
        end_points_gdf = self.shelters_gdf
        end_points = [Point(xy) for xy in zip(end_points_gdf.geometry.x, end_points_gdf.geometry.y)]
        self.road_network.batch_calculate_shortest_paths(start_points, end_points)

        # Create agents
        shelter_ag_creator = mg.AgentCreator(Shelter, model=self)
        shelter_agents = shelter_ag_creator.from_GeoDataFrame(self.shelters_gdf)
        self.space.add_agents(shelter_agents)

        resident_ag_creator = mg.AgentCreator(Resident, model=self)
        resident_agents = resident_ag_creator.from_GeoDataFrame(self.population_distribution_gdf)
        self.space.add_agents(resident_agents)
        print(len(self.agents_by_type[Resident]))

        # Data collector
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "steps": "steps",
                "agents evacuated": get_count_agent_sheltered
            }
        )
        self.datacollector.collect(self)

    def step(self):

        self.agents_by_type[Resident].do("step")

        self.datacollector.collect(self)
        if self.steps <= self.num_steps:
            print("Step: ", self.steps)
        else:
            self.running = False

def get_count_agent_sheltered(model):
    # TODO: save the count inside the Resident class
    n = 0
    for agent in model.agents_by_type[Resident]:
        if agent.status == "sheltered":
            n += 1
    return n

def demo():
    model = EvacuationModel()
    for i in range(2):
        model.step()
        get_count_agent_sheltered(model)

if __name__ == "__main__":
    demo()