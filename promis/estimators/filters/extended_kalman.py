"""This module implements the extended Kalman filter for non-linear state
   estimation."""

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
from numpy import ndarray
from numpy.linalg import inv
from pandas import DataFrame, concat

# ProMis
from promis.models import Gaussian


class ExtendedKalman:

    """The extended Kalman filter for non-linear state estimation.

    This filter behaves similarly to the standard Kalman filter, but utilizes nonlinear
    models and their jacobian matrix to estimate state variables whose process and/or relation to
    the measured properties cannot be accurately described by a linear model.

    Examples:
        Start by importing the necessary numpy functions.

        >>> from numpy import array
        >>> from numpy import cos
        >>> from numpy import eye
        >>> from numpy import sin
        >>> from numpy import vstack

        Setup the model. In this case, we track a sine wave.
        Thereby we choose the transition model and its jacobian, as well as the linear
        measurement model, like so.

        >>> f = lambda x: sin(x)
        >>> F = lambda x: cos(x)
        >>> H = lambda x: eye(1)
        >>> h = lambda x: x

        Furthermore, we assume the following noise on the process and measurements.

        >>> Q = eye(1)
        >>> R = eye(1)

        Our initial belief is at 0.

        >>> mean = vstack([0.0])
        >>> covariance = eye(1)
        >>> estimate = Gaussian(mean, covariance)

        Then, we initialize the filter.

        >>> kalman = ExtendedKalman(estimate, F, f, H, h, Q, R)

        We first predict with the provided model and then correct the prediction with a
        measurement of the true position.

        >>> kalman.predict()
        >>> kalman.correct(array([5.]))

    Args:
        estimate: Initial belief, i.e. the gaussian that describes your initial guess
            on the state and your uncertainty
        F: Linearized state transition model, i.e. the jacobi matrix of f (n, n)
        f: Non-linear state transition model that describes the state's evolution
            from one timestep to the next
        H: Linearized measurement model, i.e. the jacobi matrix of h (m, n)
        h: Non-linear measurement model that maps a state variable into the measured space
        Q: Process noise matrix, i.e. the covariance of the state transition (n, n)
        R: Measurement noise matrix, i.e. the covariance of the sensor readings (m, m)
        keep_trace: Flag for tracking filter process

    References:
        - https://en.wikipedia.org/wiki/Extended_Kalman_filter
    """

    def __init__(
        self,
        estimate: Gaussian,
        F: ndarray | Callable[..., ndarray],
        f: Callable[..., ndarray],
        H: ndarray | Callable[..., ndarray],
        h: Callable[..., ndarray],
        Q: ndarray,
        R: ndarray,
        keep_trace: bool = False,
    ):
        # Initial belief
        self.estimate = deepcopy(estimate)
        self.prediction = deepcopy(estimate)

        # Model specification
        self.f = f
        self.F = F
        self.h = h
        self.H = H
        self.Q = Q
        self.R = R

        # Residual and its covariance matrix
        self.y: ndarray
        self.S: ndarray

        # Kalman gain
        self.K: ndarray

        # Objects for process tracing
        self.keep_trace = keep_trace
        self.predictions = DataFrame(columns=["x", "P", "F"])
        self.estimates = DataFrame(columns=["x", "P", "z"])

    def predict(self, **kwargs) -> None:
        """Predict a future state based on a linear forward model with optional system input."""

        # Linearize and predict state transition
        F = self.F(self.prediction.x, **kwargs) if callable(self.F) else self.F
        self.prediction = Gaussian(
            self.f(x=self.estimate.x, **kwargs),
            F @ self.estimate.P @ F.T + self.Q,
        )

        # Append prediction data to trace
        if self.keep_trace:
            new = DataFrame(
                {
                    "x": (self.prediction.x.copy(),),
                    "P": (self.prediction.P.copy(),),
                    "F": (F.copy(),),
                }
            )
            self.predictions = concat([self.predictions, new], ignore_index=True)

    def correct(self, z: ndarray, **kwargs) -> None:
        """Correct a state prediction based on a measurement."""

        # Check for differing measurement model
        H, h = kwargs.pop("H", self.H), kwargs.pop("h", self.h)

        # Approximate about predicted state
        h_x: ndarray = H(self.prediction.x, **kwargs) if callable(H) else H

        # Compute the residual and its covariance
        self.y = z - h(self.prediction.x, **kwargs)
        self.S = h_x @ self.prediction.P @ h_x.T + self.R

        # Compute the new Kalman gain
        self.K = self.prediction.P @ h_x.T @ inv(self.S)

        # Estimate new state
        self.estimate = Gaussian(
            self.prediction.x + self.K @ self.y, self.prediction.P - self.K @ self.S @ self.K.T
        )

        # Append estimation data to trace
        if self.keep_trace:
            new = DataFrame(
                {"x": (self.estimate.x.copy(),), "P": (self.estimate.P.copy(),), "z": (z.copy(),)}
            )
            self.estimates = concat([self.estimates, new], ignore_index=True)
