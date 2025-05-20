# The Constitutional Controller

Official implementation of the paper *The Constitutional Controller: Doubt-Calibrated Steering of Compliant Agents* submitted to *Knowledge Representation & Reasoning in Planning & Scheduling (KR&R in P&S) 2025*.

## Structure

The implementation of *CoCo* builds on [ProMis](https://github.com/HRI-EU/ProMis), a framework for the design and execution of mission plans for autonomous agents.
Most of the implementation is contained in `promis/coco.py` and is then used in `examples/coco/`.

Specifically, in the latter you can find the central `coco.ipynb` notebook demonstrating how to use CoCo.
It also forms the basis of the experiments in the paper, which can be executed by running the `record_test_run.py` script on a computer with a working [Crazyflie 2.1](https://www.bitcraze.io/products/old-products/crazyflie-2-1/) + [ROS2](docs.ros.org/en/rolling) setup.
The file `convert_rosbag_to_csv.py` helps to convert the recorded ROS2 bag files into a CSV format for easier analysis.
All recordings must eventually be stored in `examples/coco/data/`.

## Installation

In case you would like to contribute to the project, the following sets up ProMis for development.

```bash
git clone ###this repository###
cd this_repository
pip install -e ".[dev,doc]"
pip install git+https://github.com/simon-kohaut/problog.git@dcproblog_develop
```

Finally, the installation can be automated in a containerized environment using `Docker` in a `vscode devcontainer` or by running the following commands.

```bash
# Builds a new Docker image and runs it in interactive mode
docker build . -t coco
docker run -it coco
```

## License

We will open-source the implementation of CoCo upon acceptance under the *BSD-3-Clause License*.
