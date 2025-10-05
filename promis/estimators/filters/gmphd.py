"""This module implements the Gaussian Mixture PHD filter for linear
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
from copy import deepcopy

# Third Party
from numpy import ndarray
from numpy.linalg import inv

# ProMis
from promis.models import Gaussian, GaussianMixture


class GaussianMixturePhd:

    """The gaussian mixture PHD filter for linear multi-target tracking.

    The gaussian mixture PHD filter is a multi target tracker for linear state space models.
    It can be regarded as an extension of the Kalman filter formulas to so-called random
    finite sets (RFS). The PHD filter follows the same prediction-correction scheme for state
    estimation as the single target Kalman filters. As an additional part of the interface,
    the internal model for the filter's belief needs to be pruned regularly as to limit
    the computational complexity. The extraction of a state estimate is similarly more
    sophisticated in the PHD filter and requires the use of a dedicated procedure.

    Examples:
        Start by importing the necessary numpy functions.

        >>> from numpy import array
        >>> from numpy import eye
        >>> from numpy import vstack

        Setup the model.
        In this case, we track 1D positions with constant velocities.
        Thereby we choose the transition model like so.

        >>> F = array([[1.0, 1.0], [0.0, 0.0]])

        The measurements will be positions and no velocities.

        >>> H = array([[1.0, 0.0]])

        Furthermore, we assume the following noise on the process and measurements.

        >>> Q = eye(2)
        >>> R = eye(1)

        Our belief of how targets are generetaded is for them to start with
        a position and velocity of 0.

        >>> mean = vstack([0.0, 0.0])
        >>> covariance = array([[1.0, 0.0], [0.0, 1.0]])
        >>> birth_belief = GaussianMixture([Gaussian(mean, covariance)])

        We need to tell the filter how certain we are to detect targets and whether they survive.
        Also, the amount of clutter in the observed environment is quantized.

        >>> survival_rate = 0.99
        >>> detection_rate = 0.99
        >>> intensity = 0.01

        Then, we initialize the filter. This model has not input, so we ignore B.

        >>> phd = GaussianMixturePhd(
        ...     birth_belief,
        ...     survival_rate,
        ...     detection_rate,
        ...     intensity,
        ...     F,
        ...     H,
        ...     Q,
        ...     R
        ... )

        We can now predict with the provided model and then correct the prediction with a
        measurement, in this case of a single targets' position.

        >>> for _ in range(5):
        ...     phd.predict()
        ...     phd.correct(vstack([5.]))

        Furthermore, an alternative measurement model can be provided in case it is needed.
        For this, define H and its arguments as keyword arguments as follows.

        >>> phd.correct(vstack([5.]), H=lambda v: array([[v, 0.0]]), v=3)

    Args:
        birth_belief: GMM of target births
        survival_rate: Probability of a target to survive a timestep
        detection_rate: Probability of a target to be detected at a timestep
        intensity: Clutter intensity
        F: Linear state transition model (n, n)
        H: Linear measurement model (m, n)
        Q: Process noise matrix (n, n)
        R: Measurement noise matrix (m, m)

    Refernces:
        - B.-N. Vo and W.-K. Ma, "The Gaussian Mixture Probability Hypothesis Density Filter,"
          in IEEE Transactions on Signal Processing, vol. 54, no. 11, pp. 4091-4104,
          Nov. 2006, doi: 10.1109/TSP.2006.881190.
    """

    def __init__(
        self,
        birth_belief: GaussianMixture,
        survival_rate: float,
        detection_rate: float,
        intensity: float,
        F: ndarray | Callable[..., ndarray],
        H: ndarray | Callable[..., ndarray],
        Q: ndarray,
        R: ndarray,
    ):
        # Filter specification
        self.F = F
        self.H = H
        self.Q = Q
        self.R = R

        # Gaussian mixture model for spontaneous birth of new targets
        self.birth_belief = birth_belief

        # Rates of survival, detection and clutter intensity
        self.survival_rate = survival_rate
        self.detection_rate = detection_rate
        self.intensity = intensity

        # Gaussian mixture model
        self.gmm = GaussianMixture()

    def forward_model(self, component: Gaussian, **kwargs) -> Gaussian:
        # Compute F if additional parameters are needed
        F = self.F(**kwargs) if callable(self.F) else self.F

        return Gaussian(
            F @ component.x,
            F @ component.P @ F.T + self.Q,
            component.w * self.survival_rate,
        )

    def measurement_model(self, component: Gaussian, **kwargs):
        # Compute H if additional parameters are needed
        H = self.H(component.x, **kwargs) if callable(self.H) else self.H

        mu = H @ component.x
        S = self.R + H @ component.P @ H.T
        K = component.P @ H.T @ inv(S)
        P = component.P - K @ S @ K.T

        return mu, S, K, P

    def predict(self, **kwargs) -> None:
        """Predict the future state."""

        # Spontaneous birth of new targets
        born = deepcopy(self.birth_belief)

        # Spawning off of existing targets
        # TODO: Spawning not implemented at this point in time
        spawned = GaussianMixture()

        # Prediction for existing targets
        predicted = GaussianMixture()
        for component in self.gmm:
            predicted.append(self.forward_model(component, **kwargs))

        # Concatenate with newborn and spawned target components
        self.gmm = predicted + born + spawned

    def correct(self, measurements: ndarray, **kwargs) -> None:
        """Correct the former prediction based on a sensor reading.

        Args:
            measurements: Measurements at this timestep
        """

        # ######################################
        # Construction of update components

        mu: list[ndarray] = []  # Means mapped to measurement space
        S: list[ndarray] = []  # Residual covariance
        K: list[ndarray] = []  # Gains
        P: list[ndarray] = []  # Covariance

        for i, component in enumerate(self.gmm):
            results = self.measurement_model(component, **kwargs)

            mu.append(results[0])
            S.append(results[1])
            K.append(results[2])
            P.append(results[3])

        # ######################################
        # Update

        # Undetected assumption
        updated = deepcopy(self.gmm)
        for component in updated:
            component.weight *= 1 - self.detection_rate

        # Measured assumption
        for z in range(measurements.shape[1]):
            # Fill batch with corrected components
            batch = GaussianMixture(
                [
                    Gaussian(
                        self.gmm[i].x + K[i] @ (measurements[:, [z]] - mu[i]),
                        P[i],
                        self.detection_rate * Gaussian(mu[i], S[i])(measurements[:, [z]]),
                    )
                    for i in range(len(self.gmm))
                ]
            )

            # Normalize weights
            sum_of_weights = sum([component.weight for component in batch])
            for component in batch:
                component.weight /= self.intensity + sum_of_weights

            # Append batch to updated GMM
            updated += batch

        # Set updated as new gaussian mixture model
        self.gmm = updated
