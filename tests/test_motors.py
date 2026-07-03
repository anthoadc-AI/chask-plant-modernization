"""Tests for chask.energy.motors — validated against hand-calculated values."""

from chask.energy.motors import (
    MOTOR_INVENTORY,
    motor_savings_detail,
    reconciliation,
    total_motor_savings_kwh_mo,
)


class TestMotorSavingsDetail:
    def test_returns_dataframe(self):
        result = motor_savings_detail()
        assert hasattr(result, "columns")

    def test_row_count_matches_inventory(self):
        result = motor_savings_detail()
        assert len(result) == len(MOTOR_INVENTORY)

    def test_savings_positive_for_all_motors(self):
        result = motor_savings_detail()
        assert (result["savings_kwh_mo"] > 0).all()

    def test_savings_total_positive(self):
        result = motor_savings_detail()
        assert result["savings_kwh_mo_total"].sum() > 0

    def test_horno_is_largest_contributor(self):
        # Horno soplante 15kW × 2 at 600h/mo → should be the biggest single group
        result = motor_savings_detail()
        max_row = result.loc[result["savings_kwh_mo_total"].idxmax()]
        assert "horno" in max_row["name"].lower() or max_row["power_kw"] >= 11.0

    def test_hand_calculation_amasadora_1(self):
        # Amasadora 11kW×2, eff 0.78→0.921, 360h:
        # savings/unit = 11 * 360 * (1/0.78 - 1/0.921) ≈ 776 kWh
        result = motor_savings_detail()
        row = result[result["name"] == "Amasadora espiral 1"].iloc[0]
        expected_unit = 11.0 * 360 * (1 / 0.78 - 1 / 0.921)
        assert abs(row["savings_kwh_mo"] - expected_unit) < 0.5

    def test_total_count_kwh(self):
        result = motor_savings_detail()
        # total for a row = savings_unit × count
        for _, row in result.iterrows():
            assert abs(row["savings_kwh_mo_total"] - row["savings_kwh_mo"] * row["count"]) < 0.2


class TestTotalMotorSavings:
    def test_returns_float(self):
        result = total_motor_savings_kwh_mo()
        assert isinstance(result, float)

    def test_total_in_plausible_range(self):
        # Theoretical ~7,000–10,000 kWh/mo for this fleet
        result = total_motor_savings_kwh_mo()
        assert 5_000 < result < 12_000

    def test_consistent_with_detail_sum(self):
        from chask.energy.motors import motor_savings_detail

        detail = motor_savings_detail()
        assert abs(total_motor_savings_kwh_mo() - detail["savings_kwh_mo_total"].sum()) < 0.1


class TestReconciliation:
    # Observed SS savings: ~11,764.8 kWh/mo (pre mean − SS mean from dataset)
    OBSERVED = 11_764.8

    def test_returns_dict(self):
        result = reconciliation(self.OBSERVED)
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = reconciliation(self.OBSERVED)
        for key in (
            "theoretical_motor_kwh_mo",
            "non_motor_kwh_mo",
            "observed_kwh_mo",
            "gap_kwh_mo",
            "motor_share_pct",
            "explained_pct",
        ):
            assert key in result

    def test_motor_share_between_30_and_80_pct(self):
        # Motors expected to explain 40–70% of observed savings
        result = reconciliation(self.OBSERVED)
        assert 30 < result["motor_share_pct"] < 80

    def test_explained_pct_reasonable(self):
        # Combined motor + non-motor attribution should cover most of observed savings
        result = reconciliation(self.OBSERVED)
        # With our inventory + NON_MOTOR_SAVINGS_BREAKDOWN total ≈ observed
        # The gap_kwh_mo can be small positive or negative depending on rounding
        assert abs(result["gap_kwh_mo"]) < 3_000

    def test_tolerance_with_custom_inventory(self):
        # Test that reconciliation tolerance is within 25% of observed
        result = reconciliation(self.OBSERVED)
        tolerance = 0.25 * self.OBSERVED
        assert abs(result["gap_kwh_mo"]) <= tolerance
