"""Provides mathematical abstractions for usage within Promis."""



# ProMis
from promis.models.gaussian import Gaussian
from promis.models.gaussian_mixture import GaussianMixture
from promis.models.gaussian_process import GaussianProcess

__all__ = ["Gaussian", "GaussianMixture", "GaussianProcess"]
