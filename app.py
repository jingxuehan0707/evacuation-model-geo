import numpy as np
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mesa.visualization import Slider, SolaraViz, make_plot_component
from mesa_geo.visualization import make_geospace_component
from mesa.visualization.utils import update_counter
import mesa_geo as mg
from model import EvacuationModel
from agents import Resident, Shelter, FireHazard
from cell import FireHazardCell
import xyzservices.providers as xyz
import solara

model_params = {
    "num_steps": Slider("Number of steps", 1000, 10, 1000, 1),
    "num_residents": Slider("Number of residents", 100, 10, 2000, 1),
    "max_speed": {
        "type": "InputText",
        "value": 35,
        "label": "Car Max Speed (mph)",
    },
    "acceleration": {
        "type": "InputText",
        "value": 5,
        "label": "Car Acceleration (ft^2/s)",
    },
    "deceleration": {
        "type": "InputText",
        "value": 25,
        "label": "Car Deceleration (ft^2/s)",
    },
    "alpha": {
        "type": "InputText",
        "value": 0.14,
        "label": "Alpha (mi2/hr)",
    },
    "Rtau": {
        "type": "InputText",
        "value": 10,
        "label": "Milling Time (min)",
    },
    "Rsig": {
        "type": "InputText",
        "value": 1.65,
        "label": "Scale Factor Parameter",
    },
}

def draw_agents(agent):
    if isinstance(agent, mg.GeoAgent):
        if isinstance(agent, Resident):
            if agent.status == "waiting":
                return {
                "color": "#FF00FF",  # Light Magenta
                "weight": 2,
                }
            if agent.status == "evacuating":
                if agent.speed < 15.65: # 15.65 m/s = 35 mph
                    return {
                    "color": "#FFA500",  # Orange
                    "weight": 2,
                    }
                else:
                    return {
                    "color": "#32CD32",  # Lime Green
                    "weight": 2,
                    }
            if agent.status == "evacuated":
                return {
                "color": "#4682B4",  # Steel Blue
                "weight": 2,
                }
            if agent.status == "dead":
                return {
                "color": "#000000",  # Black
                "weight": 2,
                }
        elif isinstance(agent, Shelter):
            return {
                "color": "Red",
                "weight": 5,
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

def display_txt(model):
    minutes, seconds = divmod(model.time_elapsed, 60)
    return solara.Markdown(f"**Time Elapsed:** {int(minutes):02d}:{int(seconds):02d} <br >**Evacuated:** {model.n_evacuated} **Casuality:** {model.n_dead} <br> **Percentage of Evacuated:** {model.n_evacuated / model.num_residents:.2%} <br> **Percentage of Casuality:** {model.n_dead / model.num_residents:.2%}")

def post_process_line_plot(ax):
    """
    Post-processes the line plot by setting labels, limits, and styling.

    Args:
        ax (matplotlib.axes.Axes): The axes object to modify.
    """
    ax.legend(loc="upper left")
    ax.set_ylim(bottom=0, top=101)
    ax.set_xlim(left=0)
    ax.set_xlabel("Time Elapsed (minutes)")
    ax.set_ylabel("Percentage (%)")
    ax.set_title("Percentage of Agents Status")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

@solara.component
def evacuation_time_plot(model):
    update_counter.get()
    fig = Figure()
    ax = fig.subplots()

    # Create histogram if evacuation_time_list is not empty
    if np.sum(model.evacuation_time_list) > 0:
        counts, bins, _ = ax.hist(
            model.evacuation_time_list,
            bins=20,
            color="skyblue",
            edgecolor="black"
        )

        # Annotate histogram bars with counts
        for count, bin_left, bin_right in zip(counts, bins[:-1], bins[1:]):
            if count > 0:
                bin_center = (bin_left + bin_right) / 2
                ax.text(
                    bin_center,
                    count / 2,
                    f"{int(count)}",
                    ha="center",
                    va="center",
                    fontsize=8,
                    bbox=dict(facecolor='none', edgecolor='none', alpha=0.7)
                )

        # Add mean and median lines with labels
        mean_value = np.mean(model.evacuation_time_list)
        median_value = np.median(model.evacuation_time_list)
        ax.axvline(x=mean_value, color="red", linestyle="--", label="Mean")
        ax.axvline(x=median_value, color="green", linestyle="--", label="Median")
        ax.text(
            mean_value,
            ax.get_ylim()[1] * 0.9,
            f"Mean: {mean_value:.2f}",
            color="red",
            ha="center",
            bbox=dict(facecolor='white', edgecolor='red', boxstyle='round,pad=0.3')
        )
        ax.text(
            median_value,
            ax.get_ylim()[1] * 0.8,
            f"Median: {median_value:.2f}",
            color="green",
            ha="center",
            bbox=dict(facecolor='white', edgecolor='green', boxstyle='round,pad=0.3')
        )

    # Set plot title and labels
    ax.set_title("Agents Evacuation Time Distribution")
    ax.set_xlabel("Evacuation Time (minutes)")
    ax.set_ylabel("Frequency")
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)

    solara.FigureMatplotlib(fig)

@solara.component
def evacuation_status_plot(model):
    update_counter.get()
    fig = Figure()
    ax = fig.subplots()
    # get xticks first, and convert from steps to minutes
    xticks = ax.get_xticks()
    # convert xticks from steps to minutes
    xticks = [int(xtick * model.step_interval) for xtick
              in xticks]
    # create line plot with n_evacuated and n_dead
    ax.plot(xticks, model.n_evacuated, label="Evacuated", color="tab:blue")
    ax.plot(xticks, model.n_dead, label="Casuality", color="tab:red")
    ax.set_title("Evacuation Status")
    ax.set_xlabel("Time Elapsed (minutes)")
    ax.set_ylabel("Number of Agents")
    solara.FigureMatplotlib(fig)

model = EvacuationModel()
esri_imagery = xyz.USGS.USImagery
page = SolaraViz(
    model,
    [   
        display_txt,
        make_geospace_component(
            draw_agents,
            zoom=13,
            tiles=esri_imagery,
            # layout=Layout(width="800px"),
        ),
        #make_plot_component("agents evacuated"), 
        make_plot_component({"Percentage of Evacuated": "tab:blue", "Percentage of Casuality": "tab:red"}, post_process=post_process_line_plot),
        evacuation_time_plot,
        # make_statistics_plot,
    ],
    name="Evacuation Model",
    model_params=model_params,
)

page