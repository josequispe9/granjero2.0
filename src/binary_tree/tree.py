"""Binary tree como lista plana.

Cada nodo: {"state": "I"|"NI", "sub_state": str, "turn": int}
IND es transicional y NO se agrega al arbol.
"""


def append_node(tree: list[dict], state: str, sub_state: str) -> list[dict]:
    """Agrega un nodo al arbol. IND se ignora."""
    if state == "IND":
        return tree
    turn = len(tree) + 1
    return tree + [{"state": state, "sub_state": sub_state, "turn": turn}]


def get_consecutive_ni(tree: list[dict]) -> int:
    """Cuenta NI consecutivos desde el final del arbol."""
    count = 0
    for node in reversed(tree):
        if node["state"] == "NI":
            count += 1
        else:
            break
    return count


def should_prune(tree: list[dict], threshold: int = 3) -> bool:
    """True si hay >= threshold NI consecutivos al final."""
    return get_consecutive_ni(tree) >= threshold


def get_path_signature(tree: list[dict]) -> str:
    """Genera firma del camino: 'I-I-NI-I-NI-NI-NI'."""
    return "-".join(node["state"] for node in tree)
