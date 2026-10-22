<p align="center">
  <img src="https://github.com/HRI-EU/ProMis/blob/main/images/logo.png" width=512/>
</p>

# Probabilistic Mission Design

<p align="center">
  <a href="https://github.com/simon-kohaut/resin">Resin</a> reasoning ·
  <b>ProMis</b> mission design ·
  <a href="https://github.com/simon-kohaut/CoFi">CoFi</a> tracking ·
  <a href="https://github.com/simon-kohaut/CoCo">CoCo</a> control
</p>

This repository implements Probabilistic Mission Design (ProMis).
ProMis enables users to formalize their knowledge of local rules, such as traffic regulations, to constrain an agent's actions and movements. 
To achieve this, we employ probabilistic first-order logic, a mathematical framework that combines formal reasoning with probabilistic inference.
The rules are written in [Resin](https://github.com/simon-kohaut/resin), a reactive probabilistic logic language whose syntax and semantics are described in [its language reference](https://github.com/simon-kohaut/resin/blob/main/docs/language.md).
Using ProMis, scalar fields of the probability of adhering to the agent's constitution are obtained across its state space.

<p align="center">
  <img src="https://github.com/HRI-EU/ProMis/blob/main/images/landscapes.png"/>
</p>

Building on these landscapes, we further provide [CoFi](https://github.com/simon-kohaut/CoFi), which tracks agents that are expected to follow their constitution, and [CoCo](https://github.com/simon-kohaut/CoCo), steering agents to comply with it.
The following shows ProMis being applied in a diverse set of scenarios, with a high probability of satisfying all flight restrictions being shown in blue, a low probability being shown in red, and unsuitable spaces being transparent.

# Installation & Usage

To install ProMis, please follow the instructions [here](https://hri-eu.github.io/ProMis/installation.html).
For an in-depth walkthrough on applying ProMis in your own applications, you can check our [usage guide](https://hri-eu.github.io/ProMis/notebooks/usage.html).
An [interactive version](https://colab.research.google.com/github/HRI-EU/ProMis/blob/main/examples/usage.ipynb) of the usage guide is also available.

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

## Citation

If you use ProMis, please cite the paper below.

```bibtex
@ARTICLE{11193664,
  author={Kohaut, Simon and Flade, Benedict and Ochs, Daniel and Dhami, Devendra Singh and Eggert, Julian and Kersting, Kristian},
  journal={IEEE Transactions on Intelligent Transportation Systems}, 
  title={Probabilistic Mission Design for Neuro-Symbolic Unmanned Aircraft Systems}, 
  year={2025},
  volume={26},
  number={12},
  pages={22751-22760},
  doi={10.1109/TITS.2025.3609835}
}
```

You may further be interested in consulting the following accompanying works:
- [Mission Design for Unmanned Aerial Vehicles using Hybrid Probabilistic Logic Programs](https://arxiv.org/abs/2406.03454).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In Proceedings of the 26th IEEE International Intelligent Transportation Systems Conference (ITSC).
- [StaR Maps: Unveiling Uncertainty in Geospatial Relations](https://arxiv.org/abs/2412.18356).
  Benedict Flade, Simon Kohaut, Devendra Singh Dhami, Kristian Kersting.
  In Proceedings of the 27th IEEE International Intelligent Transportation Systems Conference (ITSC).
- [Hybrid Many-Objective Optimization in Probabilistic Mission Design for Compliant and Effective UAV Routing](https://dl.acm.org/doi/pdf/10.1145/3742440).
  Simon Kohaut, Nikolas Hohmann, Sebastian Brulin, Benedict Flade, Julian Eggert, Markus Olhofer, Jürgen Adamy, Devendra Dhami, Kristian Kersting.
  In the ACM Journal on Autonomous Transportation Systems (JATS).
- [Towards Probabilistic Clearance, Explanation and Optimization](https://arxiv.org/abs/2406.15088).
  Simon Kohaut, Benedict Flade, Devendra Singh Dhami, Julian Eggert, Kristian Kersting.
  In Proceedings of the 2024 IEEE International Conference on Unmanned Aircraft Systems (ICUAS).

