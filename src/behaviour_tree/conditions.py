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


def subestado_rechazo_duro(bb: dict) -> bool:
    return bb.get("sub_state") == "rechazo_duro"
