from __future__ import annotations

import logging
from typing import Any
import httpx

from app.core.config import get_settings

logger = logging.getLogger("nirman_ai.llm")

GROQ_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"


def generate_paimana_rag_response(user_query: str, project_context: dict[str, Any] | None = None) -> str:
    """Generate structured, deterministic PAIMANA grounded retrieval response."""
    if not project_context:
        return (
            "**NIRMAN AI Assistant (PAIMANA Grounded Retrieval)**\n\n"
            "Please select an infrastructure project from the Monitored Projects list to analyze risk drivers, cost variance, physical progress, and government interventions."
        )

    p_id = project_context.get("project_id", "N/A")
    p_name = project_context.get("project_name", "N/A")
    state = project_context.get("state", "N/A")
    sector = project_context.get("sector", "N/A")
    op_status = project_context.get("operational_status", "IN_PROGRESS")
    
    risk_info = project_context.get("risk_assessment") or {}
    risk_cat = risk_info.get("risk_category") or project_context.get("risk_category", "LOW")
    risk_prob = risk_info.get("risk_probability") or project_context.get("risk_probability", 0.05)
    risk_pct = f"{float(risk_prob) * 100:.1f}%" if isinstance(risk_prob, (int, float)) and float(risk_prob) <= 1.0 else f"{risk_prob}%"

    drivers = project_context.get("risk_drivers") or []
    recs = project_context.get("recommendations") or []

    q_lower = user_query.lower()

    if any(k in q_lower for k in ["why", "risk", "risky", "cause", "reason", "driver"]):
        lines = [
            f"**Risk Analysis for {p_name} (`{p_id}`)**\n",
            f"The project is evaluated at **{risk_cat} RISK** ({risk_pct} risk probability) with operational status: **{op_status}**.\n",
            "**Key Risk Drivers (SHAP Feature Contributions):**"
        ]
        if drivers:
            for d in drivers[:4]:
                fname = d.get("feature_name", "Feature")
                fval = d.get("feature_value", "N/A")
                desc = d.get("description", "")
                lines.append(f"• **{fname}** ({fval}): {desc}")
        else:
            lines.append("• Cost escalation & sanction budget ratio monitoring active.")

        lines.extend([
            "\n**Source**",
            "PAIMANA Grounded Retrieval • Infrastructure Risk Model"
        ])
        return "\n".join(lines)

    elif any(k in q_lower for k in ["do", "recommend", "action", "intervention", "what should"]):
        lines = [
            f"**Recommended Government Interventions for {p_name} (`{p_id}`)**\n",
            f"Current Risk Level: **{risk_cat}** | Operational Status: **{op_status}**\n",
            "**Action Plan Directives:**"
        ]
        if recs and isinstance(recs, list) and len(recs) > 0:
            for r in recs[:3]:
                act = r.get("action", "Monitor project execution")
                prio = r.get("priority", "MEDIUM")
                reason = r.get("reason", "Standard monitoring protocol")
                lines.append(f"• **[{prio} PRIORITY] {act}**\n  *Reason:* {reason}")
        else:
            lines.append("• **Financial Review**: Trigger expenditure audit against sanctioned milestones.\n• **Site Inspection**: Conduct field verification for physical progress validation.")

        lines.extend([
            "\n**Source**",
            "NIRMAN Government Decision Engine"
        ])
        return "\n".join(lines)

    elif any(k in q_lower for k in ["cost", "budget", "financial", "expenditure", "sanction"]):
        orig_cost = project_context.get("original_cost", "N/A")
        rev_cost = project_context.get("revised_cost", "N/A")
        exp = project_context.get("expenditure", "N/A")
        lines = [
            f"**Financial Analysis for {p_name} (`{p_id}`)**\n",
            f"• **State / UT:** {state}",
            f"• **Sector:** {sector}",
            f"• **Original Sanctioned Cost:** ₹{orig_cost} Cr",
            f"• **Revised Sanctioned Cost:** ₹{rev_cost} Cr",
            f"• **Cumulative Expenditure:** ₹{exp} Cr\n",
            "**Financial Assessment:**",
            f"Project is under continuous budget tracking. Risk category: **{risk_cat}**.",
            "\n**Source**",
            "PAIMANA Monitored Financial Ledger"
        ]
        return "\n".join(lines)

    else:
        lines = [
            f"**Project Summary: {p_name} (`{p_id}`)**\n",
            f"• **State:** {state} | **Sector:** {sector}",
            f"• **Operational Status:** {op_status}",
            f"• **Risk Level:** {risk_cat} ({risk_pct})",
            "\n**Operational Insights:**",
            "Project metrics are continuously ingested from MoSPI / DIID monitoring system.",
            "\n**Source**",
            "PAIMANA Structured Retrieval System"
        ]
        return "\n".join(lines)


class GroqLLMService:
    """Groq API integration for government project decision support with fast RAG failover."""

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
        """Generate response via Groq API with strict 2-second timeout and PAIMANA RAG fallback."""
        if self.is_available:
            api_key = self.settings.groq_api_key.strip()
            system_prompt = (
                "You are NIRMAN AI, an official decision-support assistant for MoSPI / DIID "
                "monitoring infrastructure projects in India. Provide concise, clear, "
                "data-grounded recommendations for government officials based strictly on project facts. "
                "Always align text strictly to the left and structure response with clear bullet points."
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
                    f"- Decision Interventions: {project_context.get('recommendations')}\n"
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

                # Strict 2.0 second timeout for Groq API call
                with httpx.Client(timeout=2.0) as client:
                    response = client.post(GROQ_COMPLETIONS_URL, headers=headers, json=payload)
                    if response.status_code == 200:
                        res_json = response.json()
                        choices = res_json.get("choices", [])
                        if choices:
                            content = choices[0].get("message", {}).get("content", "")
                            if content and content.strip():
                                return {
                                    "success": True,
                                    "source": "groq_llm",
                                    "model": DEFAULT_GROQ_MODEL,
                                    "text": content.strip(),
                                }

                    logger.warning(
                        "Groq API returned HTTP %s: %s",
                        response.status_code,
                        response.text,
                    )
            except Exception as err:
                logger.info("Groq API call unresolved/timed out (>2.0s): %s", err)

        # Failover to structured PAIMANA grounded retrieval
        fallback_text = generate_paimana_rag_response(user_query, project_context=project_context)
        return {
            "success": True,
            "source": "paimana_rag",
            "model": "PAIMANA Grounded Retrieval",
            "text": fallback_text,
        }


llm_service = GroqLLMService()

