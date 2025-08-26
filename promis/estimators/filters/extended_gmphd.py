"""This module implements the extended Gaussian Mixture PHD filter for linear
   multi target tracking.."""

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

# ProMis
from promis.estimators.filters.gmphd import GaussianMixturePhd
from promis.models import Gaussian, GaussianMixture


class ExtendedGaussianMixturePhd(GaussianMixturePhd):

    """The extended gaussian mixture PHD filter for non-linear multi-target tracking.

    The extended gaussian mixture PHD is a multi target tracker for non-linear state space models.
    It can be regarded as an extension of the extended Kalman filter formulas to so-called random
    finite sets (RFS). The PHD filter follows the same prediction-correction scheme for state
    estimation as the single target extended Kalman filters. As an additional part of the interface,
    the internal model for the filter's belief needs to be pruned regularly as to limit
    the computational complexity. The extraction of a state estimate is similarly more
    sophisticated in the PHD filter and requires the use of a dedicated procedure.

    Examples:
        Start by importing the necessary numpy functions.

        >>> from numpy import array
        >>> from numpy import cos
        >>> from numpy import eye
        >>> from numpy import sin
        >>> from numpy import vstack

        Setup the model. In this case, we track sine waves.
        Thereby we choose the transition model and its jacobian, as well as the linear
        measurement model, like so.

        >>> F = lambda x: cos(x)
        >>> f = lambda x: sin(x)
        >>> H = lambda x: array([[1.0]])
        >>> h = lambda x: x

        Furthermore, we assume the following noise on the process and measurements.

        >>> Q = eye(1)
        >>> R = eye(1)

        Our belief of how targets are generetaded is for them to start with
        a position at zero.

        >>> mean = vstack([0.0])
        >>> covariance = array([[1.0]])
        >>> birth_belief = GaussianMixture([Gaussian(mean, covariance)])

        We need to tell the filter how certain we are to detect targets and whether they survive.
        Also, the amount of clutter in the observed environment is quantized.

        >>> survival_rate = 0.99
        >>> detection_rate = 0.99
        >>> intensity = 0.01

        Then, we initialize the filter. This model has not input, so we ignore B.

        >>> phd = ExtendedGaussianMixturePhd(
        ...     birth_belief,
        ...     survival_rate,
        ...     detection_rate,
        ...     intensity,
        ...     F,
        ...     f,
        ...     H,
        ...     h,
        ...     Q,
        ...     R
        ... )

        We can now predict with the provided model and then correct the prediction with a
        measurement, in this case of a single targets' position.

        >>> for _ in range(5):
        ...     phd.predict()
        ...     phd.correct(vstack([5.]))

    Args:
        birth_belief: GMM of target births
        survival_rate: Probability of a target to survive a timestep
        detection_rate: Probability of a target to be detected at a timestep
        intensity: Clutter intensity
        F: Linear state transition model (n, n)
        f: Non-linear state transition model that describes the state's evolution
               from one timestep to the next
        H: Linearized measurement model, i.e. the jacobi matrix of h (m, n)
        h: Non-linear measurement model that maps a state variable into the measured space
        Q: Process noise matrix (n, n)
        R: Measurement noise matrix (m, m)
    """

    def __init__(
        self,
        birth_belief: GaussianMixture,
        survival_rate: float,
        detection_rate: float,
        intensity: float,
        F: ndarray | Callable[..., ndarray],
        f: Callable[..., ndarray],
        H: ndarray | Callable[..., ndarray],
        h: Callable[..., ndarray],
        Q: ndarray,
        R: ndarray,
    ):
        # Extended filter specification
        self.f = f
        self.h = h

        # Initializes internal linear model
        super().__init__(birth_belief, survival_rate, detection_rate, intensity, F, H, Q, R)

    def forward_model(self, component: Gaussian, **kwargs) -> Gaussian:
        F = self.F(component.x, **kwargs) if callable(self.F) else self.F

        return Gaussian(
            self.f(x=component.x, **kwargs),
            F @ component.P @ F.T + self.Q,
            component.w * self.survival_rate,
        )

    def measurement_model(self, component: Gaussian, **kwargs):
        # Approximate about predicted state
        h_x: ndarray = self.H(component.x, **kwargs) if callable(self.H) else self.H

        mu = self.h(component.x, **kwargs)
        S = self.R + h_x @ component.P @ h_x.T
        K = component.P @ h_x.T @ inv(S)
        P = component.P - K @ S @ K.T

        return mu, S, K, P
