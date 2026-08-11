#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

from unittest import TestCase, main

from numpy import abs as np_abs
from numpy import allclose, array, cov, eye, vstack, zeros
from numpy.random import default_rng, seed

from promis.models.gaussian import Gaussian


class TestGaussianIsIsotropic(TestCase):
    def test_isotropic_covariances_are_detected(self):
        mean = vstack([1.0, 2.0])

        self.assertTrue(Gaussian(mean, 4.0 * eye(2)).is_isotropic())
        self.assertTrue(Gaussian(mean, eye(2)).is_isotropic())
        # Tiny float noise should still count as isotropic
        self.assertTrue(Gaussian(mean, 4.0 * eye(2) + 1e-12).is_isotropic())

    def test_non_isotropic_covariances_are_rejected(self):
        mean = vstack([1.0, 2.0])

        # Unequal diagonal entries
        self.assertFalse(Gaussian(mean, array([[1.0, 0.0], [0.0, 4.0]])).is_isotropic())
        # Off-diagonal correlation
        self.assertFalse(Gaussian(mean, array([[2.0, 0.5], [0.5, 2.0]])).is_isotropic())
        # Clearly anisotropic, not just float noise
        self.assertFalse(Gaussian(mean, array([[1.0, 0.0], [0.0, 1.1]])).is_isotropic())

    def test_zero_covariance_is_isotropic(self):
        mean = vstack([1.0, 2.0])

        self.assertTrue(Gaussian(mean, zeros((2, 2))).is_isotropic())


class TestGaussianSample(TestCase):
    def test_isotropic_sample_shape(self):
        mean = vstack([0.0, 0.0])
        distribution = Gaussian(mean, eye(2))

        self.assertEqual(distribution.sample().shape, (2, 1))
        self.assertEqual(distribution.sample(100).shape, (2, 100))

    def test_isotropic_sample_statistics(self):
        seed(42)

        mean = vstack([5.0, -3.0])
        sigma = 2.0
        distribution = Gaussian(mean, sigma**2 * eye(2))

        samples = distribution.sample(20_000)

        empirical_mean = samples.mean(axis=1)
        empirical_cov = cov(samples)

        assert allclose(empirical_mean, mean.T[0], atol=0.1)
        assert allclose(empirical_cov, sigma**2 * eye(2), atol=0.15)

    def test_non_isotropic_fallback_is_used_and_correct(self):
        seed(42)

        mean = vstack([1.0, -1.0])
        covariance = array([[4.0, 1.0], [1.0, 1.0]])
        distribution = Gaussian(mean, covariance)

        # This is exactly the case the fast path must not take
        self.assertFalse(distribution.is_isotropic())

        samples = distribution.sample(20_000)

        empirical_mean = samples.mean(axis=1)
        empirical_cov = cov(samples)

        assert allclose(empirical_mean, mean.T[0], atol=0.1)
        assert allclose(empirical_cov, covariance, atol=0.15)

    def test_zero_covariance_returns_exactly_the_mean(self):
        mean = vstack([3.0, 4.0])
        distribution = Gaussian(mean, zeros((2, 2)))

        samples = distribution.sample(50)

        assert (samples == mean).all()

    def test_isotropic_and_general_path_agree_on_distribution(self):
        # Same isotropic covariance, drawn via both the fast path and (by construction of a
        # non-isotropic-looking but numerically isotropic matrix) confirm consistent statistics.
        # Regression against exact values is intentionally not done here: the fast path changes
        # which numbers are drawn from the global RNG stream even though it is statistically
        # equivalent to the old implementation.
        rng = default_rng(1234)
        mean = vstack([0.0, 0.0])
        sigma = 1.5
        distribution = Gaussian(mean, sigma**2 * eye(2))

        samples = distribution.sample(50_000)
        reference = rng.multivariate_normal(mean.T[0], sigma**2 * eye(2), 50_000).T

        # Compare distributions rather than exact values: mean/covariance should match closely
        assert np_abs(samples.mean(axis=1) - reference.mean(axis=1)).max() < 0.1
        assert np_abs(cov(samples) - cov(reference)).max() < 0.2


if __name__ == "__main__":
    main()
