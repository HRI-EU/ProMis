"""This module implements Gaussian Mixture Models (GMM)."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from copy import deepcopy

# Third Party
from numpy import array, ndarray
from numpy.linalg import inv

# ProMis
from promis.models.gaussian import Gaussian


class GaussianMixture:

    """The Gaussian Mixture Model (GMM) for representing multi-modal probability distribution.

    Args:
        components: An initial list of components to consider in this GMM
    """

    def __init__(self, components: list[Gaussian] | None = None):
        # Setup attributes
        self.components: list[Gaussian] = components if components else []

    def __iter__(self):
        return self.components.__iter__()

    def __getitem__(self, key: int) -> Gaussian:
        return self.components[key]

    def __len__(self) -> int:
        return len(self.components)

    def __add__(self, other: "GaussianMixture") -> "GaussianMixture":
        return GaussianMixture(self.components + other.components)

    def append(self, component: Gaussian):
        """Appends a new Gaussian to this Mixture's list of components.

        Args:
            component: The new Gaussian to append
        """

        self.components.append(component)

    def modes(self, threshold: float = 0.5) -> list[ndarray]:
        """Extract all modes of the mixture model that are above a set threshold.

        Args:
            threshold: Weight that a component needs to have to be considered

        Returns:
            The locations of all modes with weight larger than the threshold
        """

        # Memory for all estimated modes
        modes: list[ndarray] = []

        # Every component with sufficient weight is considered to be a target
        for component in self.components:
            if component.w > threshold:
                # A component with weight over 1 represents multiple targets
                modes += [component.x for _ in range(int(round(component.w)))]

        # Return all extracted modes
        return modes

    def prune(self, threshold: float, merge_distance: float, max_components: int) -> None:
        """Reduces the number of gaussian mixture components.

        Args:
            threshold: Truncation threshold s.t. components with weight < threshold are removed
            merge_distance: Merging threshold s.t. components 'close enough' will be merged
            max_components: Maximum number of gaussians after pruning
        """

        # Select a subset of components to be pruned
        selected = [component for component in self.components if component.w > threshold]

        # Create new list for pruned mixture model
        pruned: list[Gaussian] = []

        # While candidates for pruning exist ...
        while selected:
            # Find mean of component with maximum weight
            index = max(range(len(selected)), key=lambda index: selected[index].w)

            mean = selected[index].x

            # Select components to be merged and remove merged from selected
            mergeable = [
                c
                for c in selected
                if ((c.x - mean).T @ inv(c.P) @ (c.x - mean)).item() <= merge_distance
            ]
            selected = [c for c in selected if c not in mergeable]

            # Compute new mixture component
            merged_weight = sum([component.w for component in mergeable])
            merged_mean = array(
                sum([component.w * component.x for component in mergeable]) / merged_weight
            )
            merged_covariance = array(
                sum(
                    [
                        component.w * (component.P + (mean - component.x) @ (mean - component.x).T)
                        for component in mergeable
                    ]
                )
                / merged_weight
            )

            # Store the component
            pruned.append(Gaussian(merged_mean, merged_covariance, merged_weight))

        # Remove components with minimum weight if maximum number is exceeded
        while len(pruned) > max_components:
            # Find index of component with minimum weight
            index = min(range(len(pruned)), key=lambda index: pruned[index].w)

            # Remove the component
            del pruned[index]

        # Update GMM with pruned model
        self.components = deepcopy(pruned)
