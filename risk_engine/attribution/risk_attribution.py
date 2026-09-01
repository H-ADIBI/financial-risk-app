"""
Component VaR attribution: decomposes total portfolio VaR into each
position's (and sector's / asset class's) contribution, using the
simulated position-level P&L already produced by the VaR model.

Component VaR here is computed as each position's covariance-weighted
contribution to the tail scenarios that drive portfolio VaR -- i.e. for
the simulation draws in the loss tail defining VaR, how much of the
portfolio loss did each position contribute, on average. This sums
(approximately) back to total VaR, which is the property that makes it
useful for "who's driving our risk" reporting.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from risk_engine.attribution.base import AttributionModel, AttributionResult
from risk_engine.data.models import Portfolio
from risk_engine.registry import register
from risk_engine.var.base import VaRResult


@register("attribution_model", "component_var", description="Component VaR via tail-scenario decomposition")
class ComponentVaRAttribution(AttributionModel):
    display_name = "Component VaR Attribution"
    description = (
        "Decomposes total portfolio VaR across positions, sectors, and asset classes "
        "by averaging each position's simulated P&L over the tail scenarios that define "
        "portfolio VaR at the primary confidence level."
    )

    def compute(self, portfolio: Portfolio, var_result: VaRResult) -> AttributionResult:
        if var_result.simulated_position_pnl is None:
            raise ValueError("VaRResult has no simulated_position_pnl to attribute from.")

        primary_cl = max(var_result.confidence_levels)
        loss_quantile = np.percentile(var_result.simulated_pnl, (1 - primary_cl) * 100)
        tail_mask = var_result.simulated_pnl <= loss_quantile

        sim_pos = var_result.simulated_position_pnl
        tail_position_pnl = sim_pos.loc[tail_mask]
        component_var = -tail_position_pnl.mean(axis=0)  # positive = contributes to loss

        df = portfolio.to_dataframe().set_index("position_id")
        by_position = pd.DataFrame(
            {
                "position_id": component_var.index,
                "component_var": component_var.values,
            }
        )
        by_position["name"] = by_position["position_id"].map(df["name"])
        by_position["sector"] = by_position["position_id"].map(df["sector"])
        by_position["asset_class"] = by_position["position_id"].map(df["asset_class"])

        total_component_var = by_position["component_var"].sum()
        by_position["pct_of_var"] = (
            by_position["component_var"] / total_component_var if total_component_var else 0.0
        )
        by_position = by_position.sort_values("component_var", ascending=False).reset_index(drop=True)

        by_sector = (
            by_position.groupby("sector")["component_var"]
            .sum()
            .reset_index()
            .sort_values("component_var", ascending=False)
        )
        by_sector["pct_of_var"] = (
            by_sector["component_var"] / total_component_var if total_component_var else 0.0
        )

        by_asset_class = (
            by_position.groupby("asset_class")["component_var"]
            .sum()
            .reset_index()
            .sort_values("component_var", ascending=False)
        )
        by_asset_class["pct_of_var"] = (
            by_asset_class["component_var"] / total_component_var if total_component_var else 0.0
        )

        return AttributionResult(
            model_key=self.registry_key,
            model_name=self.display_name,
            by_position=by_position,
            by_sector=by_sector,
            by_asset_class=by_asset_class,
        )
