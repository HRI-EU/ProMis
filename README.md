# The Constitutional Controller

Official implementation of the paper *The Constitutional Controller: Doubt-Calibrated Steering of Compliant Agents* submitted to ECAI 2025.

## Structure

The implementation builds on [ProMis](https://github.com/HRI-EU/ProMis), a framework for the design and execution of mission plans for autonomous agents.
Most of the implementation is contained in `promis/coco.py` and is then used in `examples/`.

Specifically, in the latter you can find the central `coco.ipynb` notebook demonstrating how to use CoCo.
It also forms the basis of the experiments in the paper, which can be executed by running the `record_test_run.py` script on a computer with a working [Crazyflie 2.1](https://www.bitcraze.io/products/old-products/crazyflie-2-1/) + [ROS2](docs.ros.org/en/rolling) setup.
The file `convert_rosbag_to_csv.py` helps to convert the recorded ROS2 bag files into a CSV format for easier analysis.

## Installation

The following commands create a local working environment for using this repository.
For this, it is recommended to use [virtual environments](https://docs.python.org/3/library/venv.html) to manage the Python dependencies.

```bash
# This step is optional but highly recommended
python -m venv venv
source venv/bin/activate    # Linux
.\venv\Scripts\activate     # Windows

# Install all dependencies
pip install -e ".[dev]"
```

If you have `Docker` installed on your system, we provide instructions in the following section to set up everything in a container.
You can use it to automate the above process in a containerized environment by running the following instead:

```bash
# Builds a new Docker image and runs it in interactive mode
docker build . -t coco
docker run -it coco
```

## License

We will open-source this complete implementation upon acceptance.
