"""Decoradores del Behaviour Tree. Cada funcion recibe blackboard y retorna bool."""


def confianza_70(bb: dict) -> bool:
    return bb.get("confidence", 0) >= 0.70


def confianza_75(bb: dict) -> bool:
    return bb.get("confidence", 0) >= 0.75


def slots_completos(bb: dict) -> bool:
    """True si el perfil del cliente tiene los campos minimos."""
    return bool(bb.get("pain_point")) and bool(bb.get("customer_name"))


def max_1_consecutivo(bb: dict) -> bool:
    """True si no se ha usado la misma categoria de tactica 2 veces seguidas."""
    # Se evalua en la accion misma via used_arguments
    return True


def max_intentos_dinamico(bb: dict) -> bool:
    """Permite hasta N intentos de objecion segun profundidad del arbol.

    - Arbol corto (< 6 turnos): hasta 4 intentos de objecion
    - Arbol medio (6-12): hasta 3
    - Arbol largo (> 12): hasta 2
    """
    tree = bb.get("binary_tree", [])
    depth = len(tree)
    consecutive_ni = bb.get("consecutive_ni", 0)

    if depth < 6:
        max_attempts = 4
    elif depth <= 12:
        max_attempts = 3
    else:
        max_attempts = 2

    return consecutive_ni < max_attempts
