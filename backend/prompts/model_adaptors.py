"""Model-specific adaptors — tailored instructions per pool complexity level."""

MODEL_ADAPTORS = {
    "pool-a": """## Response Style (Quick Analysis)
- Be concise: under 150 words unless detailed analysis requested
- When using tools, summarize results in 2-3 sentences
- Include well IDs and numeric values, skip verbose explanations
- Example: "AUH-01-003: debit declined 32% (12.1 to 8.2 L/s). Recommend pump inspection."
""",
    "pool-b": """## Response Style (Analytical)
- Think step by step before concluding
- Structure: Observation -> Context -> Assessment -> Recommendation
- Cross-reference multiple data points before declaring anomalies
- Cite specific values and well IDs throughout
""",
    "pool-b-upgrade": """## Response Style (Comprehensive)
- Provide comprehensive analysis with evidence and reasoning
- Consider geological, operational, and seasonal factors holistically
- Include confidence levels in assessments
- Reference hydrogeological principles (Theis, Cooper-Jacob)
""",
}


def get_model_adaptor(model_pool: str, model_name: str = "") -> str:
    """Get the appropriate model adaptor text for a model pool."""
    return MODEL_ADAPTORS.get(model_pool, MODEL_ADAPTORS["pool-b"])
