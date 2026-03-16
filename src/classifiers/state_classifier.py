import json
from langchain_core.messages import HumanMessage
from src.config import haiku


PROMPT = """Eres un clasificador de estado conversacional para un agente de ventas.

Analiza el ULTIMO mensaje del cliente en el contexto de la conversacion.

Clasifica en:
- estado: "I" (interes), "NI" (no interes), "IND" (indeterminado/ambiguo)
- subestado:
  - Si I: "saludo" | "descubrimiento" | "eleccion" | "oferta" | "conclusion"
  - Si NI: "precio" | "tiempo" | "necesidad" | "autoridad" | "rechazo_duro"
  - Si IND: "ambiguo"
- confianza: float entre 0.0 y 1.0

Reglas:
- Si no estas seguro (confianza < 0.6), clasifica como IND
- "No me interesa" / "No quiero" / "Dejame en paz" = NI rechazo_duro
- "Es muy caro" / "No tengo presupuesto" = NI precio
- "No es el momento" / "Ahora no puedo" = NI tiempo
- "No lo necesito" / "Ya tengo" = NI necesidad
- "No soy yo quien decide" / "Tengo que consultarlo" = NI autoridad
- Preguntas sobre el producto = I con subestado segun fase
- Respuestas vagas, monosilabos, emojis sin contexto = IND

Conversacion reciente:
{conversation}

Responde SOLO con JSON valido:
{{"estado": "...", "subestado": "...", "confianza": 0.0}}"""


async def classify_state(messages: list, current_phase: str) -> dict:
    recent = messages[-6:]

    def _role(m):
        if hasattr(m, "type"):
            return m.type
        if isinstance(m, dict):
            return m.get("role", "unknown")
        return "unknown"

    def _content(m):
        if hasattr(m, "content"):
            return m.content
        if isinstance(m, dict):
            return m.get("content", "")
        return str(m)

    conversation = "\n".join(
        f"{_role(m)}: {_content(m)}" for m in recent
    )

    result = await haiku.ainvoke([
        HumanMessage(content=PROMPT.format(conversation=conversation))
    ])

    try:
        raw = result.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
    except Exception:
        return {"estado": "IND", "subestado": "ambiguo", "confianza": 0.3}

    estado = data.get("estado", "IND")
    confianza = float(data.get("confianza", 0.5))

    if confianza < 0.6:
        estado = "IND"
        data["subestado"] = "ambiguo"

    return {
        "estado": estado,
        "subestado": data.get("subestado", "ambiguo"),
        "confianza": confianza,
    }
