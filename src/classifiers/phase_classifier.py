"""Evalua si la fase Cardone debe avanzar basandose en las condiciones de avance."""


def classify_phase(
    current_phase: str,
    current_state: str,
    sub_state: str,
    pain_point: str | None,
    binary_tree: list[dict],
) -> str:
    """Retorna la nueva fase Cardone (o la misma si no hay avance).

    Condiciones de avance:
    - saludo -> descubrimiento: cliente responde sin rechazo duro
    - descubrimiento -> eleccion: al menos 1 pain point identificado
    - eleccion -> oferta: cliente hace preguntas de implementacion
    - oferta -> conclusion: cliente no rechaza la oferta
    """
    if current_state == "NI":
        # NI nunca avanza fase, solo resuelve objecion y vuelve
        return current_phase

    phases = ["saludo", "descubrimiento", "eleccion", "oferta", "conclusion"]
    idx = phases.index(current_phase) if current_phase in phases else 0

    if current_phase == "saludo" and current_state == "I":
        # Cualquier respuesta sin rechazo avanza
        return "descubrimiento"

    if current_phase == "descubrimiento" and pain_point:
        return "eleccion"

    if current_phase == "eleccion" and current_state == "I" and sub_state == "eleccion":
        return "oferta"

    if current_phase == "oferta" and current_state == "I" and sub_state == "oferta":
        return "conclusion"

    return current_phase
