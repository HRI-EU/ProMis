ProMis - Probabilistic Mission Design
=====================================

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

.. image:: ../../images/landscapes.png
    
.. toctree::
    :hidden:

    installation
    notebooks/usage
    gui
    api
