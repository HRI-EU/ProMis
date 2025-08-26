"""This module provides an implementation of the Unscented Kalman filter
   for non-linear state estimation."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from collections.abc import Callable
from copy import deepcopy

# Third Party
from numpy import array, hstack, ndarray, outer, tensordot, vectorize, vstack
from numpy.linalg import inv
from pandas import DataFrame, concat
from scipy.linalg import cholesky

# ProMis
from promis.models import Gaussian


class UnscentedKalman:

    """The unscented Kalman filter for non-linear state estimation.

    This filter behaves similarly to the standard Kalman filter, but utilizes the so-called
    unscented transform to approximate gaussian distributions by sampling from the given
    nonlinear models to estimate state variables whose process and/or relation to
    the measured properties cannot be accurately described by a linear model.

    Examples:
        To use the UKF, here we utilize numpy's functionality.

        >>> from numpy import array
        >>> from numpy import cos
        >>> from numpy import eye
        >>> from numpy import sin
        >>> from numpy import vstack

        Setup the model. In this case, we track a sine wave.
        Thereby we choose the transition model and its jacobian, as well as the linear
        measurement model, like so.

        >>> f = lambda x: sin(x)
        >>> F = lambda x: array([cos(x)])
        >>> H = lambda x: array([[1.0]])
        >>> h = lambda x: x

        Furthermore, we assume the following noise on the process and measurements.

        >>> Q = eye(1)
        >>> R = eye(1)

        Our initial belief is at 0.

        >>> mean = vstack([0.0])
        >>> covariance = array([[1.0]])
        >>> estimate = Gaussian(mean, covariance)

        Then, we initialize the filter. This model has not input, so we ignore B.

        >>> kalman = UnscentedKalman(estimate, f, h, Q, R)

        We first predict with the provided model and then correct the prediction with a
        measurement of the true position.

        >>> kalman.predict()
        >>> kalman.correct(array([5.]))

    Args:
        estimate: Initial belief, i.e. the gaussian that describes your initial guess
            on the state and your uncertainty
        f: Non-linear state transition model that describes the state's evolution
            from one timestep to the next
        h: Non-linear measurement model that maps a state variable into the measured space
        Q: Process noise matrix, i.e. the covariance of the state transition (n, n)
        R: Measurement noise matrix, i.e. the covariance of the sensor readings (m, m)
        alpha: Spread of sample points, pick between 0. and 1.
        beta: Sigma point parameter, 2 is optimal for gaussian problems
        kappa: Sigma point parameter, a common choice for kappa is to subtract 3
                from your state's dimension
        keep_trace: Flag for tracking filter process

    References:
        - https://en.wikipedia.org/wiki/Unscented_Kalman_filter
    """

    def __init__(
        self,
        estimate: Gaussian,
        f: Callable[..., ndarray],
        h: Callable[..., ndarray],
        Q: ndarray,
        R: ndarray,
        alpha: float = 1.0,
        beta: float = 2.0,
        kappa: float = 1.0,
        keep_trace: bool = False,
    ):
        # Initial belief
        self.estimate = deepcopy(estimate)
        self.prediction = deepcopy(estimate)

        # Model specification
        self.f = f
        self.h = h
        self.Q = Q
        self.R = R
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa

        # Residual and its covariance matrix
        self.y: ndarray
        self.S: ndarray

        # Predicted sigma points and measurements
        self.Y: ndarray
        self.Z: ndarray

        # Kalman gain
        self.K: ndarray

        # Merwe initial points and weights
        self.X: ndarray
        self.mean_weights: ndarray
        self.cov_weights: ndarray
        self.setup_weights()

        # Objects for process tracing
        self.keep_trace = keep_trace
        self.predictions = DataFrame(columns=["x", "P", "X", "Y"])
        self.estimates = DataFrame(columns=["x", "P", "z"])

    def setup_weights(self) -> None:
        """Computes mean and covariance weights for unscented transform"""

        # Aliases for calculation
        n = self.estimate.x.size
        l = self.alpha**2 * n + self.kappa  # noqa: E741

        # Weights for mean and covariance
        self.mean_weights = array([l / (n + l)] + [1 / (2 * (n + l))] * (2 * n))
        self.cov_weights = array(
            [l / (n + l) + 1 - self.alpha**2 + self.beta] + [1 / (2 * (n + l))] * (2 * n)
        )

    def compute_sigma_points(self) -> None:
        """Calculates van der Merwe's sigma points"""

        # Compute the distances for each point
        distance_factor = self.estimate.x.size * (1 + self.alpha**2) + self.kappa
        distances = cholesky(distance_factor * self.estimate.P)

        # Sigma points
        self.X = hstack([self.estimate.x, self.estimate.x + distances, self.estimate.x - distances])

    def predict(self, **kwargs) -> None:
        """Predict a future state based on a linear forward model with optional system input.

        Args:
            **kwargs: Arguments that are passed to forward model
        """

        # Compute and propagate Merwe points
        self.compute_sigma_points()
        self.Y = vectorize(lambda x: self.f(x, **kwargs), signature="(m)->(n)")(self.X.T).T

        # Predict next state as mean of distribution
        self.prediction = Gaussian(
            vstack(self.mean_weights @ self.Y.T),
            tensordot(
                self.cov_weights,
                [outer(y - self.prediction.x.T, y - self.prediction.x.T) for y in self.Y.T],
                axes=1,
            )
            + self.Q,
        )

        # Append prediction data to trace
        if self.keep_trace:
            new = DataFrame(
                {
                    "x": (self.prediction.x.copy(),),
                    "P": (self.prediction.P.copy(),),
                    "X": (deepcopy(self.X),),
                    "Y": (deepcopy(self.Y),),
                }
            )
            self.predictions = concat([self.predictions, new], ignore_index=True)

    def correct(self, z: ndarray, **kwargs) -> None:
        """Correct a state prediction based on a measurement."""

        # Check for differing measurement model
        h = kwargs.pop("h", self.h)

        # Compute measurement distribution
        self.Z = vectorize(lambda y: h(y, **kwargs), signature="(m)->(n)")(self.Y.T).T
        mean_z = vstack(self.mean_weights @ self.Z.T)

        # Compute the residual and its covariance
        self.y = z - mean_z
        self.S = (
            tensordot(
                self.cov_weights, [outer(z - mean_z.T, z - mean_z.T) for z in self.Z.T], axes=1
            )
            + self.R
        )

        # Compute the new Kalman gain
        self.K = tensordot(
            self.cov_weights,
            [outer(y - self.prediction.x.T, z - mean_z.T) for y, z in zip(self.Y.T, self.Z.T)],
            axes=1,
        ) @ inv(self.S)

        # Estimate new state
        self.estimate = Gaussian(
            self.prediction.x + self.K @ self.y,
            self.prediction.P - self.K @ self.S @ self.K.T,
        )

        # Append estimation data to trace
        if self.keep_trace:
            new = DataFrame(
                {"x": (self.estimate.x.copy(),), "P": (self.estimate.P.copy(),), "z": (z.copy(),)}
            )
            self.estimates = concat([self.estimates, new], ignore_index=True)
