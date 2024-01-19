# ProMis - Probabilistic Mission Design using Logic Programming

The goal of this repository is to provide an implementation and representation of inference on probabilistic logic programs that enables advanced, high level mission design.
Probabilistic Mission Design (ProMis) aims at giving high-level control over the navigation of vehicles, e.g., to effortlessly integrate local laws and regulations, by employing declarative, probabilistic modeling languages into the navigation process. 

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
pip install pyro-ppl graphviz
pip install --upgrade --force-reinstall --no-deps --no-binary :all: pysdd

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

To build the documentation, ensure a full installation with the respective dependencies by running `pip install .[doc]`.
Then, using the following commands trigger Sphinx to create the documentation.

```bash
cd doc
make html
```

To view the documentation, open the file `ProMis/doc/build/html/index.html` with the browser of your choice.
