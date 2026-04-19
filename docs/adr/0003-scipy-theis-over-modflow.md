# ADR 0003: Analytical Theis Equation over MODFLOW Numerical Model

**Status:** Accepted
**Date:** 2026-04-19

## Context

Depression cone visualization requires groundwater flow modeling. Options: (1) FloPy + MODFLOW numerical simulation, (2) analytical Theis equation via scipy. MODFLOW is industry standard but requires grid setup, boundary conditions, and calibration.

## Decision

Use the **Theis equation** (`scipy.special.exp1`) with superposition principle for multi-well drawdown calculation. 15 lines of code, no external numerical solver.

## Consequences

**Positive:**
- Implementation in ~15 lines of Python — easy to understand, test, and maintain
- No MODFLOW binary dependency — works in Docker without Fortran compiler
- Sufficient accuracy for visualization and anomaly detection at demo scale
- Superposition principle correctly handles well interference
- Test suite verifies physical correctness (drawdown decreases with distance, increases with time)

**Negative:**
- Assumes homogeneous, isotropic, infinite aquifer — unrealistic for real heterogeneous formations
- No boundary effects (recharge, no-flow boundaries, rivers)
- Would not replace MODFLOW for actual calibration or predictive modeling
- Adequate for 25-well demo; would need numerical model for production with 315 wells
