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

# Usage

To install ProMis, please follow the instructions [here](https://hri-eu.github.io/ProMis/installation.html).
For an in-depth walkthrough on applying ProMis in your own applications, you can check our [usage guide](https://hri-eu.github.io/ProMis/usage.html).
An [interactive version](https://github.com/HRI-EU/ProMis/blob/main/examples/usage.ipynb) of the usage guide is also available in this repository. 

# Cite

Please consult and cite the following publications for an in-depth discussion of the methods implemented in this repository.
- [Mission Design for Unmanned Aerial Vehicles using Hybrid Probabilistic Logic Programs](https://arxiv.org/abs/2406.03454).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In 26th IEEE International Intelligent Transportation Systems Conference (ITSC).
- [Towards Probabilistic Clearance, Explanation and Optimization](https://arxiv.org/abs/2406.15088).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In Proceedings of the 2024 International Conference on Unmanned Aircraft Systems (ICUAS).

## Documentation

ProMis' documentation is available [online](https://hri-eu.github.io/ProMis).
It can also be built locally with the following commands.

```bash
git clone 
pip install ".[doc]"

mkdir -p doc/source/notebooks
cp examples/*.ipynb doc/source/notebooks
sphinx-build -b html doc/source _build/html
```

To view the documentation, open the file `ProMis/doc/build/html/index.html` using the browser of your choice.
