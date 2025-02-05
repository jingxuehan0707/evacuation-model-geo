import mesa_geo as mg
from pyproj import Transformer
from shapely.geometry import Point, LineString

class Resident(mg.GeoAgent):

    def __init__(self, model, geometry, crs):
        super().__init__(model, geometry, crs)

        # Test destination to move
        # transformer = Transformer.from_crs("EPSG:4326", self.crs)
        self.destination = Point(-116.1479, 43.59)
        # self.destination = transformer.transform(self.destination.x, self.destination.y)
        self.od_line = LineString([self.geometry, self.destination])

    def step(self):
        # Percentage of distance to move
        percentage = self.model.steps / self.model.num_steps
        # print("Percentage: ", percentage)

        # Interpolate the point to move
        new_position = self.od_line.interpolate(percentage, normalized=True)
        self.geometry = new_position
        # print("Geometry: ", self.geometry)
        # print("crs: ", self.crs)

        # print("Resident stepped")