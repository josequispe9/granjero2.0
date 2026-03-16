import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import conversations
from src.db import load_session, save_session
from src.graph import agent
from src.binary_tree.metrics import compute_metrics
from src.promos.loader import list_promos, load_promo

app = FastAPI(title="Vendedor IA - Agente CBST", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_NAME = "Lucas"


def _get_content(msg) -> str:
    """Extrae contenido de un mensaje (LangChain object o dict)."""
    if hasattr(msg, "content"):
        return msg.content
    if isinstance(msg, dict):
        return msg.get("content", "")
    return str(msg)


def _default_state(session_id: str, customer_name: str) -> dict:
    """Estado inicial outbound: fase saludo, estado I."""
    return {
        "session_id": session_id,
        "customer_name": customer_name,
        "name": AGENT_NAME,
        "messages": [],
        "current_state": "I",
        "sub_state": "saludo",
        "confidence": 1.0,
        "cardone_phase": "saludo",
        "pain_point": None,
        "product_interested": None,
        "binary_tree": [],
        "objection": None,
        "used_arguments": [],
        "consecutive_ni": 0,
        "consecutive_ind": 0,
        "competitor_provider": None,
        "competitor_service_type": None,
        "competitor_plan": None,
        "competitor_price": None,
        "competitor_satisfaction": None,
        "sondeo_turns": 0,
        "comparison_result": None,
        "selected_promo_id": None,
        "product_to_sell": None,
        "products_rejected": [],
        "offer_stage": "primary",
        "cobertura_pendiente": False,
        "tactic": None,
        "bt_action_id": None,
        "bt_trace": [],
        "termination": None,
        "bought": False,
        "score_conversation": "NEUTRO",
        "take_human": False,
        "prompt_injection_attempts": 0,
        "asleep": False,
    }


# --- API ---

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    customer_name: str | None = None
    selected_promo_id: str | None = None


class StartRequest(BaseModel):
    customer_name: str
    selected_promo_id: str | None = None


@app.get("/promos")
async def get_promos():
    """Retorna promos de portabilidad para el dropdown."""
    return list_promos()


@app.get("/planes-fibra")
async def get_planes_fibra():
    """Retorna planes de fibra (siempre los mismos)."""
    return load_promo("fibra")


@app.get("/bundle-info")
async def get_bundle_info():
    """Retorna info del bundle porta+fibra."""
    return load_promo("bundle_fibra_portabilidad")


@app.get("/promo/{promo_id}")
async def get_promo(promo_id: str):
    """Retorna datos de una promo por id (GET simple, sin sesion)."""
    data = load_promo(promo_id)
    if not data:
        raise HTTPException(status_code=404, detail="Promo no encontrada")
    return data


class SelectPromoRequest(BaseModel):
    session_id: str
    promo_id: str


@app.post("/select-promo")
async def select_promo(req: SelectPromoRequest):
    """Selecciona una promo para la sesion."""
    promo_data = load_promo(req.promo_id)
    if not promo_data:
        raise HTTPException(status_code=404, detail="Promo no encontrada")
    doc = await load_session(req.session_id)
    if doc:
        doc["selected_promo_id"] = req.promo_id
        await save_session(req.session_id, doc)
    return {"promo_id": req.promo_id, "promo_data": promo_data}


@app.get("/graph")
async def get_graph():
    image = agent.get_graph().draw_mermaid_png()
    return Response(content=image, media_type="image/png")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    doc = await load_session(session_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    return doc


SALUDO_TEMPLATE = (
    "Hola {name}! Soy Lucas de Movistar. "
    "Vi que estas en la zona y queria consultarte: "
    "como te esta andando el servicio de internet que tenes actualmente?"
)


@app.post("/start")
async def start_conversation(req: StartRequest):
    """Inicia conversacion outbound: primer mensaje hardcodeado."""
    session_id = str(uuid.uuid4())
    response_text = SALUDO_TEMPLATE.format(name=req.customer_name)

    state = _default_state(session_id, req.customer_name)
    state["messages"] = [{"role": "assistant", "content": response_text}]
    if req.selected_promo_id:
        state["selected_promo_id"] = req.selected_promo_id

    await save_session(session_id, state)

    return {
        "response": response_text,
        "session_id": session_id,
        "customer_name": req.customer_name,
        "state": _public_state(state),
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    doc = await load_session(session_id)

    if doc:
        history = doc.get("messages", [])
        customer_name = doc.get("customer_name", req.customer_name or "Cliente")
    else:
        history = []
        customer_name = req.customer_name or "Cliente"

    # Construir estado para el grafo
    state = _default_state(session_id, customer_name)
    if doc:
        # Restaurar estado persistido
        for key in state:
            if key in doc and key != "messages":
                state[key] = doc[key]

    # Setear promo seleccionada desde request o doc
    if req.selected_promo_id:
        state["selected_promo_id"] = req.selected_promo_id
    elif doc and doc.get("selected_promo_id"):
        state["selected_promo_id"] = doc["selected_promo_id"]

    # Agregar mensaje del usuario
    messages = history + [{"role": "user", "content": req.message}]
    state["messages"] = messages

    # Verificar si ya termino
    if state.get("termination"):
        return {
            "response": "Esta conversacion ya finalizo.",
            "session_id": session_id,
            "customer_name": customer_name,
            "state": _public_state(state),
        }

    # Invocar grafo
    result = await agent.ainvoke(state)

    response_text = _get_content(result["messages"][-1])

    updated_messages = history + [
        {"role": "user", "content": req.message},
        {"role": "assistant", "content": response_text},
    ]

    save_state = _extract_save_state(session_id, customer_name, result, updated_messages)
    await save_session(session_id, save_state)

    return {
        "response": response_text,
        "session_id": session_id,
        "customer_name": customer_name,
        "state": _public_state(save_state),
    }


def _extract_save_state(session_id: str, customer_name: str, result: dict, messages: list) -> dict:
    """Extrae campos del resultado del grafo para persistir."""
    return {
        "session_id": session_id,
        "customer_name": result.get("customer_name", customer_name),
        "name": result.get("name", AGENT_NAME),
        "messages": messages,
        "current_state": result.get("current_state", "I"),
        "sub_state": result.get("sub_state", "saludo"),
        "confidence": result.get("confidence", 1.0),
        "cardone_phase": result.get("cardone_phase", "saludo"),
        "pain_point": result.get("pain_point"),
        "product_interested": result.get("product_interested"),
        "competitor_provider": result.get("competitor_provider"),
        "competitor_service_type": result.get("competitor_service_type"),
        "competitor_plan": result.get("competitor_plan"),
        "competitor_price": result.get("competitor_price"),
        "competitor_satisfaction": result.get("competitor_satisfaction"),
        "sondeo_turns": result.get("sondeo_turns", 0),
        "comparison_result": result.get("comparison_result"),
        "selected_promo_id": result.get("selected_promo_id"),
        "product_to_sell": result.get("product_to_sell"),
        "products_rejected": result.get("products_rejected", []),
        "offer_stage": result.get("offer_stage", "primary"),
        "cobertura_pendiente": result.get("cobertura_pendiente", False),
        "binary_tree": result.get("binary_tree", []),
        "objection": result.get("objection"),
        "used_arguments": result.get("used_arguments", []),
        "consecutive_ni": result.get("consecutive_ni", 0),
        "consecutive_ind": result.get("consecutive_ind", 0),
        "tactic": result.get("tactic"),
        "bt_action_id": result.get("bt_action_id"),
        "bt_trace": result.get("bt_trace", []),
        "termination": result.get("termination"),
        "bought": result.get("bought", False),
        "score_conversation": result.get("score_conversation", "NEUTRO"),
        "take_human": result.get("take_human", False),
        "prompt_injection_attempts": result.get("prompt_injection_attempts", 0),
        "asleep": result.get("asleep", False),
        "metrics": compute_metrics(result.get("binary_tree", [])),
    }


def _public_state(state: dict) -> dict:
    """Campos visibles para el frontend."""
    return {k: v for k, v in state.items() if k != "messages"}
