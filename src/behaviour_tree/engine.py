"""Motor del Behaviour Tree.

Clases base: Node, Selector (Fallback), Sequence, Condition, Action, Decorator.
Cada nodo tiene tick(bb) -> Status.
Todos los nodos registran su visita en bb["bt_trace"].
"""

from src.behaviour_tree.status import Status
from src.behaviour_tree.conditions import (
    estado_I, estado_NI, estado_IND,
    subestado_precio, subestado_tiempo, subestado_necesidad, subestado_autoridad,
    subestado_rechazo_duro,
)
from src.behaviour_tree.actions import (
    avanzar_fase, pedir_confirmacion,
    reencuadrar_valor, mostrar_roi, caso_exito, prueba_piloto,
    inicio_minimo, fecha_flexible, urgencia,
    revelar_pain_point, pain_point_oculto,
    redirigir_decisor, agendar_llamada,
    rechazo_duro_fin, fallback_fin,
)
from src.behaviour_tree.decorators import (
    max_intentos_dinamico, confianza_70, confianza_75,
    slots_completos, max_1_consecutivo,
)


def _trace(bb: dict, node_id: str, node_type: str, label: str, status: Status):
    """Registra la visita de un nodo en el trace."""
    bb.setdefault("bt_trace", []).append({
        "id": node_id,
        "type": node_type,
        "label": label,
        "status": status.value,
    })


class Node:
    def __init__(self, node_id: str = "", label: str = ""):
        self.node_id = node_id
        self.label = label

    def tick(self, bb: dict) -> Status:
        raise NotImplementedError


class Selector(Node):
    """Fallback: ejecuta hijos hasta que uno tenga SUCCESS."""
    def __init__(self, children: list[Node], node_id: str = "", label: str = ""):
        super().__init__(node_id, label)
        self.children = children

    def tick(self, bb: dict) -> Status:
        for child in self.children:
            result = child.tick(bb)
            if result == Status.SUCCESS:
                _trace(bb, self.node_id, "selector", self.label, Status.SUCCESS)
                return Status.SUCCESS
        _trace(bb, self.node_id, "selector", self.label, Status.FAILURE)
        return Status.FAILURE


class Sequence(Node):
    """Ejecuta hijos en orden; falla si alguno falla."""
    def __init__(self, children: list[Node], node_id: str = "", label: str = ""):
        super().__init__(node_id, label)
        self.children = children

    def tick(self, bb: dict) -> Status:
        for child in self.children:
            result = child.tick(bb)
            if result == Status.FAILURE:
                _trace(bb, self.node_id, "sequence", self.label, Status.FAILURE)
                return Status.FAILURE
        _trace(bb, self.node_id, "sequence", self.label, Status.SUCCESS)
        return Status.SUCCESS


class Condition(Node):
    def __init__(self, fn, node_id: str = "", label: str = ""):
        super().__init__(node_id, label)
        self.fn = fn

    def tick(self, bb: dict) -> Status:
        result = Status.SUCCESS if self.fn(bb) else Status.FAILURE
        _trace(bb, self.node_id, "condition", self.label, result)
        return result


class Action(Node):
    def __init__(self, fn, node_id: str = "", label: str = ""):
        super().__init__(node_id, label)
        self.fn = fn

    def tick(self, bb: dict) -> Status:
        result = self.fn(bb)
        _trace(bb, self.node_id, "action", self.label, result)
        return result


class Decorator(Node):
    def __init__(self, fn, child: Node, node_id: str = "", label: str = ""):
        super().__init__(node_id, label)
        self.fn = fn
        self.child = child

    def tick(self, bb: dict) -> Status:
        if self.fn(bb):
            result = self.child.tick(bb)
            _trace(bb, self.node_id, "decorator", self.label, result)
            return result
        _trace(bb, self.node_id, "decorator", self.label, Status.FAILURE)
        return Status.FAILURE


# --- Arbol completo ---

def _build_tree() -> Node:
    """Construye el BT con IDs para tracing."""

    # Camino feliz: I -> avanzar fase
    camino_feliz = Sequence([
        Condition(estado_I, "c_I", "estado_I"),
        Decorator(confianza_70,
            Action(avanzar_fase, "a_avanzar", "avanzar_fase"),
            "d_conf70", "confianza_70"),
    ], "seq_feliz", "Camino Feliz")

    # Manejo ambiguedad: IND -> pedir confirmacion
    manejo_ambiguedad = Sequence([
        Condition(estado_IND, "c_IND", "estado_IND"),
        Action(pedir_confirmacion, "a_confirmar", "pedir_confirmacion"),
    ], "seq_ambig", "Ambiguedad")

    # Objeciones de precio
    obj_precio = Sequence([
        Condition(subestado_precio, "c_precio", "sub_precio"),
        Decorator(max_intentos_dinamico, Selector([
            Decorator(max_1_consecutivo,
                Action(reencuadrar_valor, "a_reenc", "reencuadrar_valor"),
                "d_max1_reenc", "max1"),
            Decorator(max_1_consecutivo,
                Action(mostrar_roi, "a_roi", "mostrar_roi"),
                "d_max1_roi", "max1"),
            Decorator(max_1_consecutivo,
                Action(caso_exito, "a_caso", "caso_exito"),
                "d_max1_caso", "max1"),
            Action(prueba_piloto, "a_piloto", "prueba_piloto"),
        ], "sel_precio_tac", "Tacticas"), "d_max_precio", "max_intentos"),
    ], "seq_precio", "Obj Precio")

    # Objeciones de tiempo
    obj_tiempo = Sequence([
        Condition(subestado_tiempo, "c_tiempo", "sub_tiempo"),
        Decorator(max_intentos_dinamico, Selector([
            Decorator(max_1_consecutivo,
                Action(inicio_minimo, "a_minimo", "inicio_minimo"),
                "d_max1_min", "max1"),
            Decorator(max_1_consecutivo,
                Action(fecha_flexible, "a_fecha", "fecha_flexible"),
                "d_max1_fecha", "max1"),
            Action(urgencia, "a_urgencia", "urgencia"),
        ], "sel_tiempo_tac", "Tacticas"), "d_max_tiempo", "max_intentos"),
    ], "seq_tiempo", "Obj Tiempo")

    # Objeciones de necesidad
    obj_necesidad = Sequence([
        Condition(subestado_necesidad, "c_necesidad", "sub_necesidad"),
        Decorator(max_intentos_dinamico, Selector([
            Decorator(max_1_consecutivo,
                Action(revelar_pain_point, "a_revelar", "revelar_pain_point"),
                "d_max1_rev", "max1"),
            Action(pain_point_oculto, "a_oculto", "pain_point_oculto"),
        ], "sel_nec_tac", "Tacticas"), "d_max_nec", "max_intentos"),
    ], "seq_necesidad", "Obj Necesidad")

    # Objeciones de autoridad
    obj_autoridad = Sequence([
        Condition(subestado_autoridad, "c_autoridad", "sub_autoridad"),
        Selector([
            Decorator(max_1_consecutivo,
                Action(redirigir_decisor, "a_redir", "redirigir_decisor"),
                "d_max1_redir", "max1"),
            Action(agendar_llamada, "a_agendar", "agendar_llamada"),
        ], "sel_aut_tac", "Tacticas"),
    ], "seq_autoridad", "Obj Autoridad")

    # Rechazo duro
    rechazo = Sequence([
        Condition(subestado_rechazo_duro, "c_rechazo", "sub_rechazo_duro"),
        Action(rechazo_duro_fin, "a_rechazo", "rechazo_duro_fin"),
    ], "seq_rechazo", "Rechazo Duro")

    # Manejo objeciones completo
    manejo_objeciones = Sequence([
        Condition(estado_NI, "c_NI", "estado_NI"),
        Selector([
            obj_precio,
            obj_tiempo,
            obj_necesidad,
            obj_autoridad,
            rechazo,
        ], "sel_objs", "Tipo Objecion"),
    ], "seq_objs", "Objeciones")

    # Arbol principal
    return Selector([
        camino_feliz,
        manejo_ambiguedad,
        manejo_objeciones,
        Action(fallback_fin, "a_fallback", "fallback_fin"),
    ], "sel_root", "Root")


_TREE = _build_tree()


def tick_tree(bb: dict) -> dict:
    """Ejecuta un tick del BT y retorna el blackboard actualizado."""
    bb["bt_trace"] = []  # Reset trace cada tick
    _TREE.tick(bb)
    return bb
