from argparse import ArgumentParser
from pathlib import Path
from pickle import load
from signal import SIGINT
from subprocess import PIPE, Popen
from time import monotonic, sleep

from crazyflie_py import Crazyswarm
from networkx import Graph
from numpy import array, full, load, stack
from tqdm import tqdm


def main(setting: str, controller: int, rosbag_name: str, speed: float = 0.1) -> None:
    # Load the graph and landscape
    # with open(f"data/drone-exp/extended_graph-controller-{controller}.pkl", "rb") as f:
    #     graph: Graph = load(f)

    start = (-1_000, -1_000)
    start_w_speed = (*start, speed)
    goal = (1_400, 1_400)
    goal_w_speed = (*goal, speed)

    speeds = [0.3, 0.8]
    assert speed in speeds, f"Speed {speed} not in {speeds}"
    start_speed = speeds[0]
    end_speed = speeds[0]

    # min_speed = 0.3
    # max_speed = 1.4

    # # Only comes from the speed component
    # min_cost = min_speed / max_speed  # All speed costs are scaled to this anyway

    # def cost_model(p):
    #     consitution_cost = (1.0 - p) * 4
    #     time_cost = min_speed / speed
    #     return consitution_cost + time_cost

    # def value_filter(p):
    #     return p >= min_cost

    # match setting:
    #     case "promis":
    #         landscape_one_speed = CartesianRasterBand.load(
    #             f"data/drone-exp/original_landscape-speed-{default_speed:.2f}.pkl"
    #         )
    #         path = landscape_one_speed.search_path(
    #             start=start,
    #             goal=goal,
    #             cost_model=cost_model,
    #             value_filter=value_filter,
    #             min_cost=min_cost,
    #         )
    #     case "coco-fixed-v":
    #         speed = 0.1
    #         landscape_one_speed = CartesianRasterBand.load(
    #             f"data/drone-exp/augmented_landscape-controller-{controller}-speed-{speed:.2f}.pkl"
    #         )
    #     case "coco-dynamic-v":
    #         path = landscape_one_speed.search_path(
    #             start=start,
    #             goal=goal,
    #             graph=graph,
    #         )
    #     case _:
    #         raise ValueError(f"Unknown setting: {setting}")

    match setting:
        case "promis":
            path = load(f"data/drone-exp/original_path-speed-{speed:.2f}.npy")
        case "coco-fixed-v":
            path = load(
                f"data/drone-exp/augmented_graph-controller-{controller}-speed-{speed:.2f}.npy"
            )
        case "coco-dynamic-v":
            path = load(f"data/drone-exp/extended_path-controller-{controller}.npy")

    path_with_velocity = (
        path
        if path.shape[1] == 3
        else stack([path[:, 0], path[:, 1], full(path.shape[0], speed)], axis=1)
    )

    TAKEOFF_DURATION = 2.0
    HOVER_DURATION = 0.5
    GOTO_START_DURATION = 2.0
    Z = 0.4

    ROSBAG_START_DURATION = 5.0  # Also needs time to reach the start position
    assert ROSBAG_START_DURATION >= GOTO_START_DURATION
    ROSBAG_TARGET = Path("data/rosbag-recordings").absolute()
    ROSBAG_TARGET.mkdir(exist_ok=True)

    swarm = Crazyswarm()
    cf = swarm.allcfs.crazyflies[0]

    # Liftoff and go to start position
    print("Liftoff!")
    cf.takeoff(targetHeight=Z, duration=TAKEOFF_DURATION)
    sleep(TAKEOFF_DURATION + HOVER_DURATION)

    cf.goTo(
        array([*path[0][:2], Z]),
        yaw=0.0,
        duration=GOTO_START_DURATION,
    )
    # We wait while rosbag is starting

    # Start rosbag as a subprocess that we can interrupt/shutdown later
    rosbag_process = Popen(
        ["ros2", "bag", "record", "-o", str(ROSBAG_TARGET / rosbag_name), "-a"],
        # ["watch", "ls", "/"],
        shell=False,
        stdout=PIPE,
        stderr=PIPE,
    )
    try:
        # Wait for rosbag to start
        sleep(ROSBAG_START_DURATION)
        print("Recording started")

        # Fly
        t0 = monotonic()
        last_x, last_y = path[0][:2]
        should_have_elapsed = 0.0
        # We skip the first point, since we already flew there
        for index, (x, y, v) in tqdm(enumerate(path_with_velocity[1:, ...]), disable=False):
            distance = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
            duration = distance / (v * 1000)  # m/s to mm/s
            cf.goTo(
                array([x, y, Z]),
                yaw=0.0,
                duration=duration,
            )
            # print(
            #     f"Flying to ({x:.2f}, {y:.2f}) with speed {v:.2f} m/s, "
            #     f"duration {duration:.2f} s, distance {distance:.2f} mm"
            # )
            elapsed = monotonic() - t0
            should_have_elapsed += duration
            to_sleep = should_have_elapsed - elapsed
            if to_sleep > 0:
                sleep(to_sleep)
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
        "controller",
        type=int,
        choices=[0, 1, 2],
        help="The controller to use for the test run.",
    )
    parser.add_argument(
        "rosbag_name",
        type=str,
        help="The name of the directory to save the rosbag recording.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=0.3,
        choices=[0.3, 0.8],
        help="The speed to use for the test run.",
    )
    args = parser.parse_args()

    main(
        setting=args.setting,
        controller=args.controller,
        rosbag_name=args.rosbag_name,
        speed=args.speed,
    )
