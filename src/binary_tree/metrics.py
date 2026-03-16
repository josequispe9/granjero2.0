"""Metricas derivadas del binary tree."""


def compute_metrics(tree: list[dict]) -> dict:
    if not tree:
        return {
            "total_turns": 0,
            "i_count": 0,
            "ni_count": 0,
            "reversion_rate": 0.0,
            "depth": 0,
        }

    i_count = sum(1 for n in tree if n["state"] == "I")
    ni_count = sum(1 for n in tree if n["state"] == "NI")

    # Tasa de reversion: NI seguido de I / total NI
    reversions = 0
    for i in range(len(tree) - 1):
        if tree[i]["state"] == "NI" and tree[i + 1]["state"] == "I":
            reversions += 1

    reversion_rate = reversions / ni_count if ni_count > 0 else 0.0

    return {
        "total_turns": len(tree),
        "i_count": i_count,
        "ni_count": ni_count,
        "reversion_rate": round(reversion_rate, 2),
        "depth": len(tree),
    }
