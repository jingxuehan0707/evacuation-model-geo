from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import EvacuationModel
from ipywidgets import Layout

model_params = {
    "num_steps": Slider("Number of steps", 30, 10, 50, 1),
}

def draw_agents(agent):
    portrayal = {
        "color": "Green",
        "weight": 1,
        # "radius": 1
    }
    return portrayal

model = EvacuationModel()
page = SolaraViz(
    model,
    [
        make_geospace_component(
            draw_agents,
            tiles=None,
            zoom=12,
            # layout=Layout(width="800px", height="100%"),
        ),
        # make_plot_component("steps"),
    ],
    name="Evacuation Model",
    model_params=model_params,
)

page