"""Model-specific adaptors — tailored instructions per LLM provider.

Each provider has different strengths. We optimize prompt style accordingly:
- DeepSeek V3: strong structured output, good reasoning, cost-effective
- Gemini Flash: fast, good at concise responses
- NVIDIA Nemotron: free tier, needs explicit format guidance
- Anthropic Haiku: excellent tool calling, chain-of-thought
"""

MODEL_ADAPTORS = {
    "pool-a": {
        "deepseek": """## Response Style (DeepSeek — Efficient)
- Be concise: respond in under 150 words unless detailed analysis is explicitly requested
- When using tools, summarize results in 2-3 sentences
- For structured output, use exact JSON format — no markdown wrapping
- Prefer bullet points over paragraphs
- Include well IDs and numeric values, skip verbose explanations
- Example anomaly summary: "AUH-01-003: debit declined 32% (12.1→8.2 L/s). Recommend pump inspection."
""",
        "gemini_flash": """## Response Style (Gemini Flash — Concise)
- Be very concise: under 100 words for simple queries
- Use bullet points, not paragraphs
- Include well IDs and numeric values with units
- For structured output, return exact JSON — no wrapping
""",
    },
    "pool-b": """## Response Style (Analytical)
- Think step by step before concluding. Consider multiple hypotheses.
- Structure your analysis:
  1. Observation: what the data shows
  2. Context: relevant hydrogeological factors
  3. Assessment: most likely explanation
  4. Recommendation: specific actionable steps
- You may use chain-of-thought reasoning for complex questions
- Cross-reference multiple data points before declaring anomalies
- Compare with neighboring wells when relevant
- Cite specific values and well IDs throughout
""",
    "pool-b-upgrade": """## Response Style (Comprehensive Analysis)
- Provide comprehensive analysis with evidence and reasoning
- You have full freedom to reason at length — use it for complex cases
- Consider geological, operational, and seasonal factors holistically
- For anomaly interpretation:
  - Analyze time series patterns in detail
  - Consider superposition effects from neighboring wells
  - Evaluate whether anomaly is isolated or part of regional trend
  - Provide differential diagnosis with likelihood assessment
- For calibration/optimization questions:
  - Consider trade-offs explicitly
  - Provide quantitative recommendations where possible
  - Reference hydrogeological principles (Theis, Cooper-Jacob)
- Include confidence levels in your assessments
""",
}


def get_model_adaptor(model_pool: str, model_name: str = "") -> str:
    """Get the appropriate model adaptor text for a model pool."""
    adaptor = MODEL_ADAPTORS.get(model_pool, "")
    if isinstance(adaptor, dict):
        if "gemini" in model_name:
            return adaptor.get("gemini_flash", list(adaptor.values())[0])
        return adaptor.get("deepseek", list(adaptor.values())[0])
    return adaptor
