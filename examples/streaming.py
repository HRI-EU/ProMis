# Standard Library
from pathlib import Path
import time

# Third Party
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy import eye, mean
from numpy.random import normal

# ProMis
from promis import ProMis, StaRMap
from promis.geo import PolarLocation, CartesianMap, CartesianLocation, CartesianRasterBand, CartesianCollection
from promis.loaders import LocalOsmLoader

##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Plotting setup ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman"],
    "font.size": 20,
    "xtick.labelsize": 20,
    "ytick.labelsize": 20,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

def show_collection(collection, value_index, ax, title):
    mission_area = CartesianRasterBand(collection.origin, (300, 300), collection.dimensions[0], collection.dimensions[1])

    image = collection.into(mission_area).to_polar().scatter(value_index=value_index, ax=ax, s=0.6, plot_basemap=True, rasterized=True, cmap="coolwarm_r", alpha=0.25)
    cbar = plt.colorbar(image, aspect=18.5, fraction=0.05, pad=0.02)
    cbar.solids.set(alpha=1)
    ax.set_title(title)


def set_style(axes, width, height):
    ticks = [-width / 2.0, 0, width / 2.0]
    axes[0].set_ylabel("Latitude")
    for ax in axes:
        ax.set_xlabel("Longitude")


def show_star_map(star_map, dimensions):
    fig, axes = plt.subplots(1, 4, sharey=True, figsize=(25, 10))

    over_park = star_map.get("over", "park")
    over_water = star_map.get("over", "water")
    distance_hospital = star_map.get("distance", "hospital")
    distance_primary = star_map.get("distance", "primary")

    show_collection(over_park.parameters, 0, axes[0], r'$P(over(X, park))$')
    show_collection(over_water.parameters, 0, axes[1], r'$P(over(X, water))$')
    show_collection(distance_hospital.parameters, 0, axes[2], r'$E[distance(X, hospital)]$')
    show_collection(distance_primary.parameters, 0, axes[3], r'$E[distance(X, primary)]$')

    set_style(axes, dimensions[0], dimensions[1])


##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Environment setup ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
def get_environment():
    # Bounding box centered at Central Park in NY City
    # 40.782628599814906, -73.96559374658658
    bbox = (
        (40.73, -74.01),
        (40.83, -73.91),
    )

    origin = PolarLocation(
        latitude=mean([bbox[0][0], bbox[1][0]]), longitude=mean([bbox[0][1], bbox[1][1]])
    )

    width = PolarLocation(latitude=bbox[0][0], longitude=bbox[0][1]).distance(
        PolarLocation(latitude=bbox[0][0], longitude=bbox[1][1])
    )
    height = PolarLocation(latitude=bbox[0][0], longitude=bbox[0][1]).distance(
        PolarLocation(latitude=bbox[1][0], longitude=bbox[0][1])
    )

    dimensions = (width, height)
    return origin, dimensions, bbox


def get_uam(uam_path, origin=None, dimensions=None, recompute=False):
    if uam_path.exists() and not recompute:
        uam = CartesianMap.load(uam_path)

    else:
        feature_description = {
            "park": "[leisure=park]",
            "water": "[natural=water]",
            "hospital": "[amenity=hospital]",
            "primary": "[highway=primary]",
            "secondary": "[highway=secondary]",
        }

        covariance = {
            "water": 25 * eye(2),
            "park": 25 * eye(2),
            "primary": 15 * eye(2),
            "secondary": 15 * eye(2),
            "hospital": 5 * eye(2),
        }

        pbf_path = Path(__file__).parent / "data" / "NewYork.osm.pbf"
        uam = LocalOsmLoader(pbf_path, origin, dimensions, feature_description).to_cartesian_map()
        uam.apply_covariance(covariance)

        uam.save(uam_path)

    return uam


def get_starmap(star_map_path, evaluation_points, uam=None, recompute=False):
    if star_map_path.exists() and not recompute:
        star_map = StaRMap.load(star_map_path)

    else:
        star_map = StaRMap(uam)
        star_map.sample(evaluation_points, number_of_random_maps=25, what={"distance": ["hospital", "primary", "secondary"], "over": ["park", "water"]})

        star_map.save(star_map_path)

    return star_map


def get_ais(
    path: str | Path, bbox: None | tuple[tuple[float, float], tuple[float, float]]
) -> pd.DataFrame:
    # Get all ships within mission area
    df = pd.read_pickle(path)
    if bbox is not None:
        df = df[
            (df["LAT"] > bbox[0][0])
            & (df["LAT"] < bbox[1][0])
            & (df["LON"] > bbox[0][1])
            & (df["LON"] < bbox[1][1])
        ]

    # Sort by time per ship
    df["BaseDateTime"] = pd.to_datetime(df["BaseDateTime"])
    df.sort_values(["BaseDateTime"], inplace=True)

    df.loc[df["VesselType"].isna(), "VesselType"] = 0  # Zero means unknown

    df["VesselType"] = df["VesselType"].astype(int)

    return df


##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Reasoning ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
# Movement constraints for UAVs flying over NY City
resin_program = """
over(park) <- source("/star_map/over/park", Probability).
over(water) <- source("/star_map/over/water", Probability).

distance(hospital) <- source("/star_map/distance/hospital", Density).
distance(primary) <- source("/star_map/distance/primary", Density).
distance(secondary) <- source("/star_map/distance/secondary", Density).
distance(vessel) <- source("/star_map/distance/vessel", Density).
distance(uas) <- source("/star_map/distance/uas", Density).

permitted if over(park).
permitted if over(water).

road_safety if distance(primary) < 35.0.
road_safety if distance(secondary) < 15.0.

agent_safety if distance(vessel) > 100.0 and distance(uas) > 100.0.

landscape if distance(hospital) > 200.0 and road_safety and agent_safety.
landscape if permitted and agent_safety.
landscape -> target("/reactive_mission_landscape").
"""


if __name__ == "__main__":
    # Simulation parameters
    NUM_DRONES = 10
    DRONE_SPEED = 30.0  # m/s
    SIMULATION_FREQUENCY = 2.0  # Hz
    dt = 1.0 / SIMULATION_FREQUENCY

    # Inference settings
    origin, dimensions, bbox = get_environment()
    resolution = (200, 200)
    raster = CartesianRasterBand(origin, resolution, dimensions[0], dimensions[1])
    print(f"Reactive Mission Landscape on {dimensions[0]:.2f}m x {dimensions[1]:.2f}m")

    # Simulated vertiports to spawn UAS from
    vertiports = [
        CartesianLocation(-2000, -2000, location_type="vertiport"),
        CartesianLocation( 2000,  -500, location_type="vertiport"),
        CartesianLocation(    0,  2000, location_type="vertiport"),
    ]

    print("Setup ProMis ...")
    data_path = Path(__file__).parent / "data"
    # Local features such as roads, hospitals, ... to relate to
    uam = get_uam(data_path / "streaming_uam.pkl", origin, dimensions, recompute=False)
    uam.features.extend(vertiports)
    # Spatial relations
    star_map = get_starmap(data_path / "streaming_star_map.pkl", uam=uam, evaluation_points=raster, recompute=False)
    # AIS data from NOAA
    ais = get_ais(data_path / "AIS_2024_02_24.pkl", bbox=bbox)
    # ProMis itself
    promis = ProMis(star_map, resin_program, resolution[0] * resolution[1], False)

    # We adapt the Reactive Circuit (internal inference engine) for the scenario by hand
    # Alternatively, run inference for some time and rc.adapt() instead for automatic restructuring
    rc = promis.get_reactive_circuit()    
    # Specific leaf names depend on comparison operators
    names = promis.get_names()
    drone_index = names.index("distance_uas_gt_100")
    vessel_index = names.index("distance_vessel_gt_100")
    # We know that these two are in a higher frequency band than the rest
    rc.lift_leaf(drone_index)
    rc.lift_leaf(drone_index + 1)
    rc.lift_leaf(vessel_index)
    rc.lift_leaf(vessel_index + 1)

    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(12, 7))

    for a in ax:
        a.set_box_aspect(1)

    fline = []
    fline.append(ax[1].plot([], [], "-", label=fr"$\lambda$ Drones")[0])
    fline.append(ax[1].plot([], [], "-", label=fr"$\lambda$ Vessels")[0])
    fline.append(ax[1].plot([], [], "-", label=fr"$\lambda$ OpenStreetMap")[0])

    rc_vline = ax[0].plot([], [], "-", label=f"Reactive Runtime")[0]
    promis_hline = ax[0].axhline(42.0, 0, 120, color="orange", label=f"Baseline")
    lscatter = ax[2].scatter([], [], c=[], marker='s', edgecolors='none', s=1.0, cmap="coolwarm_r", vmin=0.0, vmax=1.0)

    ax[0].set_xlabel("Time / s")
    ax[0].set_ylabel("Inference Time / s")
    ax[0].set_yscale("log")
    ax[0].legend(loc="upper right")
    ax[1].set_xlabel("Time / s")
    ax[1].set_ylabel("Frequency / Hz")
    ax[1].set_ylim(-0.1, 2.5)
    ax[1].legend(loc="upper right")
    ax[2].set_xlabel("Easting / m")
    ax[2].set_ylabel("Northing / m")
    ax[2].set_xlim(-dimensions[0] / 2.0, dimensions[0] / 2.0)
    ax[2].set_ylim(-dimensions[1] / 2.0, dimensions[1] / 2.0)

    fig.canvas.draw()
    plt.ion()
    plt.tight_layout()
    plt.show()

    coords = raster.coordinates()

    # Write all static star_map sources automatically (over/park, over/water,
    # distance/hospital, distance/primary, distance/secondary).
    promis.initialize(raster)

    # Initialise dynamic sources with a "very far away" distribution so that
    # P(distance > 100) ≈ 1 everywhere before any live data arrives.
    FAR_MEAN = 10_000.0  # m
    FAR_STD  = 100.0
    n = len(coords)
    promis.get_writer("distance", "vessel").write("normal", [[FAR_MEAN] * n, [FAR_STD] * n], time.monotonic())
    promis.get_writer("distance", "uas").write("normal",    [[FAR_MEAN] * n, [FAR_STD] * n], time.monotonic())

    # Ensures that all data was transferred
    time.sleep(0.00001)

    print(f"Starting simulation for {len(ais)} messages...")
    drones = []
    dynamic_uam = CartesianMap(origin)
    dynamic_features = {}
    dynamic_star_map = StaRMap(dynamic_uam)
    dynamic_star_map.link(promis)

    # Simulation setup
    results_data = []
    results_file = data_path / "results.csv"
    ais_start_time = ais.iloc[0]["BaseDateTime"]
    simulation_start_time = time.monotonic()
    ais_index = 0
    frequency_history = [[], [], []]
    rc_runtime_history = []
    times = []

    def get_random_dest():
        return np.array(
            [
                (np.random.rand() - 0.5) * dimensions[0],
                (np.random.rand() - 0.5) * dimensions[1],
            ]
        )

    # Run simulation
    try:
        iteration = 0
        current_sim_time_offset = 0.0
        while current_sim_time_offset <= 600.0:
            loop_start_time = time.monotonic()
            current_sim_time_offset = loop_start_time - simulation_start_time

            # AIS update
            ais_updated = False
            while ais.iloc[ais_index + 1]["BaseDateTime"] <= ais_start_time + pd.Timedelta(seconds=current_sim_time_offset):
                ais_index += 1
                current_row = ais.iloc[ais_index]
                dynamic_features[current_row["MMSI"]] = PolarLocation(
                    current_row["LON"], current_row["LAT"], location_type="vessel"
                ).to_cartesian(origin)
                ais_updated = True

            if ais_updated:
                dynamic_uam.features = list(dynamic_features.values())
                vessel_locations = CartesianCollection(origin)
                if dynamic_uam.features:
                    start = time.monotonic()
                    vessel_locations.append_with_default(
                        np.vstack([normal([l.x, l.y], 150.0, [50, 2]) for l in dynamic_uam.features]), 0.0
                    )
                    dynamic_star_map.update("distance", "vessel", vessel_locations, 25)
                    vessel_elapsed = time.monotonic() - start
                else:
                    vessel_elapsed = 0.0
            else:
                vessel_elapsed = 0.0

            # UAS update
            while len(drones) < NUM_DRONES:
                start_vertiport = np.random.choice(vertiports)
                drone = {
                    "position": np.array([start_vertiport.x, start_vertiport.y]),
                    "destination": get_random_dest(),
                    "state": "to_destination",
                }
                drones.append(drone)

            for drone in drones:
                pos = drone["position"]
                dest = drone["destination"]
                direction = dest - pos
                distance = np.linalg.norm(direction)

                if distance < DRONE_SPEED * dt:
                    drone["position"] = dest
                    if drone["state"] == "to_destination":
                        drone["state"] = "to_vertiport"
                        new_destination = np.random.choice(vertiports)
                        drone["destination"] = np.array([new_destination.x, new_destination.y])
                    else:
                        drone["state"] = "to_destination"
                        drone["destination"] = get_random_dest()
                else:
                    drone["position"] += (direction / distance) * DRONE_SPEED * dt

            dynamic_uam.features = [
                CartesianLocation(d["position"][0], d["position"][1], location_type="uas") for d in drones
            ]

            start = time.monotonic()
            uas_locations = CartesianCollection(origin)
            uas_locations.append_with_default(
                np.vstack([normal([d["position"][0], d["position"][1]], 150.0, [50, 2]) for d in drones]), 0.0
            )
            dynamic_star_map.update("distance", "uas", uas_locations, 25)
            uas_elapsed = time.monotonic() - start

            times.append(current_sim_time_offset)

            start = time.monotonic()
            landscape = promis.update()
            elapsed = time.monotonic() - start
            rc_runtime_history.append(elapsed + vessel_elapsed + uas_elapsed)

            frequencies = promis.get_frequencies()
            frequency_history[0].append(frequencies[drone_index])
            frequency_history[1].append(frequencies[vessel_index])
            frequency_history[2].append(frequencies[0])
            fline[0].set_data(times, frequency_history[0])
            fline[1].set_data(times, frequency_history[1])
            fline[2].set_data(times, frequency_history[2])
            rc_vline.set_data(times, rc_runtime_history)

            if landscape is not None:
                lscatter.set_offsets(coords)
                lscatter.set_array(landscape.data["v0"])

            ax[0].relim()
            ax[0].autoscale_view()
            ax[1].relim()
            ax[1].autoscale_view()

            fig.canvas.draw_idle()

            results_data.append({
                "runtime": rc_runtime_history[-1],
                "uas_frequency": frequency_history[0][-1],
                "vessel_frequency": frequency_history[1][-1],
                "time": iteration / SIMULATION_FREQUENCY,
            })
            iteration += 1

            # --- Loop Rate Control ---
            loop_end_time = time.monotonic()
            elapsed_loop_time = loop_end_time - loop_start_time
            sleep_time = dt - elapsed_loop_time

            if sleep_time > 0:
                fig.canvas.start_event_loop(sleep_time)

            if ais_index >= len(ais) - 1:
                exit()

    except KeyboardInterrupt:
        pass

    if results_data:
        results_df = pd.DataFrame(results_data)
        is_new_file = not results_file.exists() or results_file.stat().st_size == 0
        results_df.to_csv(
            results_file, mode="a", header=is_new_file, index=False
        )
