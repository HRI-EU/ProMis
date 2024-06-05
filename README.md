# ProMis - Probabilistic Mission Design

This repository implements Probabilistic Mission Design (ProMis), i.e., employing inference over a declarative language (hybrid probabilistic logic programs) to provide a foundation for creating constitutional agents. ProMis aims to give high-level, easy-to-understand, and adaptable control over the navigation process, e.g., to effortlessly integrate local laws with operator requirements and environmental uncertainties into logical and spatial constraints. Using ProMis, scalar fields of the probability of adhering to the agent's constitution across its state-space are obtained and utilized for path planning and trajectory clearance, explaining the impact of and optimizing mission parameters.

For an in-depth discussion of the methods implemented in this repository, please consult the following publications.
- [Mission Design for Unmanned Aerial Vehicles using Hybrid Probabilistic Logic Programs](https://www.aiml.informatik.tu-darmstadt.de/papers/kohaut2023promis.pdf).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In 26th IEEE International Intelligent Transportation Systems Conference (ITSC).
- [Towards Probabilistic Clearance, Explanation and Optimization](https://www.aiml.informatik.tu-darmstadt.de/papers/kohaut2024ceo.pdf).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In Proceedings of the 2024 International Conference on Unmanned Aircraft Systems (ICUAS).

## Installation

First, clone the repository to create a local workspace using `git clone git@github.com:HRI-EU/ProMis.git`.
It is recommandable to employ a `Python virtualenv` or similar in order to contain the installed packages in their own space:

```bash
python -m venv venv
source venv/bin/activate
```

Further, we need to install `Problog` with support for Distributional Clauses (DC) and Sentential Decision Diagrams (SDD).
To do so, run the following commands.

```bash
# Install separate pip dependencies
pip install pyro-ppl graphviz git+https://github.com/wannesm/PySDD.git#egg=PySDD

# Clone and install Problog with distributional clauses
# This contains bugfixes and features that are not part of the official release yet
cd ProMis/external
git clone https://github.com/simon-kohaut/problog.git
cd problog 
git checkout dcproblog_develop
pip install .
```

Finally, it is time to install `promis` as a Python package.

```bash
cd ProMis
pip install .
```

You can automate this process in a containerized environment using `Docker` and running the following instead.

```bash
cd ProMis
docker build . -t promis
docker run -it promis
```

## Usage

ProMis can be employed by first deciding the mission's setting and rules in the form of a Hybrid Probabilistic Logic Program (agent constitution).
Examples for this can be found in the `/models` folder.
Here, we will use the following constitution:
```prolog
% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Mission parameters and UAV properties
1.0::standard; 0.0::special.        % Standard license
initial_charge ~ normal(90, 5).     % UAV battery state and discharge rate
charge_cost ~ normal(-0.2, 0.1).
weight ~ normal(2.0, 0.1).          % UAV take-off-mass
1/10::fog; 9/10::clear.             % Mostly clear weather
0.0::high_altitude.                 % UAV will not fly at high altitudes


% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Mission rules
% Visual line of sight
vlos(X, Y) :- 
    fog, distance(X, Y, operator) < 250;
    clear, distance(X, Y, operator) < 500.

% Simplified OPEN flight category
open_flight(X, Y) :- 
    standard, vlos(X, Y), weight < 25.

% Sufficient charge is defined to be
% enough to return to the operator
can_return(X, Y) :-
    B is initial_charge,
    O is charge_cost,
    D is distance(X, Y, operator),
    0 < B + (2 * O * D).

% Special permit for parks and roads
permit(X, Y) :- 
    over(X, Y, park); 
    distance(X, Y, primary) < 15;
    distance(X, Y, secondary) < 10;
    distance(X, Y, tertiary) < 5.

% %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% The Probabilistic Mission Landscape
landscape(X, Y) :- 
    permit(X, Y), open_flight(X, Y), can_return(X, Y);
    special, high_altitude, can_return(X, Y).
```

Once the rules have been decided, the `ProMis` class can be used to generate a Probabilistic Mission Landscape (PML) in the relevant area.

```python
import matplotlib.pyplot as plt
from promis import ProMis
from promis.geo import LocationType, PolarLocation, CartesianLocation

# ProMis Parameters
dimensions = (1000.0, 1000.0)  # Meters
resolution = (100, 100)        # Pixels
spatial_samples = 50           # How many maps to generate to compute statistics
model = "Park"                 # Hybrid ProbLog to be used
types = [                      # Which types to load and compute relations for
    LocationType.PARK,
    LocationType.PRIMARY,
    LocationType.SECONDARY,
    LocationType.TERTIARY,
]  
tu_darmstadt = PolarLocation(latitude=49.878091, longitude=8.654052)

# Setup engine
pmd = ProMis(tu_darmstadt, dimensions, resolution, types, spatial_samples)

# Set parameters that are unrelated to the loaded map data
# Here, we imagine the operator to be situated at the center of the mission area
pmd.create_from_location(CartesianLocation(0.0, 0.0, location_type=LocationType.OPERATOR))

# Generate landscape
with open(f"../models/{model}.pl", "r") as model_file:
    landscape, time = pmd.generate(logic=model_file.read(), n_jobs=8)

# Show result
plt.imshow(landscape.data.T)
```
<img src="https://github.com/HRI-EU/ProMis/blob/main/examples/pml.png" width="256">

Note that each point in this landscape expresses an i.i.d. probability of the constitution being adhered to at that location.
We can then integrate this landscape into the trajectory planning process, search for the most optimal mission setting or explain how mission parameters influence the obtained routes. 

## Documentation

To build the documentation, ensure a full installation with the respective dependencies by running `pip install ".[doc]"`.
Then, using the following commands trigger Sphinx to create the documentation.

```bash
cd doc
make html
```

To view the documentation, open the file `ProMis/doc/build/html/index.html` with the browser of your choice.

## Quality Assurance

This projects is setup to be checked against `black` and `ruff`.
For ease of use, they can both be called by running `check.sh` in the ProMis root directory.
For tests with `pytest`, we employ `Hypothesis` to enhance coverage.
