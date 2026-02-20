<p align="center">
  <img src="https://github.com/HRI-EU/ProMis/blob/main/images/logo.png" width=512/>
</p>

# Probabilistic Mission Design

This repository implements Probabilistic Mission Design (ProMis).
ProMis enables users to formalize their knowledge of local rules, such as traffic regulations, to constrain an agent's actions and movements. 
To achieve this, we employ probabilistic first-order logic, a mathematical framework that combines formal reasoning with probabilistic inference.
This provides a weighted belief whether the encoded rules are satisfied for a state or action. 

Using ProMis, we pave the way towards Constitutional Agents. 
Such agents can give reasons for their actions and act in a principled fashion even under uncertainty. 
To this end, ProMis provides high-level, easy-to-understand, and adaptable control over the navigation process, for example, to seamlessly integrate local laws, operator requirements, and environmental uncertainties into logical and spatial constraints. 

Using ProMis, scalar fields of the probability of adhering to the agent's constitution are obtained across its state space.
These can then be utilized for tasks such as path planning, automated clearance granting, explaining the impact of, and optimizing mission parameters.
For instance, the following shows ProMis being applied in a diverse set of scenarios, with a high probability of satisfying all flight restrictions being shown in blue, a low probability being shown in red, and unsuitable spaces being transparent. 

<p align="center">
  <img src="https://github.com/HRI-EU/ProMis/blob/main/images/landscapes.png"/>
</p>

# Usage

To install ProMis, please follow the instructions [here](https://hri-eu.github.io/ProMis/installation.html).
For an in-depth walkthrough on applying ProMis in your own applications, you can check our [usage guide](https://hri-eu.github.io/ProMis/notebooks/usage.html).
An [interactive version](https://colab.research.google.com/github/HRI-EU/ProMis/blob/main/examples/usage.ipynb) of the usage guide is also available. 

# Cite

Please consult and cite the following publications for an in-depth discussion of the methods implemented in this repository.
- [Mission Design for Unmanned Aerial Vehicles using Hybrid Probabilistic Logic Programs](https://arxiv.org/abs/2406.03454).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In Proceedings of the 26th IEEE International Intelligent Transportation Systems Conference (ITSC).
- [Towards Probabilistic Clearance, Explanation and Optimization](https://arxiv.org/abs/2406.15088).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In Proceedings of the 2024 IEEE International Conference on Unmanned Aircraft Systems (ICUAS).
  
For specific use cases, please cite the following works as well.
- Environment Representation: [StaR Maps: Unveiling Uncertainty in Geospatial Relations](https://arxiv.org/abs/2412.18356).
  Benedict Flade, Simon Kohaut, Devendra Singh Dhami, Kristian Kersting.
  In Proceedings of the 27th IEEE International Intelligent Transportation Systems Conference (ITSC).
- Planning: [Hybrid Many-Objective Optimization in Probabilistic Mission Design for Compliant and Effective UAV Routing](https://dl.acm.org/doi/pdf/10.1145/3742440).
  Simon Kohaut, Nikolas Hohmann, Sebastian Brulin, Benedict Flade, Julian Eggert, Markus Olhofer, Jürgen Adamy, Devendra Dhami, Kristian Kersting.
  In the ACM Journal on Autonomous Transportation Systems (JATS).
- Tracking: [The Constitutional Filter: Bayesian Estimation of Compliant Agents](https://arxiv.org/abs/2412.18347).
  Simon Kohaut, Felix Divo, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In Proceedings of the 2025 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS).
- Control: [The Constitutional Controller: Doubt-calibrated Steering of Compliant Agents](https://arxiv.org/abs/2507.15478?).
  Simon Kohaut, Felix Divo, Navid Hamid, Benedict Flade, Julian Eggert, Devendra Singh Dhami, Kristian Kersting.
  Arxiv preprint.

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

## Contributing

This project is set up to be checked and formatted with `ruff check` and `ruff format`.
Use `pytest` to run automated tests.

## License

Copyright (c) 2023 Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors.
See [LICENSE.md](https://github.com/HRI-EU/ProMis/blob/main/LICENSE.md) for details.
