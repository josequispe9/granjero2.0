import json
from langchain_core.messages import HumanMessage
from src.config import haiku


PROMPT = """Eres un clasificador que detecta actualizaciones en el perfil del cliente.

Analiza el ultimo mensaje del cliente y determina si revela:
- Un pain point (problema que tiene el cliente)
- Interes en un producto especifico
- Su nombre

Contexto actual:
- Pain point conocido: {pain_point}
- Producto de interes: {product}
- Nombre: {name}

Mensaje del cliente: {message}

Responde SOLO con JSON valido:
{{
  "pain_point": "nuevo pain point o null si no hay",
  "product_interested": "producto mencionado o null",
  "customer_name": "nombre si lo menciona o null"
}}"""


async def classify_revision(
    last_message: str,
    pain_point: str | None,
    product_interested: str | None,
    customer_name: str,
) -> dict:
    result = await haiku.ainvoke([
        HumanMessage(content=PROMPT.format(
            pain_point=pain_point or "desconocido",
            product=product_interested or "desconocido",
            name=customer_name,
            message=last_message,
        ))
    ])

    try:
        raw = result.content.strip()
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
    except Exception:
        data = {}

    return {
        "pain_point": data.get("pain_point"),
        "product_interested": data.get("product_interested"),
        "customer_name": data.get("customer_name"),
    }
