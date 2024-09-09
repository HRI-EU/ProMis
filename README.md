<p align="center">
  <img src="https://github.com/HRI-EU/ProMis/blob/main/logo.png" width=512/>
</p>

# Probabilistic Mission Design

This repository implements Probabilistic Mission Design (ProMis), i.e., employing inference over a declarative language (hybrid probabilistic logic programs) to provide a foundation for creating constitutional agents. ProMis aims to give high-level, easy-to-understand, and adaptable control over the navigation process, e.g., to effortlessly integrate local laws with operator requirements and environmental uncertainties into logical and spatial constraints. Using ProMis, scalar fields of the probability of adhering to the agent's constitution across its state-space are obtained and utilized for path planning and trajectory clearance, explaining the impact of and optimizing mission parameters.

Please consult the following publications for an in-depth discussion of the methods implemented in this repository.
- [Mission Design for Unmanned Aerial Vehicles using Hybrid Probabilistic Logic Programs](https://arxiv.org/abs/2406.03454).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In 26th IEEE International Intelligent Transportation Systems Conference (ITSC).
- [Towards Probabilistic Clearance, Explanation and Optimization](https://arxiv.org/abs/2406.15088).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In Proceedings of the 2024 International Conference on Unmanned Aircraft Systems (ICUAS).

## Installation

First, clone the repository to create a local workspace using `git clone git@github.com:HRI-EU/ProMis.git`.
It is recommended to employ a `Python virtualenv` or similar to contain the installed packages in their own space:

```bash
python -m venv venv
source venv/bin/activate
```

Further, we must install `Problog` with support for Distributional Clauses (DC) and Sentential Decision Diagrams (SDD).
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

This projects is setup to be checked against `black` and `ruff`.
For ease of use, they can both be called by running `check.sh` in the ProMis root directory.
For tests with `pytest`, we employ `Hypothesis` to enhance coverage.
