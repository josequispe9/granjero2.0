"""Genera respuesta usando Sonnet con la tactica y contexto del blackboard."""

from langchain_core.messages import HumanMessage, SystemMessage
from src.config import sonnet
from src.generator.prompts import SYSTEM_BASE, PHASE_PROMPTS, TACTIC_PROMPTS


def _build_competitor_context(bb: dict) -> str:
    """Construye contexto del competidor para inyectar en el prompt."""
    parts = []
    provider = bb.get("competitor_provider")
    service_type = bb.get("competitor_service_type")
    plan = bb.get("competitor_plan")
    price = bb.get("competitor_price")
    satisfaction = bb.get("competitor_satisfaction")

    if provider:
        parts.append(f"Proveedor actual del cliente: {provider}")
    if service_type:
        tipo_label = {"movil": "Celular/Movil", "fibra": "Internet/Fibra", "ambos": "Movil + Fibra"}
        parts.append(f"Tipo de servicio: {tipo_label.get(service_type, service_type)}")
    if plan:
        parts.append(f"Plan actual: {plan}")
    if price:
        parts.append(f"Precio actual: ${price:,}/mes")
    if satisfaction:
        parts.append(f"Satisfaccion: {satisfaction}")

    # Indicar producto que estamos vendiendo
    product = bb.get("product_to_sell")
    if product:
        prod_label = {"portabilidad": "Portabilidad Movil", "fibra": "Fibra Optica", "bundle": "Bundle Fibra + Portabilidad"}
        parts.append(f"PRODUCTO QUE ESTAS VENDIENDO: {prod_label.get(product, product)}")
        parts.append(f"IMPORTANTE: Toda tu argumentacion debe girar en torno a {prod_label.get(product, product)}. NO mezcles con otros productos.")

    if not parts:
        return ""
    return "\nCONTEXTO COMPETIDOR:\n" + "\n".join(parts) + "\n"


def _build_promo_context(bb: dict) -> str:
    """Construye resumen de la promo Movistar segun product_to_sell.

    IMPORTANTE: Solo incluye precio con descuento, NUNCA el precio full.
    Usa product_to_sell para determinar que promo cargar.
    """
    from src.promos.loader import load_promo

    product = bb.get("product_to_sell")
    promo_id = bb.get("selected_promo_id")

    # Cargar promo segun producto que estamos vendiendo
    if product == "fibra":
        data = load_promo("fibra")
    elif product == "bundle":
        data = load_promo("bundle_fibra_portabilidad")
    elif product == "portabilidad" and promo_id:
        data = load_promo(promo_id)
    elif promo_id:
        # Fallback: si no hay product_to_sell, usar service_type
        service_type = bb.get("competitor_service_type")
        if service_type == "fibra":
            data = load_promo("fibra")
        elif service_type == "ambos":
            data = load_promo("bundle_fibra_portabilidad")
        else:
            data = load_promo(promo_id)
    else:
        return ""

    if not data:
        return ""

    parts = [f"\nPROMO MOVISTAR ACTIVA: {data.get('nombre', promo_id or '')}"]

    tipo = data.get("tipo")

    if tipo == "portabilidad":
        dto = data.get("porcentaje_descuento", "")
        dur = data.get("duracion_descuento_meses", "")
        parts.append(f"Descuento: {dto}% por {dur} meses")
        parts.append("Planes disponibles (SOLO mencionar precio con descuento):")
        for plan in data.get("planes", []):
            gb = plan.get("datos_gb", "")
            precio = plan.get("precio_final", 0)
            extras = []
            if plan.get("roaming"):
                r = plan["roaming"]
                extras.append(f"roaming {r.get('datos_incluidos_gb', '')}GB {r.get('zona', '')}")
            extras_str = f" + {', '.join(extras)}" if extras else ""
            parts.append(f"  {gb}GB: ${precio:,}/mes{extras_str}")
        for b in data.get("beneficios_generales", [])[:3]:
            parts.append(f"  - {b.split(':')[0]}")

    elif tipo == "fibra":
        parts.append("Planes fibra disponibles (SOLO mencionar precio con descuento):")
        for plan in data.get("planes", []):
            mb = plan.get("velocidad_mb", "")
            precio = plan.get("precio_final", 0)
            zona = " (zona critica)" if plan.get("zona") == "alta_competencia" else ""
            parts.append(f"  {mb}Mb{zona}: ${precio:,}/mes")

    elif tipo == "bundle":
        ben = data.get("beneficios", {})
        parts.append(f"Ahorro: ${ben.get('descuento_factura_hogar', 0):,}/mes + {ben.get('gigas_extra_linea_movil', 0)}GB extra")
        parts.append("Este bundle combina fibra optica + portabilidad movil con descuento adicional.")

    parts.append("RECORDATORIO: NUNCA mencionar el precio sin descuento ni el precio post-promo.")

    return "\n".join(parts) + "\n"


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

    # Inyectar contexto para tacticas de competencia
    competition_tactics = (
        "sondear_competencia", "comparar_competencia", "ventaja_exclusiva",
        "pivotar_producto", "ofrecer_bundle",
    )
    if tactic in competition_tactics:
        # Datos faltantes para sondeo
        faltantes = []
        if not bb.get("competitor_service_type"):
            faltantes.append("tipo de servicio (internet/fibra o celular/movil)")
        if not bb.get("competitor_provider"):
            faltantes.append("proveedor")
        if not bb.get("competitor_price"):
            faltantes.append("precio mensual")

        # Resumen de comparacion
        comp_result = bb.get("comparison_result") or {}
        comp_summary = comp_result.get("resumen", "Sin datos de comparacion aun")

        # Producto que estamos vendiendo
        product = bb.get("product_to_sell") or "por definir"
        prod_label = {"portabilidad": "Portabilidad Movil", "fibra": "Fibra Optica", "bundle": "Bundle Fibra + Portabilidad"}

        # Productos rechazados
        rejected = bb.get("products_rejected", [])
        rejected_labels = [prod_label.get(r, r) for r in rejected]

        tactic_prompt = tactic_prompt.format(
            datos_faltantes=", ".join(faltantes) if faltantes else "ninguno",
            comparison_summary=comp_summary,
            product_to_sell=prod_label.get(product, product),
            products_rejected=", ".join(rejected_labels) if rejected_labels else "ninguno",
        )

    full_system = system + "\n" + phase_prompt + "\n" + tactic_prompt

    # Contexto de cobertura pendiente
    if bb.get("cobertura_pendiente"):
        full_system += """
COBERTURA PENDIENTE: El cliente dijo que no tiene cobertura de fibra en su zona.
Reencuadra positivamente: Movistar invirtio mucho en infraestructura y es posible que ahora
si haya cobertura. Pedi la direccion para que un compañero de backoffice verifique.
Luego transiciona naturalmente a portabilidad movil.
Ejemplo: "Mirá, Movistar viene invirtiendo mucho en infraestructura, puede que tu zona
ahora tenga cobertura. Pasame tu direccion y le pido a un compañero que lo verifique.
Mientras tanto, te cuento que tambien tenemos planes de celular re buenos..."
NO preguntes "tenes cobertura?" - pedi la direccion directamente.
"""

    # Agregar contexto competidor y promo si aplica
    if bb.get("competitor_provider") or bb.get("sub_state") == "competencia":
        full_system += _build_competitor_context(bb)
    if bb.get("selected_promo_id") or bb.get("product_to_sell"):
        full_system += _build_promo_context(bb)

    # Mensajes de la conversacion
    messages = [SystemMessage(content=full_system)] + list(bb.get("messages", []))

    result = await sonnet.ainvoke(messages)
    return result.content
