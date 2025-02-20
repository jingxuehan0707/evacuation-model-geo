import mesa
import mesa_geo as mg
import rasterio as rio

class FireHazard(mg.Cell):
    def __init__(self, model, pos, indices):
        super().__init__(model, pos, indices)
        self.fire_arrival_time = None  # in minutes
        self.is_burnt = False  # boolean

    def step(self):

        if (self.model.time_elapsed >= self.fire_arrival_time * 60) and (self.is_burnt == False):
            self.is_burnt = True
        
