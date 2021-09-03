#!/usr/bin/env python3 -u
# -*- coding: utf-8 -*-
# copyright: sktime developers, BSD-3-Clause License (see LICENSE file).
"""Modular ThetaForecaster."""

__author__ = ["GuzalBulatova"]
__all__ = ["ThetaNewForecaster"]

from sktime.forecasting.base._base import DEFAULT_ALPHA
from sktime.forecasting.base._meta import _HeterogenousEnsembleForecaster
from sktime.forecasting.compose._pipeline import TransformedTargetForecaster
from sktime.forecasting.compose import ColumnEnsembleForecaster
from sktime.forecasting.exp_smoothing import ExponentialSmoothing
from sktime.forecasting.trend import PolynomialTrendForecaster
from sktime.transformations.series.theta import ThetaLinesTransformer
from sktime.forecasting.compose._ensemble import _aggregate


class ThetaNewForecaster(_HeterogenousEnsembleForecaster):

    _tags = {
        "scitype:y": "univariate",
        "univariate-only": False,
        "y_inner_mtype": "pd.Series",
        "requires-fh-in-fit": False,
        "handles-missing-data": False,
    }

    def __init__(self, theta_values=(0, 2), aggfunc="mean", weights=None):
        self.aggfunc = aggfunc
        self.forecasters = []
        self.weights = weights
        self.theta_values = theta_values
        super(ThetaNewForecaster, self).__init__(forecasters=self.forecasters)

    def _fit(self, y, X=None, fh=None):
        # TODO TransformedTargetForecaster should be able to work with multivariate data

        self.forecasters = []
        for i, theta in enumerate(self.theta_values):
            if theta == 0:
                name = "trend" + str(i)
                forecaster = (name, PolynomialTrendForecaster(), i)
            else:
                name = "ses" + str(i)
                forecaster = (name, ExponentialSmoothing(), i)
            self.forecasters.append(forecaster)

        self._pipe = TransformedTargetForecaster(
            steps=[
                ("transformer", ThetaLinesTransformer(theta=self.theta_values)),
                ("forecaster", ColumnEnsembleForecaster(forecasters=self.forecasters)),
            ]
        )
        # for i, theta in enumerate(self.theta_values):
        #     if theta == 0:
        #         forecaster_ = PolynomialTrendForecaster()
        #     else:
        #         forecaster_ = ExponentialSmoothing()
        #     self._pipe = TransformedTargetForecaster(
        #         steps=[
        #             ("transformer", ThetaLinesTransformer(theta=theta)),
        #             ("forecaster", forecaster_),
        #         ]
        #     )

        self._pipe.fit(y=y, X=X, fh=fh)
        return self

    def _predict(self, fh, X=None, return_pred_int=False, alpha=DEFAULT_ALPHA):
        # Call predict on the forecaster directly, not on the pipeline
        # because of output conversion
        Y_pred = self._pipe.steps_[-1][-1].predict(
            fh, X, return_pred_int=return_pred_int, alpha=alpha
        )

        return _aggregate(Y_pred, aggfunc=self.aggfunc, weights=self.weights)

    def _update(self, y, X=None, update_params=True):
        self._pipe._update(y, X=None, update_params=True)
        return self
