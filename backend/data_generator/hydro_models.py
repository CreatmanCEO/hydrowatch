"""Analytical groundwater models: Theis equation, superposition."""
from dataclasses import dataclass
import numpy as np
from scipy.special import exp1


@dataclass
class PumpingWell:
    """A pumping well with hydraulic parameters."""
    id: str
    x: float            # UTM easting, meters
    y: float            # UTM northing, meters
    Q: float            # pumping rate, m3/day
    T: float            # transmissivity, m2/day
    S: float            # storativity (dimensionless)
    start_time: float   # pumping start time, days


def theis_drawdown(Q: float, T: float, S: float, r: float, t: float) -> float:
    """
    Calculate drawdown using Theis equation.

    Args:
        Q: pumping rate (m3/day)
        T: transmissivity (m2/day)
        S: storativity
        r: distance from well (m)
        t: time since pumping started (days)

    Returns:
        Drawdown in meters.
    """
    if t <= 0 or r <= 0:
        return 0.0
    u = (r**2 * S) / (4 * T * t)
    W_u = float(exp1(u))
    return (Q / (4 * np.pi * T)) * W_u


def superposition_drawdown(
    wells: list[PumpingWell],
    obs_x: float,
    obs_y: float,
    t: float,
) -> float:
    """
    Total drawdown at observation point from multiple pumping wells.
    Uses superposition principle (sum of individual Theis drawdowns).
    """
    total = 0.0
    for w in wells:
        dt = t - w.start_time
        if dt <= 0:
            continue
        r = np.sqrt((obs_x - w.x) ** 2 + (obs_y - w.y) ** 2)
        r = max(r, 0.3)  # well radius
        total += theis_drawdown(w.Q, w.T, w.S, r, dt)
    return total


def generate_drawdown_grid(
    wells: list[PumpingWell],
    center_x: float,
    center_y: float,
    extent: float = 2000,
    grid_size: int = 50,
    t: float = 30,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate 2D drawdown grid around wells for visualization."""
    x = np.linspace(center_x - extent, center_x + extent, grid_size)
    y = np.linspace(center_y - extent, center_y + extent, grid_size)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros_like(X)

    for i in range(grid_size):
        for j in range(grid_size):
            Z[i, j] = superposition_drawdown(wells, X[i, j], Y[i, j], t)

    return X, Y, Z
