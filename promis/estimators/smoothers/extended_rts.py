"""This module implements the Extended Rauch-Tung-Striebel (RTS) filter for
    state estimation based onnlinearized state transition and measurement models."""

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
from promis.estimators.filters import ExtendedKalman
from promis.models import Gaussian


class ExtendedRts(ExtendedKalman):

    """The Extended RTS smoother for non-linear state estimation.

    The Extended RTS smoother is a single target state estimator for non-linear
    models and their jacobi matrix to estimate state variables whose process and/or relation to
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

        Then, we initialize the filter. This model has not input, so we ignore B.

        >>> rts = ExtendedRts(estimate, F, f, H, h, Q, R)

        We first predict with the provided model and then correct the prediction with
        measurements of the true position.

        >>> for i in range(10):
        ...     rts.predict()
        ...     rts.correct(array([5.]))

        So far, this is equivalent to using the standard Extended Kalman filter.
        We can now get an estimate of the state trajectory by using the RTS smoothing algorithm.
        Hereby, old estimates get updated recursively by their successors.

        >>> smooth_estimates = rts.smooth()

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
    """

    def __init__(
        self,
        estimate: Gaussian,
        F: Callable[..., ndarray],
        f: Callable[..., ndarray],
        H: Callable[..., ndarray],
        h: Callable[..., ndarray],
        Q: ndarray,
        R: ndarray,
    ):
        super().__init__(estimate, F, f, H, h, Q, R, keep_trace=True)

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
