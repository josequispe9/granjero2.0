# Blackboard (Estado Compartido)

**Archivo:** `src/state.py`

El Blackboard es un `TypedDict` que actua como la memoria compartida entre todos los nodos del sistema. Es el puente entre el Binary Tree (input), el Behaviour Tree (decision) y el Generator (output).

## Campos

### Mensajes
| Campo | Tipo | Descripcion |
|---|---|---|
| `messages` | `list` | Historial de mensajes LangGraph (con `add_messages` reducer) |

### Clasificacion de Estado
| Campo | Tipo | Valores |
|---|---|---|
| `current_state` | `str` | `"I"` (interes), `"NI"` (no interes), `"IND"` (indeterminado) |
| `sub_state` | `str` | Subestado activo (ver tabla abajo) |
| `confidence` | `float` | Confianza del clasificador (0.0 - 1.0) |

**Subestados validos por estado:**

| Estado | Subestados |
|---|---|
| I (interes) | `saludo`, `descubrimiento`, `eleccion`, `oferta`, `conclusion` |
| NI (no interes) | `precio`, `tiempo`, `necesidad`, `autoridad`, `rechazo_duro` |
| IND (indeterminado) | `ambiguo` |

### Fase Cardone
| Campo | Tipo | Descripcion |
|---|---|---|
| `cardone_phase` | `str` | Fase actual: `saludo` → `descubrimiento` → `eleccion` → `oferta` → `conclusion` |

### Perfil del Cliente
| Campo | Tipo | Descripcion |
|---|---|---|
| `pain_point` | `str \| None` | Problema identificado del cliente |
| `product_interested` | `str \| None` | Producto en el que mostro interes |
| `customer_name` | `str` | Nombre del cliente |

### Binary Tree
| Campo | Tipo | Descripcion |
|---|---|---|
| `binary_tree` | `list[dict]` | Lista plana de nodos `{state, sub_state, turn}` |

### Objeciones
| Campo | Tipo | Descripcion |
|---|---|---|
| `objection` | `str \| None` | Tipo de objecion activa |
| `used_arguments` | `list[str]` | Tacticas ya usadas (para no repetir, regla Cardone) |
| `consecutive_ni` | `int` | NI consecutivos (3 = PODA) |
| `consecutive_ind` | `int` | IND consecutivos |

### Behaviour Tree Output
| Campo | Tipo | Descripcion |
|---|---|---|
| `tactic` | `str \| None` | Tactica seleccionada por el BT |
| `bt_action_id` | `str \| None` | ID de la accion BT ejecutada |
| `bt_trace` | `list[dict]` | Traza del ultimo tick `[{id, type, label, status}]` |

### Terminacion
| Campo | Tipo | Descripcion |
|---|---|---|
| `termination` | `str \| None` | `"CIERRE"`, `"PODA"`, o `"HANDOFF"` |
| `bought` | `bool` | Si el cliente compro |
| `score_conversation` | `str` | Score de conversion (NO_COMPRO..COMPRO) |

### Control
| Campo | Tipo | Descripcion |
|---|---|---|
| `take_human` | `bool` | Si se debe transferir a humano |
| `prompt_injection_attempts` | `int` | Intentos de injection detectados |
| `asleep` | `bool` | Cliente inactivo > 24h |
| `name` | `str` | Nombre del agente vendedor |

## Estado Inicial

Cuando se crea una nueva conversacion (`POST /start`), el Blackboard se inicializa con:

```python
{
    "current_state": "I",
    "sub_state": "saludo",
    "confidence": 1.0,
    "cardone_phase": "saludo",
    "binary_tree": [],
    "used_arguments": [],
    "consecutive_ni": 0,
    "termination": None,
    "bought": False,
    ...
}
```

## Flujo de Datos

```
classify       escribe → current_state, sub_state, confidence, cardone_phase, pain_point, ...
update_tree    escribe → binary_tree, consecutive_ni
decide_action  escribe → tactic, bt_action_id, bt_trace, used_arguments
generate       escribe → messages (agrega respuesta del asistente)
check_end      escribe → termination, bought
```

Cada nodo del grafo **lee** el Blackboard y **escribe** solo sus campos correspondientes. LangGraph mergea los updates automaticamente.
