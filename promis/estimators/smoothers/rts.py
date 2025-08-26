"""This module implements the Rauch-Tung-Striebel (RTS) filter for state estimation based on
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

# Third Party
from numpy import ndarray
from numpy.linalg import inv
from pandas import DataFrame

# ProMis
from promis.estimators.filters import Kalman
from promis.models import Gaussian


class Rts(Kalman):

    """The RTS smoother for linear state estimation.

    The RTS smoother is a state estimator for linear state space models, i.e. models that
    describe the transition of a state variable and its relationship to sensor readings
    as matrix-vector-multiplications.
    Additionally, the RTS smoother is based on the assumption that the state process and
    measurements are sampled from a Gaussian distribution.

    Examples:
        First, import some helper functions from numpy.

        >>> from numpy import array
        >>> from numpy import eye
        >>> from numpy import vstack

        Then, setup the system's model.
        In this case, we track a 1D position that we assume to have a constant velocity.
        Thereby we choose the transition model and measurement function like so.

        >>> F = array([[1.0, 1.0], [0.0, 0.0]])
        >>> H = array([[1.0, 0.0]])

        Furthermore, we assume the following covariance matrices to model
        the noise in our model and measurements.

        >>> Q = eye(2)
        >>> R = eye(1)

        Our initial belief is a position and velocity of 0.

        >>> mean = vstack([0.0, 0.0])
        >>> covariance = array([[1.0, 0.0], [0.0, 1.0]])
        >>> estimate = Gaussian(mean, covariance)

        Then, we initialize the smoother.
        Since this model has not input we can ignore the control function B.

        >>> rts = Rts(estimate, F, H, Q, R)

        Now, we can predict based on the provided model and correct predictions with
        measurements of the true position.

        >>> for i in range(10):
        ...     rts.predict()
        ...     rts.correct(array([5.]))

        So far, this is equivalent to using the standard Kalman filter.
        We can now get an estimate of the state trajectory by using the RTS smoothing algorithm.
        Hereby, old estimates get updated recursively by their successors.

        >>> smooth_estimates = rts.smooth()

    Args:
        estimate: Initial belief, i.e. the gaussian distribution that describes your initial guess
            on the target's state
        F: State transition model, i.e. the change of x in a single timestep (n, n)
        H: Measurement model, i.e. a mapping from a state to measurement space (m, n)
        Q: Process noise matrix, i.e. the covariance of the state transition (n, n)
        R: Measurement noise matrix, i.e. the covariance of the sensor readings (m, m)
        B: Input dynamics model, i.e. the influence of an input on the state transition (1, k)

    References:
        - https://en.wikipedia.org/wiki/Kalman_filter#Rauch%E2%80%93Tung%E2%80%93Striebel
    """

    def __init__(
        self,
        estimate: Gaussian,
        F: ndarray | Callable[..., ndarray],
        H: ndarray | Callable[..., ndarray],
        Q: ndarray,
        R: ndarray,
        B: ndarray | None = None,
    ):
        super().__init__(estimate, F, H, Q, R, B, keep_trace=True)

    def smooth(self) -> DataFrame:
        """Apply RTS smoothing.

        Returns:
            The smoothed data with columns `"x"` and `"P"`
        """

        # Dataframe of smoothed estimates
        # The latest estimated cannot be improved
        smoothed = DataFrame(columns=["x", "P"])
        smoothed.loc[self.estimates.index[-1]] = {
            "x": self.estimates.iloc[-1].x,
            "P": self.estimates.iloc[-1].P,
        }

        # Recursively go back in time
        for i in self.estimates.index[-2::-1]:
            # Access next predictions and estimates for smoothing
            prediction = self.predictions.iloc[i + 1]
            estimate = self.estimates.iloc[i]

            # Compute smoothing gain
            G = estimate.P @ prediction.F @ inv(prediction.P)

            # Append to smoothed DataFrame
            smoothed.loc[i] = {
                "x": estimate.x + G @ (smoothed.loc[i + 1].x - prediction.x),
                "P": estimate.P + G @ (smoothed.loc[i + 1].P - prediction.P) @ G.T,
            }

        return smoothed
