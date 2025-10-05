"""This module contains a class used for Gaussian Process regression and uncertainty guided sampling."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
from time import time

import gpytorch
import torch
from gpytorch.kernels import MaternKernel, ScaleKernel

# Third Party
from numpy import column_stack
from numpy.typing import NDArray
from sklearn.preprocessing import StandardScaler


class GPyTorchGP(gpytorch.models.ExactGP):
    def __init__(self, train_x, train_y, likelihood):
        super().__init__(train_x, train_y, likelihood)
        self.mean_module = gpytorch.means.ConstantMean()
        self.covar_module = ScaleKernel(MaternKernel(nu=0.5))

    def forward(self, x):
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)
        return gpytorch.distributions.MultivariateNormal(mean_x, covar_x)


class GaussianProcess:
    """A Gaussian Process regressor using GPyTorch for scalable updates."""

    def __init__(self):
        self.models = []  # One model per output dimension
        self.likelihoods = []
        self.input_scaler = None
        self.output_scaler = None

    def fit(self, coordinates: NDArray, values: NDArray, number_of_iterations: int = 50) -> float:
        self.input_scaler = StandardScaler().fit(coordinates)
        self.output_scaler = StandardScaler().fit(values)

        training_input = torch.tensor(self.input_scaler.transform(coordinates), dtype=torch.float32)
        training_output = torch.tensor(self.output_scaler.transform(values), dtype=torch.float32)

        self.models = []
        self.likelihoods = []

        start = time()
        for i in range(training_output.shape[1]):
            y = training_output[:, i]

            likelihood = gpytorch.likelihoods.GaussianLikelihood()
            model = GPyTorchGP(training_input, y, likelihood)

            model.train()
            likelihood.train()

            optimizer = torch.optim.Adam(model.parameters(), lr=0.1)
            mll = gpytorch.mlls.ExactMarginalLogLikelihood(likelihood, model)

            for _ in range(number_of_iterations):  # Training iterations
                optimizer.zero_grad()
                output = model(training_input)
                loss = -mll(output, y)
                loss.backward()
                optimizer.step()

            self.models.append(model.eval())
            self.likelihoods.append(likelihood.eval())

        return time() - start

    def __call__(self, coordinates: NDArray) -> NDArray:
        return self.predict(coordinates)

    def predict(self, coordinates: NDArray, return_std: bool = False):
        predict_input = torch.tensor(self.input_scaler.transform(coordinates), dtype=torch.float32)
        means = []
        stds = []

        for model, likelihood in zip(self.models, self.likelihoods):
            with torch.no_grad(), gpytorch.settings.fast_pred_var():
                preds = likelihood(model(predict_input))
                mean = preds.mean.numpy()
                stddev = preds.stddev.numpy()
                means.append(mean)
                stds.append(stddev)

        means = column_stack(means)
        stds = column_stack(stds)

        means = self.output_scaler.inverse_transform(means)
        stds = self.output_scaler.scale_ * stds  # Rescale standard deviations

        if return_std:
            return means, stds
        return means
