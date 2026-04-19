# ADR 0005: Synthetic Data with Controlled Anomaly Injection

**Status:** Accepted
**Date:** 2026-04-19

## Context

Real groundwater data from Abu Dhabi is classified. We need realistic data for development and demo that behaves like real monitoring data — including anomalies that the detection system should find.

## Decision

Generate synthetic data with:
- 25 wells in 4 clusters matching Abu Dhabi geography
- Realistic hydrogeological parameters (depth, aquifer type, TDS, pH) from domain expertise
- Time series with seasonal + diurnal + AR(1) noise components
- Controlled anomaly injection: debit decline, TDS spike, sensor fault
- Anomaly log as ground truth for detection accuracy evaluation
- Seeded random generator for reproducibility

## Consequences

**Positive:**
- Reproducible: same seed always generates identical data
- Ground truth: injected anomalies have known type, location, and magnitude
- Eval pipeline can compute precision/recall against known anomalies
- No data privacy or classification concerns
- Domain-realistic: parameters validated by 14 years of hydrogeology experience

**Negative:**
- Synthetic data may not capture real-world complexity (heterogeneity, measurement noise patterns)
- Anomaly patterns are "clean" — real anomalies are messier
- No correlation between wells (each generated independently) — real wells in a cluster share aquifer
