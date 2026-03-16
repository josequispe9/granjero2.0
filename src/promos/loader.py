"""Carga y cachea los JSON de promos.

El operador selecciona la promo de PORTABILIDAD del dia (marzo_75/80/85).
Los planes de FIBRA son siempre los mismos.
El BUNDLE se aplica automaticamente cuando el cliente quiere porta + fibra.
"""

import json
from pathlib import Path

_DIR = Path(__file__).parent

_cache: dict[str, dict] = {}


def _load_json(filename: str) -> dict:
    path = _DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


def _build_portabilidad_promo(promo_index: int) -> dict:
    """Extrae una promo especifica de portabilidad con sus planes y precios."""
    raw = _load_json("portabilidad_individuos.json")
    promo = raw["promociones"][promo_index]
    precios = promo.get("precios", {})

    planes = []
    for plan in raw["planes_base"]:
        pid = plan["plan_id"]
        if pid not in precios:
            continue
        planes.append({
            "plan_id": pid,
            "datos_gb": plan["datos_gb"],
            "precio_final": precios[pid]["precio_final"],
            "beneficios_base": plan.get("beneficios_base", {}),
            "roaming": plan.get("roaming"),
        })

    bps = promo.get("beneficios_promocion", {})
    return {
        "promo_id": promo["promo_id"],
        "tipo": "portabilidad",
        "nombre": promo["nombre"],
        "porcentaje_descuento": promo["porcentaje_descuento"],
        "duracion_descuento_meses": promo["duracion_descuento_meses"],
        "planes": planes,
        "beneficios_generales": bps.get("beneficios_generales", []),
        # Mantener estructura original para comparator
        "planes_base": raw["planes_base"],
        "promociones": [promo],
    }


def _build_fibra_promo() -> dict:
    """Retorna la promo de fibra normalizada."""
    raw = _load_json("venta_fibra_individuos.json")
    planes = []
    for plan in raw.get("planes_internet", []):
        planes.append({
            "plan_id": plan["plan_id"],
            "velocidad_mb": plan["velocidad_mb"],
            "zona": plan.get("zona", ""),
            "precio_final": plan["precio_final"],
            "descuento_porcentaje": plan.get("descuento_porcentaje"),
        })

    return {
        "promo_id": "fibra",
        "tipo": "fibra",
        "nombre": "Fibra Optica",
        "planes": planes,
        "planes_tv": raw.get("planes_tv", []),
        "condiciones_comerciales": raw.get("condiciones_comerciales", {}),
        # Mantener estructura original para comparator
        "segmento": raw.get("segmento"),
        "planes_internet": raw.get("planes_internet", []),
    }


def _build_bundle_promo() -> dict:
    """Retorna la promo de bundle normalizada."""
    raw = _load_json("portabilidad_mas_fibra_optica.json")
    return {
        "promo_id": "bundle_fibra_portabilidad",
        "tipo": "bundle",
        "nombre": "Bundle Fibra + Portabilidad",
        "beneficios": raw.get("beneficios", {}),
        "condiciones": raw.get("condiciones", {}),
        "notas_operativas": raw.get("notas_operativas", []),
        "tipo_promocion": raw.get("tipo_promocion"),
    }


# Mapeo: promo_id -> funcion constructora
_BUILDERS: dict[str, callable] = {
    "marzo_75": lambda: _build_portabilidad_promo(0),
    "marzo_80": lambda: _build_portabilidad_promo(1),
    "marzo_85": lambda: _build_portabilidad_promo(2),
    "fibra": _build_fibra_promo,
    "bundle_fibra_portabilidad": _build_bundle_promo,
}


def load_promo(promo_id: str) -> dict:
    """Carga y cachea una promo por su id."""
    if promo_id in _cache:
        return _cache[promo_id]
    builder = _BUILDERS.get(promo_id)
    if not builder:
        return {}
    data = builder()
    _cache[promo_id] = data
    return data


def list_promos() -> list[dict]:
    """Retorna lista de promos de portabilidad para el dropdown."""
    return [
        {"id": "marzo_75", "label": "Marzo 75%"},
        {"id": "marzo_80", "label": "Marzo 80%"},
        {"id": "marzo_85", "label": "Marzo 85%"},
    ]
