"""Multi-level prompt assembly with model-specific adaptors.

Architecture:
  Final prompt = Level 0 (base role, ~200 tok)
               + Level 1 (domain knowledge, ~500-800 tok)
               + Model adaptor (per provider, ~100-200 tok)
               + Task instructions (per task type, ~100-300 tok)
               + Output format (per response type, ~50-100 tok)
               + Level 2 (context bridge, runtime — variable)
"""
from prompts.base_role import BASE_ROLE
from prompts.domain_knowledge import DOMAIN_KNOWLEDGE
from prompts.model_adaptors import get_model_adaptor
from prompts.task_instructions import get_task_instructions
from prompts.output_formats import get_output_format


class PromptEngine:
    """Multi-level prompt assembly with model-specific adaptors."""

    def build(
        self,
        model_pool: str,
        task_type: str,
        context_section: str,
        output_type: str = "text_response",
    ) -> str:
        """
        Assemble final system prompt from components.

        Args:
            model_pool: "pool-a" | "pool-b" | "pool-b-upgrade"
            task_type: "validate_csv" | "detect_anomalies" | "general_question" | ...
            context_section: runtime context from context_bridge.py
            output_type: "text_response" | "anomaly_card" | "validation_card" | "region_stats"

        Returns:
            Complete system prompt string.
        """
        parts = [
            BASE_ROLE,
            DOMAIN_KNOWLEDGE,
            get_model_adaptor(model_pool),
            get_task_instructions(task_type),
            get_output_format(output_type),
            context_section,
        ]
        return "\n\n".join(part for part in parts if part)
