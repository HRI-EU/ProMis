from argparse import ArgumentParser
from pathlib import Path
from pickle import load
from signal import SIGINT
from subprocess import Popen
from time import monotonic, sleep

import matplotlib.pyplot as plt
import torch
from crazyflie_py import Crazyswarm
from numpy import array, ndarray

from promis import ConstitutionalController, DoubtDensity
from promis.geo import CartesianCollection


def get_path(setting: str) -> tuple[CartesianCollection, ndarray]:
    # TODO use the setting to load the correct path
    # match setting:
    #     case "promis":
    #         pass
    #     case "coco-fixed-v":
    #         pass
    #     case "coco-dynamic-v":
    #         pass

    doubt_density = DoubtDensity.load("data/doubt_density.pkl")
    landscape = CartesianCollection.load("data/virtual_setup_landscape.pkl")
    coco = ConstitutionalController()

    doubt_space = {
        "controller": {"type": "categorical", "number_of_classes": 2},
        "heading": {"type": "continuous"},
    }

    doubt_space["heading"]["values"] = torch.tensor([[0.0]])
    doubt_space["controller"]["values"] = torch.tensor([[1]])
    augmented_landscape = coco.apply_doubt(
        landscape=landscape,
        doubt_density=doubt_density,
        doubt_space=doubt_space,
        number_of_samples=100,
    )

    image = augmented_landscape.scatter(
        s=0.4, plot_basemap=False, rasterized=True, cmap="coolwarm_r", alpha=0.25
    )
    cbar = plt.colorbar(image, ticks=[0.0, 0.5, 1.0], aspect=25, pad=0.02)
    cbar.ax.set_yticklabels(["0.0", "0.5", "1.0"])
    cbar.solids.set(alpha=1)

    start = (-1_000, -1_000)
    goal = (1_400, 1_400)
    min_cost = 0.3
    return augmented_landscape, augmented_landscape.search_path(
        start,
        goal,
        cost_model=lambda p: max(min_cost, 1.0 - p**3),
        value_filter=lambda p: p >= min_cost,
        min_cost=min_cost,
    )


def main(setting: str, rosbag_name: str) -> None:
    augmented_landscape, path = get_path(setting)

    TAKEOFF_DURATION = 2.0
    HOVER_DURATION = 2.0
    Z = 0.4

    ROSBAG_START_DURATION = 5.0
    ROSBAG_TARGET = Path("data/rosbag-recordings").absolute()
    ROSBAG_TARGET.mkdir(exist_ok=True)

    swarm = Crazyswarm()
    cf = swarm.allcfs.crazyflies[0]

    # Start
    print("Liftoff!")
    cf.takeoff(targetHeight=Z, duration=TAKEOFF_DURATION)
    sleep(TAKEOFF_DURATION + HOVER_DURATION)

    # Start the rosbag as a subprocess that we can kill later
    rosbag_process = Popen(
        ["ros2", "bag", "record", "-o", str(ROSBAG_TARGET / rosbag_name), "-a"],
        shell=False,
    )
    try:
        # Wait for the rosbag to start
        sleep(ROSBAG_START_DURATION)
        print("Recording started")

        # Fly
        t0 = monotonic()
        last_x, last_y = path[0][:2]
        should_have_elapsed = 0.0
        for index, (x, y, v) in enumerate(path):
            distance = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
            duration = distance / v
            cf.goTo(
                array([x, y, Z]),
                yaw=0.0,
                duration=1.0,
            )
            elapsed = monotonic() - t0
            should_have_elapsed += duration
            sleep(should_have_elapsed - elapsed)
            last_x, last_y = x, y

        print("Experiment finished normally")

    except KeyboardInterrupt:
        print("Experiment interrupted by user")
    finally:
        print("Stopping the recording...")
        # Stop the rosbag recording
        rosbag_process.send_signal(SIGINT)
        rosbag_process.wait(timeout=5.0)

        # Land
        print("Landing...")
        cf.land(targetHeight=0.04, duration=TAKEOFF_DURATION)
        sleep(TAKEOFF_DURATION)


if __name__ == "__main__":
    parser = ArgumentParser(description="Record a test run.")
    parser.add_argument(
        "setting",
        type=str,
        choices=["promis", "coco-fixed-v", "coco-dynamic-v"],
        help="The setting to use for the test run.",
    )
    parser.add_argument(
        "rosbag_name",
        type=str,
        help="The name of the directory to save the rosbag recording.",
    )
    args = parser.parse_args()

    main(setting=args.setting, rosbag_name=args.rosbag_name)
