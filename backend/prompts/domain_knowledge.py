"""Level 1: Domain knowledge — simulates fine-tuned model's native understanding.

In production, this knowledge would be embedded via fine-tuning.
For the demo, we inject it as context — same effect, faster iteration.
"""

DOMAIN_KNOWLEDGE = """## Abu Dhabi Aquifer System

### Formations
- **Dammam Formation**: Eocene limestone, 80-200m depth, T=200-1200 m²/day, S=0.002-0.008. Best water quality in the region. Primary target for monitoring wells.
- **Umm Er Radhuma**: Lower Eocene deep limestone, 150-350m depth, T=100-800 m²/day, S=0.001-0.005. Often brackish (TDS 3,000-8,000 mg/L). Significant storage but declining quality.
- **Quaternary Sand**: Shallow unconfined, 30-80m depth, T=50-400 m²/day, S=0.01-0.05. Highly variable quality, vulnerable to surface contamination.
- **Alluvial**: Very shallow, 20-60m depth, T=30-300 m²/day, S=0.05-0.15. Limited yield, seasonal recharge dependent.

### Regional Characteristics
- Most freshwater lenses are depleted from decades of over-extraction
- Dominant water type: Na-Cl (brackish), with localized Ca-HCO3 lenses
- Natural recharge: <5 mm/year — virtually all extraction exceeds recharge
- Water table decline: 0.5-2.0 m/year across most of the emirate

## Water Quality Standards (UAE / EAD)

| Parameter | Drinking Water | Emergency Supply | Alert Threshold |
|-----------|---------------|-----------------|-----------------|
| TDS | <1,000 mg/L | <1,500 mg/L | >5,000 mg/L |
| Chloride | <250 mg/L | <600 mg/L | >3,000 mg/L |
| pH | 6.5-8.5 | 6.0-9.0 | outside 7.0-8.5 |
| Temperature | - | - | >38°C |

Note: Most monitoring wells produce brackish water (TDS 2,000-8,000 mg/L) used for agriculture and landscaping, not drinking water. Context matters for severity assessment.

## Monitoring Network (Current Deployment)
- **25 wells** across **4 clusters**: Al Wathba, Mussafah Industrial, Sweihan, Al Khatim
- Measurement frequency: every 6 hours (4 readings/day)
- Parameters measured: debit (L/s), TDS (mg/L), pH, chlorides (mg/L), water level (m bgs), temperature (°C)
- Typical well yields: 2-30 L/s (most 5-15 L/s)
- Known regional issues: general aquifer depletion trend, seasonal TDS variation (higher in summer due to evaporation effects on shallow wells)

## Anomaly Interpretation Guidelines

### Debit Decline
- **>15% decline** over observation period: Possible clogging, aquifer depletion, or casing damage
- **>25% decline**: High priority — schedule pump test and CCTV inspection
- **>40% decline**: Critical — immediate well rehabilitation assessment needed
- Consider: seasonal variation (lower in summer), neighboring well interference, recent pumping schedule changes

### TDS Spike
- **>50% above baseline**: Possible contamination event or saltwater intrusion
- **>100% above baseline**: Critical — collect confirmation samples immediately
- Check: is it correlated with rainfall (surface contamination) or pumping increase (upconing)?
- Compare with neighboring wells — if isolated, likely local; if widespread, regional process

### Sensor Fault
- **5+ consecutive zero readings**: Likely sensor malfunction, not actual zero flow
- **Constant value (zero std dev) for >24h**: Sensor stuck — field maintenance required
- Before declaring sensor fault, verify: was the well shut down for maintenance?

### Well Interference
- Correlated drawdown in wells <2km apart: pumping interference
- Depression cone radius >2km: excessive pumping, consider reducing rates
- Use Theis superposition to quantify mutual interference
"""
