#
# Copyright (c) Benedict Flade, Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#


import matplotlib.pyplot as plt
from numpy import eye
from promis import ProMis, StaRMap
from promis.geo import (
    CartesianLocation,
    CartesianRasterBand,
    PolarLocation,
    PolarMap,
)


def create_donut_pml():
    logic = """
            near_spot(X) :- distance(X, spot) > 1, distance(X, spot) < 5.
            landscape(X) :- near_spot(X).
            """
    origin = PolarLocation(latitude=0, longitude=0)
    uam_polar = PolarMap(origin=origin)
    covariance = {"spot": 1 * eye(2)}
    evaluation_resolution = (75, 75)
    area_size = (20, 20)
    number_of_random_maps = 25
    uam = uam_polar.to_cartesian()

    uam.features.append(CartesianLocation(-4.0, 6.0, location_type="spot"))

    evaluation_points = CartesianRasterBand(
        origin, evaluation_resolution, area_size[0], area_size[1]
    )

    uam.apply_covariance(covariance)
    star_map = StaRMap(uam)
    star_map.initialize(evaluation_points=evaluation_points, number_of_random_maps=number_of_random_maps, logic=logic)

    promis = ProMis(star_map)
    landscape = CartesianRasterBand(origin, (100, 100), width=area_size[0], height=area_size[1])

    promis.solve(landscape, logic=logic, n_jobs=8, batch_size=8, show_progress=True)

    return landscape


def check_donut_pml(df):
    assert (df["v0"] >= 0).all(), "v0 values must be larger than 0"
    assert (df["v0"] <= 1).all(), "v0 values must be smaller than 1"
    assert df[df["north"] <= -3.5]["v0"].max() < 1e-3, "v0 should be near zero in the bottom region"
    assert df[df["east"] >= 6.5]["v0"].max() < 1e-3, "v0 should be near zero in the right region"
    max_row = df.loc[df["v0"].idxmax()]
    assert max_row["east"] < 0, "v0 maximum should be in the left half"
    assert max_row["north"] > 0, "v0 maximum should be in the upper half"
    assert df["v0"].min() == 0, "v0 minimum should be exactly 0"


def plot_pml(landscape: CartesianRasterBand):
    plt.figure()
    axes = plt.gca()
    width, height = landscape.dimensions
    plt.xlim([-width / 2, width / 2])
    plt.ylim([-height / 2, height / 2])
    mission_area = CartesianRasterBand(landscape.origin, resolution=(500, 500), width=width, height=height)
    pml_image = landscape.into(mission_area).scatter(s=1, plot_basemap=False, rasterized=True, cmap="coolwarm_r")
    cbar = plt.colorbar(pml_image, aspect=18.5, fraction=0.05, pad=0.02)
    cbar.solids.set(alpha=1)
    axes.set_title("PML Donut Example")

    x_ticks = [-width / 2, 0, width / 2]
    x_labels = [f"{-width / 2}", "0", f"{width / 2}"]
    y_ticks = [-height / 2, 0, height / 2]
    y_labels = [f"{-height / 2}", "0", f"{height / 2}"]

    axes.axis("on")  # Hide entire axis
    axes.set_frame_on(False)

    axes.set_xticks(x_ticks)
    axes.set_xticklabels(x_labels)
    axes.set_yticks(y_ticks)
    axes.set_yticklabels(y_labels)
    axes.set_aspect("equal")

    plt.show(block=True)


def test_donut():
    pml = create_donut_pml()
    check_donut_pml(pml.data)


if __name__ == "__main__":
    pml_donut = create_donut_pml()
    plot_pml(pml_donut)
