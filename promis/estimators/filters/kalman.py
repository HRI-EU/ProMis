"""This module implements the Kalman filter for state estimation based on
   linear state transition and measurement models."""

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


class Kalman:

    """The Kalman filter for linear state estimation.

    The Kalman filter is a single target tracker for linear state space models, i.e. models that
    describe the transition of a state variable and its relationship to sensor readings
    as matrix-vector-multiplications.
    Additionally, the Kalman filter is based on the assumption that the state process and
    measurements are sampled from a Gaussian distribution.

    Examples:
        First, import some helper functions from numpy.

        >>> from numpy import array
        >>> from numpy import eye
        >>> from numpy import vstack

        Then, setup the system's model.
        In this case, we track a 1D position that we assume to have a constant velocity.
        Thereby we choose the transition model and measurement function like so.

        >>> F = array([[1.0, 1.0], [0.0, 1.0]])
        >>> H = array([[1.0, 0.0]])

        Furthermore, we assume the following covariance matrices to model
        the noise in our model and measurements.

        >>> Q = eye(2)
        >>> R = eye(1)

        An input to the system can be defined as well.
        Here, we model the input to change the velocity of the system.

        >>> B = vstack([0.0, 1.0])

        Our initial belief is a position and velocity of 0.

        >>> mean = vstack([0.0, 0.0])
        >>> covariance = array([[1.0, 0.0], [0.0, 1.0]])
        >>> estimate = Gaussian(mean, covariance)

        Then, we initialize the filter.
        Since, this model has not input we can ignore the control function B.

        >>> kalman = Kalman(estimate, F, H, Q, R, B)

        Now, we can predict based on the provided model and system input.
        Then, a correcttion with measurements of the true position is done.

        >>> for _ in range(5):
        ...     kalman.predict(u=vstack([0.0]))
        ...     kalman.correct(array([5.]))

        Predictions and corrections do not need to alternate every time.
        As an example, you can predict the state multiple times should your measurements be
        unavailable for an extended period of time.

        Furthermore, an alternative measurement model can be provided in case it is needed.
        For this, define H and its arguments as keyword arguments as follows.

        >>> kalman.correct(array([5.]), H=lambda v: array([[v, 0.0]]), v=3)

        Finally, we can set the filter to keep a trace of the estimation process:

        >>> kalman = Kalman(estimate, F, H, Q, R, B, keep_trace=True)
        >>> kalman.predict(u=vstack([0.0]))
        >>> kalman.correct(array([5.]))

        By doing so, DataFrame objects of the predictions

        >>> kalman.predictions
                        x                         P                         F
        0  [[0.0], [0.0]]  [[3.0, 1.0], [1.0, 2.0]]  [[1.0, 1.0], [0.0, 1.0]]

        and estimates

        >>> kalman.estimates
                          x                             P      z
        0  [[3.75], [1.25]]  [[0.75, 0.25], [0.25, 1.75]]  [5.0]

        can be obtained.

    Args:
        estimate: Initial belief, i.e. the gaussian distribution that describes your initial guess
            on the target's state
        F: State transition model, i.e. the change of x in a single timestep (n, n)
        H: Measurement model, i.e. a mapping from a state to measurement space (m, n)
        Q: Process noise matrix, i.e. the covariance of the state transition (n, n)
        R: Measurement noise matrix, i.e. the covariance of the sensor readings (m, m)
        B: Input dynamics model, i.e. the influence of a system input on the state transition (1, k)
        keep_trace: Flag for tracking filter process

    References:
        - https://en.wikipedia.org/wiki/Kalman_filter
    """

    def __init__(
        self,
        estimate: Gaussian,
        F: ndarray | Callable[..., ndarray],
        H: ndarray | Callable[..., ndarray],
        Q: ndarray,
        R: ndarray,
        B: ndarray | None,
        keep_trace: bool = False,
    ):
        # Initial belief
        self.estimate = deepcopy(estimate)
        self.prediction = deepcopy(estimate)

        # Model specification
        self.F = F
        self.B = B
        self.H = H
        self.Q = Q
        self.R = R

        # Objects for process tracing
        self.keep_trace = keep_trace
        self.predictions = DataFrame(columns=["x", "P", "F"])
        self.estimates = DataFrame(columns=["x", "P", "z"])

    def predict(self, **kwargs) -> None:
        """Predict a future state based on a linear forward model with optional system input."""

        # Compute F if additional parameters are needed
        F = self.F(**kwargs) if callable(self.F) else self.F

        # Consider system input
        u = kwargs.pop("u", None)
        input_influence = self.B @ u if u is not None else 0.0

        # Predict next state
        self.prediction = Gaussian(
            F @ self.estimate.x + input_influence,
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
        """Correct a state prediction based on a measurement.

        Args:
            z: The measurement taken at this timestep
        """

        # Check for differing measurement model
        H = kwargs.pop("H", self.H)

        # Compute H if additional parameters are needed
        if callable(H):
            H = H(**kwargs)

        # Compute the residual and its covariance
        y = z - H @ self.prediction.x
        S = H @ self.prediction.P @ H.T + self.R

        # Compute the new Kalman gain
        K = self.prediction.P @ H.T @ inv(S)

        # Estimate new state
        self.estimate = Gaussian(
            self.prediction.x + K @ y,
            self.prediction.P - K @ S @ K.T,
        )

        # Append estimation data to trace
        if self.keep_trace:
            new = DataFrame(
                {"x": (self.estimate.x.copy(),), "P": (self.estimate.P.copy(),), "z": (z.copy(),)}
            )
            self.estimates = concat([self.estimates, new], ignore_index=True)
