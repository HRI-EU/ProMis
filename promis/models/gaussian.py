"""This module includes an abstraction of gaussian distributions."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from typing import cast

# Third Party
from numpy import ndarray, vstack
from scipy.stats import multivariate_normal


class Gaussian:

    """A weighted multivariate gaussian distribution.

    Examples:
        A Gaussian can be simply created from a mean and covarinace vector (and an optional weight):

        >>> from numpy import array
        >>> from numpy import vstack
        >>> mean = vstack([0.0, 0.0])
        >>> covariance = array([[1.0, 0.0], [0.0, 1.0]])
        >>> N = Gaussian(mean, covariance, weight=1.0)
        >>> N(vstack([0.0, 0.0])).item()  # doctest: +ELLIPSIS
        0.159...

        Two Gaussians are equal if and only if all attributes are equal:

        >>> N == N
        True
        >>> other_covariance = array([[99.0, 0.0], [0.0, 99.0]])
        >>> other_N = Gaussian(mean, other_covariance, weight=1.0)
        >>> other_N(vstack([10.0, 10.0])).item()  # doctest: +ELLIPSIS
        0.000585...
        >>> N == other_N
        False

        Sampling from Gaussians is straight forward as well.
        Either a single

        >>> sample = N.sample()
        >>> sample.shape
        (2, 1)

        or many samples

        >>> sample = N.sample(100)
        >>> sample.shape
        (2, 100)

        can be generated at once.

    Args:
        mean: The mean of the distribution as column vector, of dimension ``(n, 1)``
        covariance: The covariance matrix of the distribution, of dimension ``(n, n)``
        weight: The weight of the distribution, e.g. within a mixture model

    References:
        - https://en.wikipedia.org/wiki/Multivariate_normal_distribution
    """

    def __init__(self, mean: ndarray, covariance: ndarray, weight: float = 1.0):
        # Sanity checks on given parameters
        assert len(mean.shape) == 2 and mean.shape[1] == 1, "Mean needs to be a column vector!"
        assert len(covariance.shape) == 2, "Covariance needs to be a 2D matrix!"
        assert covariance.shape[0] == covariance.shape[1], "Covariance needs to be a square matrix!"
        assert covariance.shape[0] == mean.shape[0], "Dimensions of mean and covariance don't fit!"

        # Assign values
        self.mean = mean
        self.covariance = covariance
        self.weight = weight

        # Abstract away from the scipy implementation
        self.distribution = multivariate_normal(mean=self.mean.T[0], cov=self.covariance)

    @property
    def x(self) -> ndarray:
        return self.mean

    @property
    def P(self) -> ndarray:
        return self.covariance

    @property
    def w(self) -> float:
        return self.weight

    def sample(self, number_of_samples: int = 1) -> ndarray:
        """Draw a number of samples following this Gaussian's distribution.

        Args:
            number_of_samples: The number of samples to draw

        Returns:
            The drawn samples
        """

        assert number_of_samples >= 1, "Number of samples cannot be negative or zero!"

        # Draw samples and ensure shape of [M, #samples]
        samples = self.distribution.rvs(size=number_of_samples)
        samples = samples.T if number_of_samples > 1 else vstack(samples)

        return cast(ndarray, samples)

    def cdf(self, x: ndarray) -> float:
        """Compute the CDF as integral of the PDF from negative infinity up to x.

        Args:
            x: The upper bound of the integral

        Returns:
            The probability of a value being less than x
        """

        return self.weight * cast(float, self.distribution.cdf(x))

    def __call__(self, value: ndarray) -> float:
        """Evaluate the gaussian at the given location, i.e. obtain the probability density.

        Args:
            value: Where to evaluate the gaussian, of dimension ``(n, 1)``

        Returns:
            The probability density at the given location
        """

        # Compute and return weighted probability density function
        return self.weight * cast(float, self.distribution.pdf(value.T[0]))

    def __eq__(self, other) -> bool:
        """Checks if two multivariate normal distributions are equal.

        Args:
            other: The distribution to compare within

        Returns:
            Whether the two distributions are the same
        """

        return (
            cast(bool, (self.mean == other.mean).all().item())
            and cast(bool, (self.covariance == other.covariance).all().item())
            and self.weight == other.weight
        )
