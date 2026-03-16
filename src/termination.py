"""Evaluacion de terminacion: CIERRE, PODA, HANDOFF."""


def evaluate_termination(bb: dict) -> str | None:
    """Retorna el tipo de terminacion o None si la conversacion continua.

    - CIERRE: el cliente compro
    - PODA: 3+ NI consecutivos (cliente no va a comprar)
    - HANDOFF: rechazo duro, injection >= 3, o take_human
    """
    # Ya terminada
    if bb.get("termination"):
        return bb["termination"]

    # CIERRE: bought
    if bb.get("bought"):
        return "CIERRE"

    # PODA: 3 NI consecutivos
    if bb.get("consecutive_ni", 0) >= 3:
        return "PODA"

    # HANDOFF: injection
    if bb.get("prompt_injection_attempts", 0) >= 3:
        return "HANDOFF"

    # HANDOFF: take_human
    if bb.get("take_human"):
        return "HANDOFF"

    # HANDOFF: rechazo duro (ya manejado por BT, pero por seguridad)
    if bb.get("sub_state") == "rechazo_duro" and bb.get("current_state") == "NI":
        return "HANDOFF"

    return None
