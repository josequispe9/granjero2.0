"""Condiciones del Behaviour Tree. Cada funcion recibe blackboard y retorna bool."""


def estado_I(bb: dict) -> bool:
    return bb.get("current_state") == "I"


def estado_NI(bb: dict) -> bool:
    return bb.get("current_state") == "NI"


def estado_IND(bb: dict) -> bool:
    return bb.get("current_state") == "IND"


def subestado_precio(bb: dict) -> bool:
    return bb.get("sub_state") == "precio"


def subestado_tiempo(bb: dict) -> bool:
    return bb.get("sub_state") == "tiempo"


def subestado_necesidad(bb: dict) -> bool:
    return bb.get("sub_state") == "necesidad"


def subestado_autoridad(bb: dict) -> bool:
    return bb.get("sub_state") == "autoridad"


def subestado_competencia(bb: dict) -> bool:
    return bb.get("sub_state") == "competencia"


def subestado_rechazo_duro(bb: dict) -> bool:
    return bb.get("sub_state") == "rechazo_duro"


def producto_no_rechazado(bb: dict) -> bool:
    """True si el producto actual no fue rechazado."""
    product = bb.get("product_to_sell")
    if not product:
        return False
    return product not in bb.get("products_rejected", [])


def puede_pivotar(bb: dict) -> bool:
    """True si hay un producto alternativo no rechazado al que pivotar."""
    rejected = bb.get("products_rejected", [])
    current = bb.get("product_to_sell")
    # Determinar el otro producto
    if current == "portabilidad":
        return "fibra" not in rejected
    elif current == "fibra":
        return "portabilidad" not in rejected
    # Si no hay producto asignado, se puede pivotar si hay algun producto disponible
    return "portabilidad" not in rejected or "fibra" not in rejected


def puede_bundle(bb: dict) -> bool:
    """True si ambos productos individuales fueron rechazados y bundle no."""
    rejected = bb.get("products_rejected", [])
    return "portabilidad" in rejected and "fibra" in rejected and "bundle" not in rejected
