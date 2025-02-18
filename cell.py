import mesa
import mesa_geo as mg
import rasterio as rio

class FireHazard(mg.Cell):
    def __init__(self, model, pos, indices):
        super().__init__(model, pos, indices)
        self.fire_arrival_time = None  # in seconds
        self.is_burnt = None  # boolean

    def step(self):
        # Logic for what happens at each step
        pass
