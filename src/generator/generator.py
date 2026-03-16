"""Genera respuesta usando Sonnet con la tactica y contexto del blackboard."""

from langchain_core.messages import HumanMessage, SystemMessage
from src.config import sonnet
from src.generator.prompts import SYSTEM_BASE, PHASE_PROMPTS, TACTIC_PROMPTS


async def generate_response(bb: dict) -> str:
    phase = bb.get("cardone_phase", "saludo")
    tactic = bb.get("tactic", "avanzar_fase")
    used = bb.get("used_arguments", [])

    # Construir system prompt
    system = SYSTEM_BASE.format(
        agent_name=bb.get("name", "Agente Movistar"),
        customer_name=bb.get("customer_name", "Cliente"),
        used_arguments=", ".join(used) if used else "ninguno",
    )

    phase_prompt = PHASE_PROMPTS.get(phase, "")
    if phase_prompt:
        phase_prompt = phase_prompt.format(
            pain_point=bb.get("pain_point") or "aun no identificado",
            product=bb.get("product_interested") or "por definir",
        )

    tactic_prompt = TACTIC_PROMPTS.get(tactic, "")

    full_system = system + "\n" + phase_prompt + "\n" + tactic_prompt

    # Mensajes de la conversacion
    messages = [SystemMessage(content=full_system)] + list(bb.get("messages", []))

    result = await sonnet.ainvoke(messages)
    return result.content
