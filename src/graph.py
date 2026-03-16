"""Grafo LangGraph: classify -> update_tree -> decide_action -> generate -> check_end."""

from langgraph.graph import StateGraph, START, END
from src.state import Blackboard
from src.classifiers.unified_classifier import classify_all
from src.classifiers.phase_classifier import classify_phase
from src.binary_tree.tree import append_node, get_consecutive_ni, should_prune
from src.behaviour_tree.engine import tick_tree
from src.generator.generator import generate_response
from src.termination import evaluate_termination
from src.comparator import compare
from src.promos.loader import load_promo


async def classify(state: Blackboard) -> dict:
    """Nodo: clasificador unificado (1 sola llamada a Haiku)."""
    messages = state["messages"]

    # Contexto competidor acumulado
    competitor_context = {
        "provider": state.get("competitor_provider"),
        "service_type": state.get("competitor_service_type"),
        "plan": state.get("competitor_plan"),
        "price": state.get("competitor_price"),
    }

    # Una sola llamada: estado + injection + revision
    result = await classify_all(
        messages,
        state.get("pain_point"),
        state.get("product_interested"),
        state.get("customer_name", "Cliente"),
        competitor_context=competitor_context,
    )

    updates: dict = {
        "current_state": result["estado"],
        "sub_state": result["subestado"],
        "confidence": result["confianza"],
    }

    # Injection
    if result["injection"]:
        updates["prompt_injection_attempts"] = state.get("prompt_injection_attempts", 0) + 1

    # Revision de perfil
    if result["pain_point"]:
        updates["pain_point"] = result["pain_point"]
    if result["product_interested"]:
        updates["product_interested"] = result["product_interested"]
    if result["customer_name"]:
        updates["customer_name"] = result["customer_name"]

    # Avance de fase
    new_phase = classify_phase(
        state.get("cardone_phase", "saludo"),
        result["estado"],
        result["subestado"],
        updates.get("pain_point") or state.get("pain_point"),
        state.get("binary_tree", []),
    )
    updates["cardone_phase"] = new_phase

    # Objecion
    if result["estado"] == "NI" and result["subestado"] != "ambiguo":
        updates["objection"] = result["subestado"]

    # Campos competidor
    if result.get("competitor_provider"):
        updates["competitor_provider"] = result["competitor_provider"]
    if result.get("competitor_service_type"):
        updates["competitor_service_type"] = result["competitor_service_type"]
    if result.get("competitor_plan"):
        updates["competitor_plan"] = result["competitor_plan"]
    if result.get("competitor_price") is not None:
        updates["competitor_price"] = result["competitor_price"]
    if result.get("competitor_satisfaction"):
        updates["competitor_satisfaction"] = result["competitor_satisfaction"]

    # Cobertura bloqueada: auto-rechazar fibra y pivotar
    if result.get("cobertura_bloqueada"):
        updates["cobertura_pendiente"] = True
        rejected = list(state.get("products_rejected", []))
        if "fibra" not in rejected:
            rejected.append("fibra")
        updates["products_rejected"] = rejected
        # Si estabamos vendiendo fibra, forzar pivot a portabilidad
        if state.get("product_to_sell") == "fibra" or not state.get("product_to_sell"):
            updates["product_to_sell"] = "portabilidad"
            updates["offer_stage"] = "pivot"
            updates["comparison_result"] = None  # limpiar comparacion de fibra

    return updates


def update_tree(state: Blackboard) -> dict:
    """Nodo: actualizar binary tree."""
    tree = list(state.get("binary_tree", []))
    current = state.get("current_state", "IND")
    sub = state.get("sub_state", "ambiguo")

    new_tree = append_node(tree, current, sub)
    consecutive_ni = get_consecutive_ni(new_tree)

    return {
        "binary_tree": new_tree,
        "consecutive_ni": consecutive_ni,
    }


def decide_action(state: Blackboard) -> dict:
    """Nodo: tick del behaviour tree."""
    # Construir dict mutable para el BT
    bb = dict(state)
    tick_tree(bb)

    updates: dict = {
        "tactic": bb.get("tactic"),
        "bt_action_id": bb.get("bt_action_id"),
        "bt_trace": bb.get("bt_trace", []),
    }

    # Registrar tactica usada
    non_tracked = ("avanzar_fase", "pedir_confirmacion", "fallback_fin", "pivotar_producto", "ofrecer_bundle")
    if bb.get("tactic") and bb["tactic"] not in non_tracked:
        used = list(state.get("used_arguments", []))
        if bb["tactic"] not in used:
            used.append(bb["tactic"])
        updates["used_arguments"] = used

    # Propagar sondeo_turns
    if bb.get("sondeo_turns") is not None:
        updates["sondeo_turns"] = bb["sondeo_turns"]

    # Propagar campos de producto
    if bb.get("product_to_sell") is not None:
        updates["product_to_sell"] = bb["product_to_sell"]
    if bb.get("products_rejected") is not None:
        updates["products_rejected"] = bb["products_rejected"]
    if bb.get("offer_stage"):
        updates["offer_stage"] = bb["offer_stage"]
    if bb.get("comparison_result") is not None:
        updates["comparison_result"] = bb["comparison_result"]

    # Ejecutar comparador si tactic necesita comparacion
    product = bb.get("product_to_sell")
    if bb.get("tactic") in ("comparar_competencia", "pivotar_producto", "ofrecer_bundle"):
        selected_promo = state.get("selected_promo_id")

        # Elegir promo segun product_to_sell
        if product == "fibra":
            promo_data = load_promo("fibra")
        elif product == "bundle":
            promo_data = load_promo("bundle_fibra_portabilidad")
        elif product == "portabilidad" and selected_promo:
            promo_data = load_promo(selected_promo)
        else:
            promo_data = None

        if promo_data:
            service_type = state.get("competitor_service_type")
            # Para comparar, mapear product_to_sell al service_type del comparador
            compare_service = "fibra" if product == "fibra" else "movil" if product == "portabilidad" else service_type
            competitor_offer = {
                "provider": state.get("competitor_provider"),
                "service_type": compare_service,
                "plan": state.get("competitor_plan"),
                "price": state.get("competitor_price"),
                "satisfaction": state.get("competitor_satisfaction"),
            }
            comparison = compare(competitor_offer, promo_data)
            updates["comparison_result"] = comparison

    # Propagate termination if BT set it
    if bb.get("termination"):
        updates["termination"] = bb["termination"]

    return updates


async def generate(state: Blackboard) -> dict:
    """Nodo: Sonnet genera respuesta con la tactica seleccionada."""
    response = await generate_response(state)
    return {"messages": [{"role": "assistant", "content": response}]}


def check_end(state: Blackboard) -> dict:
    """Nodo: evalua terminacion."""
    term = evaluate_termination(state)
    updates: dict = {}
    if term:
        updates["termination"] = term
        if term == "CIERRE":
            updates["bought"] = True
    return updates


def route_after_check(state: Blackboard) -> str:
    """Edge condicional: si hay terminacion, ir a END."""
    if state.get("termination"):
        return END
    return END  # Una invocacion por mensaje, siempre termina


# --- Compilar grafo ---

graph = StateGraph(Blackboard)
graph.add_node("classify", classify)
graph.add_node("update_tree", update_tree)
graph.add_node("decide_action", decide_action)
graph.add_node("generate", generate)
graph.add_node("check_end", check_end)

graph.add_edge(START, "classify")
graph.add_edge("classify", "update_tree")
graph.add_edge("update_tree", "decide_action")
graph.add_edge("decide_action", "generate")
graph.add_edge("generate", "check_end")
graph.add_edge("check_end", END)

agent = graph.compile()
