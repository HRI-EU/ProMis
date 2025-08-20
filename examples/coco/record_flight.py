from argparse import ArgumentParser
from pathlib import Path
from signal import SIGINT
from subprocess import DEVNULL, PIPE, Popen, TimeoutExpired
from time import monotonic, time

from crazyflie_py import Crazyswarm
from numpy import array, full, load, stack
from tqdm import tqdm


def main(setting: str, controller: int, rosbag_path: Path, speed: float) -> None:
    speeds = [0.2, 0.5, 1.0]
    assert speed in speeds, f"Speed {speed} not in {speeds}"

    match setting:
        case "promis":
            path = load(f"data/drone-exp/original_path-speed-{speed:.2f}.npy")
        case "coco-fixed-v":
            path = load(
                f"data/drone-exp/augmented_path-controller-{controller}-speed-{speed:.2f}.npy"
            )
        case "coco-dynamic-v":
            path = load(f"data/drone-exp/extended_path-controller-{controller}.npy")

    path_with_velocity = (
        path
        if path.shape[1] == 3
        else stack([path[:, 0], path[:, 1], full(path.shape[0], speed)], axis=1)
    )
    path_with_velocity[:, :2] /= 1000  # Convert from mm to m
    # The speed v is already in m/s
    del path

    TAKEOFF_DURATION = 2.5
    LAND_DURATION = TAKEOFF_DURATION
    HOVER_DURATION = 5
    SIT_DURATION = 5
    GOTO_START_DURATION = 2.0
    Z = 0.35

    ROSBAG_START_DURATION = 5.0  # Also needs time to reach the start position
    assert ROSBAG_START_DURATION >= GOTO_START_DURATION
    rosbag_path.absolute().parent.mkdir(exist_ok=True, parents=True)

    swarm = Crazyswarm()
    time_helper = swarm.timeHelper
    cf = swarm.allcfs.crazyflies[0]

    # Liftoff and go to start position
    print("Liftoff!")
    cf.takeoff(targetHeight=Z, duration=TAKEOFF_DURATION)
    time_helper.sleep(TAKEOFF_DURATION + HOVER_DURATION)

    is_forward = True
    iteration = 0
    while True:
        print(f"Performing round {iteration} (forward={is_forward})")

        target_path = path_with_velocity.copy()
        if not is_forward:
            target_path = target_path[::-1, ...]

        print("going to start:", array([*target_path[0][:2], Z]))
        cf.goTo(
            array([*target_path[0][:2], Z]),
            yaw=0.0,
            duration=GOTO_START_DURATION,
        )
        # We wait while rosbag is starting

        # Start rosbag as a subprocess that we can interrupt/shutdown later
        rosbag_individual_path = rosbag_path.absolute() / str(int(time()))
        rosbag_process = Popen(
            ["ros2", "bag", "record", "-o", str(rosbag_individual_path), "--all"],
            shell=False,
            stdin=DEVNULL,
            stdout=DEVNULL,
            stderr=PIPE,
        )
        try:
            # Wait for rosbag to start
            time_helper.sleep(ROSBAG_START_DURATION)
            print("Recording started")

            # Fly
            t0 = monotonic()
            last_x, last_y, last_v = target_path[0]
            print(f"New v = {last_v} @ #1/{len(target_path)}")
            should_have_elapsed = 0.0
            # We skip the first point, since we already flew there
            for index, (x, y, v) in tqdm(
                enumerate(target_path[1:, ...]), total=target_path.shape[0] - 1, disable=False
            ):
                if v != last_v:
                    print(f"New v = {v} @ #{index+1+1}/{len(target_path)}")
                distance = ((x - last_x) ** 2 + (y - last_y) ** 2) ** 0.5
                duration = distance / v
                cf.goTo(
                    array([x, y, Z]),
                    yaw=0.0,
                    duration=duration,
                )
                elapsed = monotonic() - t0
                should_have_elapsed += duration
                to_sleep = should_have_elapsed - elapsed
                if to_sleep > 0:
                    time_helper.sleep(to_sleep)
                last_x, last_y, last_v = x, y, v

            print("Experiment finished normally")

        except KeyboardInterrupt:
            print("Experiment interrupted by user")
            break

        finally:
            print("Stopping the recording...")
            # Stop the rosbag recording
            rosbag_process.send_signal(SIGINT)

            try:
                rosbag_process.wait(timeout=10.0)
            except TimeoutExpired:
                error = rosbag_process.stderr.read().decode().strip()
                if error:
                    print(f"There was an error with rosbag!\n{error}")

                rosbag_process.terminate()
                rosbag_process.wait(timeout=5.0)

            # Land
            print("Landing...")
            cf.land(targetHeight=0.04, duration=LAND_DURATION)
            time_helper.sleep(LAND_DURATION + SIT_DURATION)

        iteration += 1
        is_forward = not is_forward


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
        default=0.5,
        help="The speed to use for the test run.",
    )
    args = parser.parse_args()

    main(
        setting=args.setting,
        controller=args.controller,
        rosbag_path=Path(args.rosbag_name),
        speed=args.speed,
    )
