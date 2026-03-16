# Binary Tree

**Archivos:** `src/binary_tree/tree.py`, `src/binary_tree/metrics.py`

## Concepto

El Binary Tree es un modelo mental de la evolucion de la conversacion. Cada mensaje del cliente se clasifica como **I** (interes) o **NI** (no interes) y se agrega como un nodo a una lista secuencial.

**IND (indeterminado) es transicional y NO se agrega al arbol.** Es un estado temporario que dispara "pedir confirmacion" y se resuelve en el siguiente turno.

## Estructura de Datos

El arbol es una **lista plana** (no una estructura de arbol en memoria). Cada nodo es un dict:

```python
{"state": "I", "sub_state": "descubrimiento", "turn": 1}
{"state": "NI", "sub_state": "precio", "turn": 2}
{"state": "I", "sub_state": "descubrimiento", "turn": 3}
```

Esta representacion es suficiente para todas las metricas y facil de serializar a MongoDB.

## Funciones (`tree.py`)

### `append_node(tree, state, sub_state) -> list`
Agrega un nodo al arbol. Si `state == "IND"`, retorna el arbol sin cambios.

### `get_consecutive_ni(tree) -> int`
Cuenta NI consecutivos desde el final del arbol. Se usa para la condicion de PODA (3 NI consecutivos = fin de conversacion).

### `should_prune(tree, threshold=3) -> bool`
Retorna `True` si hay >= 3 NI consecutivos al final. Indica que el cliente no va a comprar.

### `get_path_signature(tree) -> str`
Genera una firma del camino: `"I-I-NI-I-NI-NI-NI"`. Util para analisis de patrones.

## Metricas (`metrics.py`)

### `compute_metrics(tree) -> dict`

Retorna:

| Metrica | Descripcion | Importancia |
|---|---|---|
| `total_turns` | Cantidad total de turnos | Profundidad de la conversacion |
| `i_count` | Cantidad de nodos I | Turnos con interes |
| `ni_count` | Cantidad de nodos NI | Turnos con objecion |
| `reversion_rate` | % de NI seguidos de I | **La mas importante:** mide efectividad del agente |
| `depth` | Profundidad del arbol | Igual a total_turns |

### Tasa de Reversion (NI → I)

Es la metrica mas importante del sistema. Mide cuantas veces el agente logra convertir una objecion (NI) de vuelta a interes (I) en el turno siguiente.

```
Reversion rate = (NI seguidos de I) / total NI
```

- **Alta (> 0.5):** El agente maneja bien las objeciones
- **Baja (< 0.3):** Las tacticas no estan funcionando

## Patrones de Conversacion

| Patron | Interpretacion |
|---|---|
| `I-I-I-I-I` | Camino feliz, conversion rapida |
| `I-NI-I-NI-I` | Cliente indeciso o agente poco efectivo |
| `I-I-I-NI-I-I` | Objecion aislada, buena recuperacion |
| `NI-NI-NI` | PODA, cliente no va a comprar |
| `I-I-NI-I-NI-NI-NI` | Perdio impulso, termina en poda |

## Regla Clave

Los nodos NI **solo retornan al subestado I del que vinieron**. No retrogradan fases. Si el cliente estaba en `I(eleccion)` y objeta precio, al resolver la objecion vuelve a `I(eleccion)`, no a `I(descubrimiento)`.
