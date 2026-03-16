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
