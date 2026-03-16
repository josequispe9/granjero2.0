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

    # --- Competencia / Sondeo ---
    competitor_provider: str | None      # "Claro", "Personal", etc.
    competitor_service_type: str | None  # "movil" | "fibra" | "ambos"
    competitor_plan: str | None          # "10GB", "100mb fibra"
    competitor_price: int | None         # precio mensual
    competitor_satisfaction: str | None  # "conforme" | "quejas" | "neutro"
    sondeo_turns: int                    # contador de turnos de sondeo
    comparison_result: dict | None       # salida del comparador

    # --- Promo seleccionada ---
    selected_promo_id: str | None

    # --- Producto a vender ---
    product_to_sell: str | None          # "portabilidad" | "fibra" | "bundle" | None
    products_rejected: list[str]         # productos rechazados: ["portabilidad"], ["fibra"], etc.
    offer_stage: str                     # "primary" | "pivot" | "bundle"
    cobertura_pendiente: bool            # True = derivar a backoffice para verificar cobertura fibra

    # --- Objeciones ---
    objection: str | None       # precio | tiempo | necesidad | autoridad | rechazo_duro | competencia
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
