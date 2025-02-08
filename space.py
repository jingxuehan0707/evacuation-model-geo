import mesa
import mesa_geo as mg
from shapely.geometry import Point
from agents import Resident

class StudyArea(mg.GeoSpace):

    def __init__(self, crs="epsg:4326", *, warn_crs_conversion=True):
        super().__init__(crs, warn_crs_conversion=warn_crs_conversion)