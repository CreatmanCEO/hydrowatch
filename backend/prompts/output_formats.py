"""Output format specifications — ensure schema compliance."""

OUTPUT_FORMATS = {
    "text_response": """## Output Format: Text Response
- Respond in markdown
- Use well IDs in bold: **AUH-01-003**
- Include specific values with units: "TDS: 4,500 mg/L"
- Use tables for comparing multiple wells
- Keep paragraphs short (2-3 sentences max)
""",
    "anomaly_card": """## Output Format: Anomaly Card (JSON)
When reporting anomalies, return a JSON object matching this schema:
```json
{
  "type": "anomaly_card",
  "severity": "low|medium|high|critical",
  "well_id": "AUH-XX-XXX",
  "anomaly_type": "debit_decline|depression_cone|interference|tds_spike|sensor_fault",
  "title": "Brief anomaly title",
  "description": "Detailed description with values and context",
  "value_current": 8.2,
  "value_baseline": 12.6,
  "change_pct": -34.9,
  "recommendation": "Specific actionable recommendation"
}
```
Severity thresholds:
- critical: immediate action required, risk to operations
- high: action needed within 1 week
- medium: monitor closely, schedule inspection
- low: note for records, continue normal monitoring
""",
    "validation_card": """## Output Format: Validation Result (JSON)
When reporting CSV validation results, return JSON matching this schema:
```json
{
  "type": "validation_result",
  "valid": true|false,
  "total_rows": 500,
  "valid_rows": 487,
  "errors": ["Row 45: negative flow rate (-2.1 L/s)"],
  "warnings": ["12 rows with missing depth values"],
  "column_stats": {
    "debit_ls": {"min": 0.0, "max": 25.3, "mean": 12.1}
  }
}
```
- errors: data that is definitely wrong (negative flows, pH=15)
- warnings: data that is suspicious but physically possible
""",
    "region_stats": """## Output Format: Region Statistics
Present as a structured summary with:
- Well count and status breakdown
- Key parameter averages with context
- Any flagged concerns
Use markdown tables for multi-cluster comparisons.
""",
    "interference_card": """## Output Format: Interference Card (JSON)
Return JSON matching InterferenceCard schema:
```json
{
  "type": "interference_card",
  "pairs_summary": {"critical": 2, "high": 4, "medium": 6, "low": 0},
  "top_concerns": [
    {"well_a": "AUH-01-001", "well_b": "AUH-01-002", "coef_max": 0.61,
     "action": "Reduce pumping at AUH-01-002"}
  ],
  "regional_pattern": "Mussafah cluster shows correlated drawdown patterns"
}
```
""",
    "drawdown_card": """## Output Format: Drawdown Card (JSON)
Return JSON matching DrawdownCard schema:
```json
{
  "type": "drawdown_card",
  "well_id": "AUH-01-001",
  "t_days": 30,
  "max_drawdown_m": 6.8,
  "cone_radius_1m_km": 2.3,
  "interfering_wells": ["AUH-01-002", "AUH-01-007"],
  "assessment": "Cone radius >2km at 1m isoline indicates excessive pumping.",
  "recommendation": "Consider reducing pumping rate by 20% to limit aquifer depletion."
}
```
""",
}


def get_output_format(output_type: str) -> str:
    """Get output format instructions for a response type."""
    return OUTPUT_FORMATS.get(output_type, OUTPUT_FORMATS["text_response"])
