import mesa
import mesa_geo as mg
from shapely.geometry import Point, Polygon, shape
import geopandas as gpd
from agents import Resident, Shelter, FireHazard
from road_network import RoadNetwork
from space import StudyArea
from cell import FireHazardCell
import rasterio as rio
from rasterio.transform import Affine
import rasterio.features
import numpy as np
import pandas as pd

# Note: When using mg.AgentCreator, the agents are stored in the self.model

class EvacuationModel(mesa.Model):

    # The shapefile path, in WGS_1984_UTM_Zone_11N, epsg:32611
    population_distribution_shp = "data/pcs/population_distribution.shp"
    shelters_shp = "data/pcs/shelters.shp"
    road_network_shp = "data/pcs/road_network.shp"

    # The hazard raster path
    hazard_raster = "data/pcs/fire_arrival_time.asc"
    hazard_raster_translated = "data/pcs/fire_arrival_time_translated.asc"
    
    # Create gdf for the shapefile
    population_distribution_gdf = gpd.read_file(population_distribution_shp)
    shelters_gdf = gpd.read_file(shelters_shp)
    road_network_gdf = gpd.read_file(road_network_shp)

    # Get CRS
    crs = population_distribution_gdf.crs

    def __init__(
        self, 
        num_steps=100, 
        num_residents=100, 
        max_speed=35, 
        acceleration=5, 
        deceleration=25, 
        alpha=0.14, 
        Rtau=45, 
        Rsig=1.65
    ):
        super().__init__()
        self.space = StudyArea(crs=self.crs ,warn_crs_conversion=True)
        self.road_network = RoadNetwork(geo_series=self.road_network_gdf['geometry'], use_cache=True)
        self.steps = 0
        self.step_interval = 1 # How many seconds each step represents
        self.time_elapsed = self.steps * self.step_interval # The total time elapsed in seconds
        self.running = True

        # Model parameters
        self.num_steps = num_steps
        self.num_residents = num_residents

        # Coversion factors
        # The model parameters uses imperial units iin consistency with Ali's paper. However we will convert
        # the units to metric system when performing spatial analysis with geopandas and rasterio.
        self.meter_to_feet = 3.28084 # 1 meter = 3.28084 feet

        # Pedestrian parameters
        self.ped_speed = 4.0 # ft/s

        # Car parameters
        self.max_speed = float(max_speed) # mph
        self.acceleration = float(acceleration) # ft/s^2
        self.deceleration = float(deceleration) # ft/s^2
        self.alpha = float(alpha) # mile^2/hr

        # Decision making time parameter
        self.Rtau = float(Rtau) # The milling time in minutes, the time it takes for a resident to receive the notification
        self.Rsig = float(Rsig) # The scale factor parameter

        # Statistics
        self.n_evacuated = 0
        self.n_dead = 0
        self.evacuation_time_list = []

        # Build shortest path cache
        # self.population_distribution_gdf = self.population_distribution_gdf.sample(n=self.num_residents)
        self.population_distribution_gdf = self.population_distribution_gdf.iloc[:self.num_residents]
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
        # resident_agents = resident_ag_creator.from_GeoDataFrame(self.population_distribution_gdf.sample(n=self.num_residents))
        resident_agents = resident_ag_creator.from_GeoDataFrame(self.population_distribution_gdf)
        self.space.add_agents(resident_agents)

        # Create fire hazard cells
        with rio.open(self.hazard_raster) as src:  
            values = src.read()      
            width = src.width
            height = src.height
            transform = src.transform      
            bounds = list(src.bounds)
            self.transform = transform
            hazard_raster_layer = mg.RasterLayer(width, height, "EPSG:32611", bounds, self, FireHazardCell)
            hazard_raster_layer.apply_raster(values, "fire_arrival_time")
            hazard_raster_layer.apply_raster(np.zeros_like(values), "is_burnt")
            self.space.add_layer(hazard_raster_layer)

        # Creare the fire hazard geoagent
        mask = values > 0
        hazard_shapes = list(rasterio.features.shapes(values, mask=mask, transform=transform))
        hazard_geoms = [shape(geom) for geom, value in hazard_shapes if value >= 0]
        hazard_gdf = gpd.GeoDataFrame(geometry=hazard_geoms, crs="EPSG:32611")
        hazard_ag_creator = mg.AgentCreator(FireHazard, model=self)
        hazard_agents = hazard_ag_creator.from_GeoDataFrame(hazard_gdf.dissolve())
        # self.space.add_agents(hazard_agents)
            
        # Data collector
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "steps": "steps",
                "Evacuated": "n_evacuated",
                "Casuality": "n_dead",
                "Percentage of Casuality": lambda m: m.n_dead / m.num_residents * 100,
                "Percentage of Evacuated": lambda m: m.n_evacuated / m.num_residents * 100,
                "Evacuation Time": lambda m: m.evacuation_time_list,
            }
        )
        self.datacollector.collect(self)

    def get_statistics(self):
        status = self.agents_by_type[Resident].get("status")
        return pd.Series(status).value_counts()

    def step(self):

        self.time_elapsed = self.steps * self.step_interval

        self.agents_by_type[FireHazardCell].do("step")
        self.agents_by_type[FireHazard].do("step")
        self.agents_by_type[Resident].do("step")
        self.agents_by_type[Resident].do("move_to_next_point")

        # Recreate R-tree for spatial queries after agents have moved
        self.space._recreate_rtree()

        # Collect data
        self.n_dead = self.get_statistics().get("dead", 0)
        self.n_evacuated = self.get_statistics().get("evacuated", 0)
        self.datacollector.collect(self)

        # Stop the model if all agents are evacuated and dead
        if self.n_dead + self.n_evacuated < len(self.agents_by_type[Resident]):
            # print("Step: ", self.steps)
            pass
        else:
            self.running = False

def get_status(model):
    status = model.agents_by_type[Resident].get("status")
    return pd.Series(status).value_counts()

def get_evacuation_time(model):
    evacuation_time = model.agents_by_type[Resident].get("evacuation_time")
    return pd.Series(evacuation_time).replace(np.inf, np.nan).dropna().tolist()

def demo():
    model = EvacuationModel(num_residents=2451, Rtau=0, Rsig=0)
    for i in range(3600):
        model.step()
        print(model.steps, model.n_evacuated, model.n_dead)
        if model.running == False:
            break
    gdf = model.space.get_agents_as_GeoDataFrame(agent_cls=Resident)
    gdf.to_file(f"debug/residents_output.shp")

def simualtion():

    # Create dictionary for differentn scenarios
    # num_residents = [500, 600, 700, 800, 900]
    # Rtau = [10, 20, 30, 40, 50]
    scenarios = {
        "num_residents": [500, 600, 700, 800, 900],
        "Rtau": [90]
    }

    # Create a list to store the results
    results = []

    for num_residents in scenarios["num_residents"]:
        for Rtau in scenarios["Rtau"]:
            model = EvacuationModel(num_residents=num_residents, Rtau=Rtau)
            while model.running:
                model.step()
                print(model.steps)
            print("Simulation completed for num_residents: ", num_residents, "Rtau: ", Rtau)
            results.append({
                "num_residents": num_residents,
                "Rtau": Rtau,
                "n_evacuated": model.n_evacuated,
                "n_dead": model.n_dead,
                "evacuation_time": model.evacuation_time_list
            })

    # Save the results to a csv file
    df = pd.DataFrame(results)
    df.to_csv("siumlation_results.csv", index=False)

if __name__ == "__main__":
    demo()
    # simualtion()