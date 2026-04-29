"""Tests for hydrogeological models."""

from data_generator.hydro_models import (
    PumpingWell,
    superposition_drawdown,
    theis_drawdown,
)


class TestTheisDrawdown:
    """Theis equation correctness tests."""

    def test_drawdown_decreases_with_distance(self):
        """Closer to well = more drawdown."""
        Q, T, S, t = 864.0, 500.0, 0.005, 1.0  # 10 L/s, 1 day
        s_near = theis_drawdown(Q, T, S, r=10, t=t)
        s_far = theis_drawdown(Q, T, S, r=500, t=t)
        assert s_near > s_far > 0

    def test_drawdown_increases_with_time(self):
        """Longer pumping = more drawdown."""
        Q, T, S, r = 864.0, 500.0, 0.005, 100.0
        s_1day = theis_drawdown(Q, T, S, r, t=1.0)
        s_30day = theis_drawdown(Q, T, S, r, t=30.0)
        assert s_30day > s_1day

    def test_drawdown_increases_with_rate(self):
        """Higher pumping rate = more drawdown."""
        T, S, r, t = 500.0, 0.005, 100.0, 1.0
        s_low = theis_drawdown(Q=432, T=T, S=S, r=r, t=t)  # 5 L/s
        s_high = theis_drawdown(Q=1728, T=T, S=S, r=r, t=t)  # 20 L/s
        assert s_high > s_low

    def test_zero_time_returns_zero(self):
        assert theis_drawdown(864, 500, 0.005, 100, t=0) == 0.0

    def test_realistic_abu_dhabi_values(self):
        """Drawdown should be in realistic range for Abu Dhabi wells."""
        Q = 10 * 86.4  # 10 L/s -> m3/day
        T = 500  # m2/day (limestone)
        S = 0.005
        s = theis_drawdown(Q, T, S, r=50, t=30)
        assert 1.0 < s < 20.0  # realistic range


class TestSuperposition:
    """Superposition of multiple wells."""

    def test_two_wells_more_than_one(self):
        wells = [
            PumpingWell(id="W1", x=0, y=0, Q=864, T=500, S=0.005, start_time=0),
            PumpingWell(id="W2", x=200, y=0, Q=864, T=500, S=0.005, start_time=0),
        ]
        s_both = superposition_drawdown(wells, obs_x=100, obs_y=0, t=10)
        s_one = superposition_drawdown(wells[:1], obs_x=100, obs_y=0, t=10)
        assert s_both > s_one

    def test_distant_well_negligible_effect(self):
        wells = [
            PumpingWell(id="W1", x=0, y=0, Q=864, T=500, S=0.005, start_time=0),
            PumpingWell(id="W2", x=50000, y=0, Q=864, T=500, S=0.005, start_time=0),
        ]
        s = superposition_drawdown(wells, obs_x=0, obs_y=0, t=1)
        s_alone = superposition_drawdown(wells[:1], obs_x=0, obs_y=0, t=1)
        assert abs(s - s_alone) < 0.01  # distant well adds < 1cm
