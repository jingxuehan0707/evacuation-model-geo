from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from model import EvacuationModel
from agents import Resident, Shelter
from ipywidgets import Layout

model_params = {
    "num_steps": Slider("Number of steps", 1000, 10, 1000, 1),
}

def draw_agents(agent):

    if isinstance(agent, Resident):
        portrayal = {
            "color": "Green",
            "weight": 5,
        }
    if isinstance(agent, Shelter):
        portrayal = {
            "color": "Red",
            "weight": 10,
        }
    return portrayal

model = EvacuationModel()
page = SolaraViz(
    model,
    [
        make_geospace_component(
            draw_agents,
            zoom=13,
            layout=Layout(width="800px"),
        ),
        # make_plot_component("steps"),
    ],
    name="Evacuation Model",
    model_params=model_params,
)

page