import mesa
import mesa_geo as mg
from shapely.geometry import Point
from agents import Resident
import numpy as np
from scipy.spatial import cKDTree

class StudyArea(mg.GeoSpace):

    def __init__(self, crs=None, *, warn_crs_conversion=True):
        super().__init__(crs, warn_crs_conversion=warn_crs_conversion)

    def get_neighbors_within_distance_ckdtree(self, agent, distance):
        """Get neighboring agents within a certain distance using cKDTree for efficiency."""
        pass