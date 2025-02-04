from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import EvacuationModel
from ipywidgets import Layout

model_params = {
    "num_steps": Slider("Number of steps", 30, 10, 50, 1),
}

def draw_agents(agent):
    return {"Shape": "circle", "r": 2, "Color": "red"}

model = EvacuationModel()
page = SolaraViz(
    model,
    [
        make_geospace_component(
            draw_agents,
            zoom=14,
            layout=Layout(width="800px", height="600px"),
        ),
        # make_plot_component("steps"),
    ],
    name="Evacuation Model",
    model_params=model_params,
)

page