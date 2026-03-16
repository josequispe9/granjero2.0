"""Comparador determinista: compara oferta competidor vs promo Movistar seleccionada."""

import re


def _extract_gb(text: str | None) -> int | None:
    """Intenta extraer GB de un string como '10GB', '10 gigas', etc."""
    if not text:
        return None
    m = re.search(r"(\d+)\s*(?:gb|gigas?)", text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _extract_mb(text: str | None) -> int | None:
    """Intenta extraer velocidad Mbps de un string como '100mb', '300 megas'."""
    if not text:
        return None
    m = re.search(r"(\d+)\s*(?:mb|mbps|megas?)", text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def _find_best_mobile_plan(gb: int | None, promo_data: dict) -> dict | None:
    """Selecciona el plan movil mas cercano al tier del competidor."""
    planes = promo_data.get("planes_base", [])
    precios = {}
    for promo in promo_data.get("promociones", []):
        precios = promo.get("precios", {})
        break  # usar primera promo disponible

    if not planes:
        return None

    if gb is None:
        # Sin dato de GB, recomendar plan_8gb como default
        for p in planes:
            if p["plan_id"] == "plan_8gb":
                precio = precios.get("plan_8gb", {})
                return {**p, **precio}
        return {**planes[0], **precios.get(planes[0]["plan_id"], {})}

    best = None
    best_diff = float("inf")
    for p in planes:
        pid = p["plan_id"]
        if pid not in precios:
            continue
        diff = abs(p["datos_gb"] - gb)
        if diff < best_diff or (diff == best_diff and p["datos_gb"] >= gb):
            best_diff = diff
            best = {**p, **precios[pid]}
    return best


def _find_best_fiber_plan(mb: int | None, promo_data: dict) -> dict | None:
    """Selecciona el plan fibra mas cercano."""
    planes = promo_data.get("planes_internet", [])
    if not planes:
        return None

    if mb is None:
        return planes[0]

    best = None
    best_diff = float("inf")
    for p in planes:
        diff = abs(p["velocidad_mb"] - mb)
        if diff < best_diff or (diff == best_diff and p["velocidad_mb"] >= mb):
            best_diff = diff
            best = p
    return best


def compare(competitor: dict, promo_data: dict) -> dict:
    """Compara oferta competidor vs promo Movistar.

    Args:
        competitor: {provider, service_type, plan, price, satisfaction}
        promo_data: JSON cargado de la promo seleccionada

    Returns:
        ventajas: list[str]
        ahorro_estimado: int | None
        mejor_plan: dict
        datos_faltantes: list[str]
        resumen: str
    """
    comp_plan = competitor.get("plan")
    comp_price = competitor.get("price")
    comp_provider = competitor.get("provider", "la competencia")
    service_type = competitor.get("service_type")

    datos_faltantes = []
    if not comp_price:
        datos_faltantes.append("precio del competidor")

    # Detectar tipo de servicio y encontrar mejor plan
    comp_gb = _extract_gb(comp_plan)
    comp_mb = _extract_mb(comp_plan)
    mejor_plan = None

    # Usar service_type explicito si disponible, sino inferir de promo_data
    if service_type == "fibra" or (not service_type and "planes_internet" in promo_data):
        mejor_plan = _find_best_fiber_plan(comp_mb, promo_data)
    elif service_type == "movil" or (not service_type and "planes_base" in promo_data):
        mejor_plan = _find_best_mobile_plan(comp_gb, promo_data)

    if not mejor_plan:
        mejor_plan = {}

    # Calcular ahorro
    ahorro = None
    movistar_price = mejor_plan.get("precio_final")
    if comp_price and movistar_price:
        ahorro = comp_price - movistar_price

    # Ventajas genericas
    ventajas = []
    if ahorro and ahorro > 0:
        ventajas.append(f"Ahorro de ${ahorro:,}/mes vs {comp_provider}")

    # Beneficios moviles
    beneficios = mejor_plan.get("beneficios_base", {})
    if beneficios.get("whatsapp_gratis"):
        ventajas.append("WhatsApp ilimitado gratis")
    if beneficios.get("llamadas_ilimitadas"):
        ventajas.append("Llamadas ilimitadas")
    if mejor_plan.get("roaming"):
        zona = mejor_plan["roaming"].get("zona", "")
        gb_roam = mejor_plan["roaming"].get("datos_incluidos_gb", 0)
        ventajas.append(f"Roaming incluido: {gb_roam}GB en {zona}")

    # Beneficios de promo
    for promo in promo_data.get("promociones", []):
        bps = promo.get("beneficios_promocion", {})
        for b in bps.get("beneficios_generales", []):
            if "Movistar con Todo" in b:
                ventajas.append("Movistar con Todo: ahorra $4000/mes + 4GB extra")
            elif "Guarda Gigas" in b:
                ventajas.append("Guarda Gigas: tus GB no se pierden")
        break

    # Beneficios fibra
    cond = promo_data.get("condiciones_comerciales", {})
    if cond.get("mes_gratis_fibra"):
        ventajas.append("1 mes gratis de fibra")

    # Datos del plan
    plan_desc = ""
    if mejor_plan.get("datos_gb"):
        plan_desc = f"{mejor_plan['datos_gb']}GB"
    elif mejor_plan.get("velocidad_mb"):
        plan_desc = f"{mejor_plan['velocidad_mb']}Mb fibra"

    precio_desc = f"${movistar_price:,}/mes" if movistar_price else "consultar"

    # Resumen enfatico para inyectar en prompt
    partes = []

    # Linea 1: comparacion directa de precio
    if comp_price and movistar_price:
        if ahorro and ahorro > 0:
            partes.append(
                f"PRECIO: El cliente paga ${comp_price:,}/mes con {comp_provider}. "
                f"Movistar ofrece {plan_desc} a ${movistar_price:,}/mes. "
                f"ES ${ahorro:,}/MES MAS BARATO. DEBES mencionar este ahorro."
            )
        elif ahorro is not None and ahorro == 0:
            partes.append(
                f"PRECIO: Mismo precio (${movistar_price:,}/mes) pero con MAS beneficios. "
                f"Enfocate en los extras que {comp_provider} no tiene."
            )
        else:
            partes.append(
                f"PRECIO: Movistar ${movistar_price:,}/mes vs {comp_provider} ${comp_price:,}/mes. "
                f"El precio es similar, enfocate en beneficios extras que compensan."
            )
    else:
        partes.append(f"Plan Movistar recomendado: {plan_desc} a {precio_desc}")

    # Linea 2: beneficios extras concretos
    extras_que_no_tiene = [v for v in ventajas if "Ahorro" not in v]
    if extras_que_no_tiene:
        partes.append(
            f"EXTRAS que {comp_provider} NO incluye: " + "; ".join(extras_que_no_tiene[:4])
        )

    if datos_faltantes:
        partes.append("Datos faltantes del competidor: " + ", ".join(datos_faltantes))

    resumen = "\n".join(partes)

    return {
        "ventajas": ventajas,
        "ahorro_estimado": ahorro,
        "mejor_plan": mejor_plan,
        "datos_faltantes": datos_faltantes,
        "resumen": resumen,
    }
