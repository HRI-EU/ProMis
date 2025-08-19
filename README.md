<p align="center">
  <img src="https://github.com/HRI-EU/ProMis/blob/main/images/logo.png" width=512/>
</p>

# Probabilistic Mission Design

This repository implements Probabilistic Mission Design (ProMis).
ProMis allows the user to formalize their knowledge about local rules, such as traffic regulations, to constrain an agent's actions and motion. 
To do so, we employ probabilistic first-order logic, a mathematical framework combining formal reasoning with probabilistic inference.
This provides a weighted belief whether the encoded rules are satisfied for a state or action. 

Using ProMis, we pave the way towards Constitutional Agents. 
Such agents can give reason for their actions and act in a principled fashion even under uncertainty. 
To this end, ProMis gives high-level, easy-to-understand, and adaptable control over the navigation process, e.g., to effortlessly integrate local laws with operator requirements and environmental uncertainties into logical and spatial constraints. 

Using ProMis, scalar fields of the probability of adhering to the agent's constitution across its state-space are obtained.
These can then be utilized for tasks such as path planning, automated clearance granting, explaining the impact of and optimizing mission parameters.
For instance, the following shows ProMis being applied in a diverse set of scenarios, with a high probability of satisfying all flight restrictions being shown in blue, a low-probability being shown in red, and unsuitable spaces being transparent. 

<p align="center">
  <img src="https://github.com/HRI-EU/ProMis/blob/main/images/landscapes.png"/>
</p>

An example for using the API is available [here](https://github.com/HRI-EU/ProMis/blob/main/examples/promis.ipynb).
Installation instructions and information on how to use ProMis own GUI can be found below.

Please consult and cite the following publications for an in-depth discussion of the methods implemented in this repository.
- [Mission Design for Unmanned Aerial Vehicles using Hybrid Probabilistic Logic Programs](https://arxiv.org/abs/2406.03454).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In 26th IEEE International Intelligent Transportation Systems Conference (ITSC).
- [Towards Probabilistic Clearance, Explanation and Optimization](https://arxiv.org/abs/2406.15088).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In Proceedings of the 2024 International Conference on Unmanned Aircraft Systems (ICUAS).

### Requirements

To use ProMis, the following requirements are needed depending on the features you want to use.
- [Python >= 3.10](https://www.python.org/downloads/) is required to run ProMis itself.
- [Node.js](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) is needed to use ProMis' graphical user interface.
- [GDAL](https://gdal.org/en/stable/download.html) is necessary to work with nautical chart data.

If you have `Docker` installed on your system, we provide instructions in the following section to setup everything in a container.
This way, the installation requirements and software dependencies are all handled automatically.

## Installation

ProMis can be easily installed using the following commands.

```bash
# Installing ProMis and a probabilistic reasoning backend
pip install promis
pip install git+https://github.com/simon-kohaut/problog.git@dcproblog_develop
```

In case you would like to contribute to the project, the following sets up ProMis for development.

```bash
git clone git@github.com:HRI-EU/ProMis.git
cd ProMis
pip install -e ".[dev,doc]"
pip install git+https://github.com/simon-kohaut/problog.git@dcproblog_develop
```

For nautical applications using marine chart data, you can install the additional dependencies with `pip install . "[nautical]"`.

Finally, the installation can be automated in a containerized environment using `Docker` in a `vscode devcontainer` or by running the following commands.

```bash
# Enters the ProMis directiory, builds a new docker image and runs it in interactive mode
docker build . -t promis
docker run -it promis
```

## Graphical User Interface

ProMis comes with a GUI that provides an interactive interface to its features.
To employ the GUI, make sure that you have installed ProMis according to the instructions above.
Then, first run the following commands to start the backend.

```bash
cd gui/backend
fastapi run main.py
```

Afterwards, you can start the frontend using `npm (Node.js)` with the following commands.

```bash
cd gui/frontend
npm install      # Only once or if changes where made
npm run start
```

We also provide Dockerfiles for backend and frontend for an automated setup:

```bash
cd gui
docker compose build
docker compose up
```

Either way, you can open [http://localhost:3000](http://localhost:3000) in a browser of your choice to start interacting with ProMis.

Once you have opened the GUI in your browser, you can check that everything works by doing an example run.
First, from the top-left, click the drone icon and place a marker where you would like to center the mission area.
Second, click the button at the bottom to open the mission design interface.
Here, you can either import ProMis code from disk using the `Import Source` button, or click `Edit`.
You may further configure your run by selecting an origin, height, width (in meters) and a resolution of the mission landscape. 
Afterwards, you can click the `Run` button and wait for the mission landscape to show on the map.

The following shows an example of entering the simple model `landscape(X) :- distance(X, building) > 10; distance(X, primary_road) < 5.`:
<p align="center">
  <img src="https://github.com/HRI-EU/ProMis/blob/main/images/gui_example.png"/>
</p>

For more detailed information, consult the GUI's own [README](https://github.com/HRI-EU/ProMis/blob/main/gui/README.md).

## Documentation

A Jupyter Notebook demonstrating the usage of ProMis is given in the examples folder.
To build the documentation, ensure a full installation with the respective dependencies by running `pip install ".[doc]"`.
Then, using the following commands, trigger Sphinx to create the documentation.

```bash
cd doc
make html
```

To view the documentation, open the file `ProMis/doc/build/html/index.html` using the browser of your choice.

## Quality Assurance

This projects is setup to be checked with `ruff` and `pytest`.
