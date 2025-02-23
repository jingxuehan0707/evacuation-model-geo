import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
import mesa_geo as mg
from model import EvacuationModel
from agents import Resident, Shelter, FireHazard
from cell import FireHazardCell
import xyzservices.providers as xyz

model_params = {
    "num_steps": Slider("Number of steps", 1000, 10, 1000, 1),
    "num_residents": Slider("Number of residents", 100, 10, 2000, 1),
}

def draw_agents(agent):
    if isinstance(agent, mg.GeoAgent):
        if isinstance(agent, Resident):
            if agent.status == "waiting":
                return {
                "color": "#FF00FF",  # Light Magenta
                "weight": 5,
                }
            if agent.status == "evacuating":
                return {
                "color": "#32CD32",  # Lime Green
                "weight": 5,
                }
            if agent.status == "sheltered":
                return {
                "color": "#4682B4",  # Steel Blue
                "weight": 5,
                }
            if agent.status == "dead":
                return {
                "color": "#000000",  # Black
                "weight": 5,
                }
        elif isinstance(agent, Shelter):
            return {
                "color": "Red",
                "weight": 10,
            }
        # elif isinstance(agent, FireHazard):
        #     return {
        #         "color": "Orange",
        #         "fillColor": "Red",
        #         "fillOpacity": 0.5,
        #         "weight": 1,
        #     }
    if isinstance(agent, mg.Cell):
        if isinstance(agent, FireHazardCell):
            if agent.fire_arrival_time == -9999 or agent.is_burnt == False:
                return (0, 0, 0, 0)
            else:
                return map_to_red_gradient(agent.fire_arrival_time)

def map_to_red_gradient(cell_values, min_value=0, max_value=120):
    """
    Maps the given cell values (ranging from min_value to max_value) 
    to an inverted red-yellow gradient in RGBA format.
    
    Args:
        cell_values (numpy array): The array of cell values to be mapped.
        min_value (int): The minimum value in the range (default is 0).
        max_value (int): The maximum value in the range (default is 120).
        
    Returns:
        numpy array: The RGBA mapped colors for the cell values.
    """
    # Normalize the values to the range [0, 1]
    norm = mcolors.Normalize(vmin=min_value, vmax=max_value)
    
    # Create an inverted red-yellow colormap
    cmap = plt.cm.autumn_r
    
    # Map the cell values to the corresponding RGBA colors using the colormap
    rgba_colors = cmap(norm(cell_values))
    
    return rgba_colors

model = EvacuationModel()
esri_imagery = xyz.USGS.USImagery
page = SolaraViz(
    model,
    [
        make_geospace_component(
            draw_agents,
            zoom=13,
            tiles=esri_imagery
            # layout=Layout(width="800px"),
        ),
        make_plot_component("agents evacuated"),
    ],
    name="Evacuation Model",
    model_params=model_params,
)

page