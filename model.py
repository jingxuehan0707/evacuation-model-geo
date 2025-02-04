import mesa
import mesa_geo as mg
from shapely.geometry import Point


class EvacuationModel(mesa.Model):
    def __init__(self, num_steps=30):
        super().__init__()
        self.space = mg.GeoSpace(warn_crs_conversion=False)
        self.steps = 0
        self.running = True
        

        # Model parameters
        self.num_steps = num_steps

        # Create agents
        test_agent = mg.GeoAgent(self, Point(-116.1479, 43.59), crs="EPSG:4326" )
        self.space.add_agents([test_agent])

        # Data collector
        self.datacollector = mesa.DataCollector(
            {
                "steps": "steps",
            }
        )
        self.datacollector.collect(self)

    def step(self):
        self.datacollector.collect(self)
        if self.steps < self.num_steps:
            self.steps += 1
            print("Step: ", self.steps)
        else:
            self.running = False