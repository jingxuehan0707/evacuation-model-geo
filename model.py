import mesa
import mesa_geo as mg
from shapely.geometry import Point
import geopandas as gpd
from agents import Resident
from road_network import RoadNetwork
from space import StudyArea


class EvacuationModel(mesa.Model):

    # The shapefile path
    population_distribution_shp = "data/gcs/population_distribution.shp"
    road_network_shp = "data/gcs/road_network.shp"

    def __init__(self, num_steps=30):
        super().__init__()
        self.space = StudyArea(crs="EPSG:4326",warn_crs_conversion=True)
        self.road_network = RoadNetwork(geo_series=gpd.read_file(self.road_network_shp)['geometry'])
        self.steps = 0
        self.running = True

        # Model parameters
        self.num_steps = num_steps

        # Create agents
        resident_ag_creator = mg.AgentCreator(Resident, model=self)
        resident_agents = resident_ag_creator.from_file(self.population_distribution_shp)
        self.space.add_agents(resident_agents)
        
        # Create a single agent
        # resident_agent = Resident(self, Point(-116.1264, 43.5984), crs="EPSG:4326" )
        # self.space.add_agents(resident_agent)

        # Data collector
        self.datacollector = mesa.DataCollector(
            {
                "steps": "steps",
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