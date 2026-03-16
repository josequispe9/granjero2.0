"""Acciones del Behaviour Tree.

Cada accion escribe `tactic` y `bt_action_id` en el blackboard.
Chequea `used_arguments` para no repetir tacticas (regla Cardone).
"""

from src.behaviour_tree.status import Status


def _set_tactic(bb: dict, tactic: str, action_id: str) -> Status:
    """Helper: asigna tactica si no fue usada antes."""
    if tactic in bb.get("used_arguments", []):
        return Status.FAILURE
    bb["tactic"] = tactic
    bb["bt_action_id"] = action_id
    return Status.SUCCESS


# --- Camino feliz ---

def avanzar_fase(bb: dict) -> Status:
    bb["tactic"] = "avanzar_fase"
    bb["bt_action_id"] = "avanzar_fase"
    return Status.SUCCESS


# --- Ambiguedad ---

def pedir_confirmacion(bb: dict) -> Status:
    bb["tactic"] = "pedir_confirmacion"
    bb["bt_action_id"] = "pedir_confirmacion"
    return Status.SUCCESS


# --- Objeciones de precio ---

def reencuadrar_valor(bb: dict) -> Status:
    return _set_tactic(bb, "reencuadrar_valor", "obj_precio_reencuadrar")


def mostrar_roi(bb: dict) -> Status:
    return _set_tactic(bb, "mostrar_roi", "obj_precio_roi")


def caso_exito(bb: dict) -> Status:
    return _set_tactic(bb, "caso_exito", "obj_precio_caso")


def prueba_piloto(bb: dict) -> Status:
    return _set_tactic(bb, "prueba_piloto", "obj_precio_piloto")


# --- Objeciones de tiempo ---

def inicio_minimo(bb: dict) -> Status:
    return _set_tactic(bb, "inicio_minimo", "obj_tiempo_minimo")


def fecha_flexible(bb: dict) -> Status:
    return _set_tactic(bb, "fecha_flexible", "obj_tiempo_flexible")


def urgencia(bb: dict) -> Status:
    return _set_tactic(bb, "urgencia", "obj_tiempo_urgencia")


# --- Objeciones de necesidad ---

def revelar_pain_point(bb: dict) -> Status:
    return _set_tactic(bb, "revelar_pain_point", "obj_necesidad_revelar")


def pain_point_oculto(bb: dict) -> Status:
    return _set_tactic(bb, "pain_point_oculto", "obj_necesidad_oculto")


# --- Objeciones de autoridad ---

def redirigir_decisor(bb: dict) -> Status:
    return _set_tactic(bb, "redirigir_decisor", "obj_autoridad_redirigir")


def agendar_llamada(bb: dict) -> Status:
    return _set_tactic(bb, "agendar_llamada", "obj_autoridad_agendar")


# --- Competencia ---

def sondear_competencia(bb: dict) -> Status:
    bb["tactic"] = "sondear_competencia"
    bb["bt_action_id"] = "obj_competencia_sondear"
    bb["sondeo_turns"] = bb.get("sondeo_turns", 0) + 1
    return Status.SUCCESS


def _assign_product(bb: dict):
    """Asigna product_to_sell basado en competitor_service_type si aun no esta asignado."""
    if bb.get("product_to_sell"):
        return  # ya asignado
    st = bb.get("competitor_service_type")
    if st == "movil":
        bb["product_to_sell"] = "portabilidad"
    elif st == "fibra":
        bb["product_to_sell"] = "fibra"
    elif st == "ambos":
        bb["product_to_sell"] = "portabilidad"  # primero porta, luego fibra como pivot
    else:
        bb["product_to_sell"] = "portabilidad"  # default


def comparar_competencia(bb: dict) -> Status:
    _assign_product(bb)
    return _set_tactic(bb, "comparar_competencia", "obj_competencia_comparar")


def ventaja_exclusiva(bb: dict) -> Status:
    _assign_product(bb)
    return _set_tactic(bb, "ventaja_exclusiva", "obj_competencia_ventaja")


def pivotar_producto(bb: dict) -> Status:
    """Rechaza el producto actual y pivota al otro."""
    current = bb.get("product_to_sell")
    rejected = list(bb.get("products_rejected", []))
    if current and current not in rejected:
        rejected.append(current)
    bb["products_rejected"] = rejected

    # Determinar nuevo producto
    if current == "portabilidad":
        bb["product_to_sell"] = "fibra"
    elif current == "fibra":
        bb["product_to_sell"] = "portabilidad"
    else:
        bb["product_to_sell"] = "fibra"

    bb["offer_stage"] = "pivot"
    # Limpiar comparacion anterior para generar nueva
    bb["comparison_result"] = None
    bb["tactic"] = "pivotar_producto"
    bb["bt_action_id"] = "obj_competencia_pivotar"
    return Status.SUCCESS


def ofrecer_bundle(bb: dict) -> Status:
    """Ofrece bundle como ultima opcion."""
    rejected = list(bb.get("products_rejected", []))
    current = bb.get("product_to_sell")
    if current and current not in rejected:
        rejected.append(current)
    bb["products_rejected"] = rejected
    bb["product_to_sell"] = "bundle"
    bb["offer_stage"] = "bundle"
    bb["comparison_result"] = None
    bb["tactic"] = "ofrecer_bundle"
    bb["bt_action_id"] = "obj_competencia_bundle"
    return Status.SUCCESS


# --- Terminacion ---

def rechazo_duro_fin(bb: dict) -> Status:
    bb["tactic"] = "rechazo_duro_fin"
    bb["bt_action_id"] = "rechazo_duro_fin"
    bb["termination"] = "HANDOFF"
    return Status.SUCCESS


def fallback_fin(bb: dict) -> Status:
    bb["tactic"] = "fallback_fin"
    bb["bt_action_id"] = "fallback_fin"
    return Status.SUCCESS
