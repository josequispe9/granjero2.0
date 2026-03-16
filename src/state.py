from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class Blackboard(TypedDict):
    # --- Mensajes LangGraph ---
    messages: Annotated[list, add_messages]

    # --- Clasificacion de estado ---
    current_state: str          # I | NI | IND
    sub_state: str              # subestado activo
    confidence: float           # confianza del clasificador

    # --- Fase Cardone ---
    cardone_phase: str          # saludo | descubrimiento | eleccion | oferta | conclusion

    # --- Perfil del cliente ---
    pain_point: str | None
    product_interested: str | None
    customer_name: str

    # --- Binary tree ---
    binary_tree: list[dict]     # lista plana de nodos {state, sub_state, turn}

    # --- Objeciones ---
    objection: str | None       # precio | tiempo | necesidad | autoridad | rechazo_duro
    used_arguments: list[str]   # tacticas ya usadas (no repetir)
    consecutive_ni: int
    consecutive_ind: int

    # --- Behaviour tree output ---
    tactic: str | None          # tactica seleccionada por el BT
    bt_action_id: str | None    # id de la accion BT ejecutada
    bt_trace: list[dict]        # traza del ultimo tick [{id, type, label, status}]

    # --- Terminacion ---
    termination: str | None     # CIERRE | PODA | HANDOFF
    bought: bool
    score_conversation: str     # NO_COMPRO..COMPRO

    # --- Control ---
    take_human: bool
    prompt_injection_attempts: int
    asleep: bool
    name: str                   # nombre del agente vendedor
