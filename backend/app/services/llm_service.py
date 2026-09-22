from __future__ import annotations

import logging
from typing import Any
import httpx

from app.core.config import get_settings

logger = logging.getLogger("nirman_ai.llm")

GROQ_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


class GroqLLMService:
    """Groq API integration for government project decision support and explanation synthesis."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def is_available(self) -> bool:
        return bool(self.settings.groq_api_key and self.settings.groq_api_key.strip())

    def generate_chat_response(
        self,
        user_query: str,
        project_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate response via Groq API with automatic fallback to structured decision payload."""
        if not self.is_available:
            return {
                "source": "prototype_engine",
                "message": "Groq API key unconfigured. Operating in deterministic rule-engine mode.",
            }

        api_key = self.settings.groq_api_key.strip()
        system_prompt = (
            "You are NIRMAN AI, an official decision-support assistant for MoSPI / DIID "
            "monitoring infrastructure projects in India. Provide concise, clear, "
            "data-grounded recommendations for government officials based strictly on project facts."
        )

        context_str = ""
        if project_context:
            context_str = (
                f"\nPROJECT CONTEXT:\n"
                f"- Project ID: {project_context.get('project_id')}\n"
                f"- Project Name: {project_context.get('project_name')}\n"
                f"- State: {project_context.get('state')}\n"
                f"- Sector: {project_context.get('sector')}\n"
                f"- Operational Status: {project_context.get('operational_status')}\n"
                f"- Risk Assessment: {project_context.get('risk_assessment')}\n"
                f"- Decision Interventions: {project_context.get('decision_interventions')}\n"
            )

        full_user_prompt = f"{user_query}\n{context_str}"

        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": DEFAULT_GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_user_prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 512,
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(GROQ_COMPLETIONS_URL, headers=headers, json=payload)
                if response.status_code == 200:
                    res_json = response.json()
                    choices = res_json.get("choices", [])
                    if choices:
                        content = choices[0].get("message", {}).get("content", "")
                        return {
                            "success": True,
                            "source": "groq_llm",
                            "model": DEFAULT_GROQ_MODEL,
                            "text": content,
                        }

                logger.warning(
                    "Groq API returned HTTP %s: %s",
                    response.status_code,
                    response.text,
                )
        except Exception as err:
            logger.error("Groq API request exception: %s", err)

        return {
            "success": False,
            "source": "fallback",
            "message": "Groq API request failed or timed out.",
        }


llm_service = GroqLLMService()
