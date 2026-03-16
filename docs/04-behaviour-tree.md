# Behaviour Tree

**Archivos:** `src/behaviour_tree/engine.py`, `conditions.py`, `actions.py`, `decorators.py`, `status.py`

## Concepto

El Behaviour Tree (BT) es el **cerebro tactico** del agente. Dado el estado actual del Blackboard, decide que tactica usar para la respuesta. Esta codificado en Python puro (no XML) para ser testeable y debuggeable.

## Clases Base (`engine.py`)

| Clase | Comportamiento |
|---|---|
| `Selector` (Fallback) | Ejecuta hijos en orden hasta que uno retorne SUCCESS |
| `Sequence` | Ejecuta hijos en orden; falla si alguno falla |
| `Condition` | Evalua una funcion booleana del blackboard |
| `Action` | Ejecuta una accion que escribe `tactic` y `bt_action_id` en el blackboard |
| `Decorator` | Gate condicional: si la funcion retorna True, ejecuta el hijo |

Cada nodo tiene un `node_id` y `label` para el sistema de tracing.

## Status

```python
class Status(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RUNNING = "RUNNING"  # No usado actualmente
```

## Estructura del Arbol

```
Selector (Root)
├── Sequence (Camino Feliz)
│   ├── Condition: estado_I
│   └── Decorator: confianza_70
│       └── Action: avanzar_fase
│
├── Sequence (Ambiguedad)
│   ├── Condition: estado_IND
│   └── Action: pedir_confirmacion
│
├── Sequence (Objeciones)
│   ├── Condition: estado_NI
│   └── Selector (Tipo Objecion)
│       ├── Sequence (Obj Precio)
│       │   ├── Condition: sub_precio
│       │   └── Decorator: max_intentos
│       │       └── Selector (Tacticas)
│       │           ├── Decorator: max1 → Action: reencuadrar_valor
│       │           ├── Decorator: max1 → Action: mostrar_roi
│       │           ├── Decorator: max1 → Action: caso_exito
│       │           └── Action: prueba_piloto
│       │
│       ├── Sequence (Obj Tiempo)
│       │   ├── Condition: sub_tiempo
│       │   └── Decorator: max_intentos
│       │       └── Selector (Tacticas)
│       │           ├── Decorator: max1 → Action: inicio_minimo
│       │           ├── Decorator: max1 → Action: fecha_flexible
│       │           └── Action: urgencia
│       │
│       ├── Sequence (Obj Necesidad)
│       │   ├── Condition: sub_necesidad
│       │   └── Decorator: max_intentos
│       │       └── Selector (Tacticas)
│       │           ├── Decorator: max1 → Action: revelar_pain_point
│       │           └── Action: pain_point_oculto
│       │
│       ├── Sequence (Obj Autoridad)
│       │   ├── Condition: sub_autoridad
│       │   └── Selector (Tacticas)
│       │       ├── Decorator: max1 → Action: redirigir_decisor
│       │       └── Action: agendar_llamada
│       │
│       └── Sequence (Rechazo Duro)
│           ├── Condition: sub_rechazo_duro
│           └── Action: rechazo_duro_fin
│
└── Action: fallback_fin
```

## Condiciones (`conditions.py`)

9 funciones que leen el Blackboard y retornan `bool`:

| Condicion | Lee | True cuando |
|---|---|---|
| `estado_I` | `current_state` | Cliente con interes |
| `estado_NI` | `current_state` | Cliente objeta |
| `estado_IND` | `current_state` | Mensaje ambiguo |
| `subestado_precio` | `sub_state` | Objecion de precio |
| `subestado_tiempo` | `sub_state` | Objecion de timing |
| `subestado_necesidad` | `sub_state` | No ve la necesidad |
| `subestado_autoridad` | `sub_state` | No es quien decide |
| `subestado_rechazo_duro` | `sub_state` | Rechazo explicito |

## Acciones (`actions.py`)

Cada accion escribe `tactic` y `bt_action_id` en el Blackboard. Las acciones de objecion usan `_set_tactic()` que chequea `used_arguments` para **no repetir tacticas** (regla Cardone).

| Accion | Tactica | Descripcion |
|---|---|---|
| `avanzar_fase` | `avanzar_fase` | Continua naturalmente (camino feliz) |
| `pedir_confirmacion` | `pedir_confirmacion` | Reformula pregunta (IND) |
| `reencuadrar_valor` | `reencuadrar_valor` | Reencuadra precio como valor |
| `mostrar_roi` | `mostrar_roi` | Demuestra retorno con numeros |
| `caso_exito` | `caso_exito` | Ejemplo de cliente similar |
| `prueba_piloto` | `prueba_piloto` | Prueba con riesgo minimo |
| `inicio_minimo` | `inicio_minimo` | Reduce friccion de timing |
| `fecha_flexible` | `fecha_flexible` | Flexibilidad en fechas |
| `urgencia` | `urgencia` | Urgencia genuina (no falsa) |
| `revelar_pain_point` | `revelar_pain_point` | Revela problema oculto |
| `pain_point_oculto` | `pain_point_oculto` | Escenario concreto de problema |
| `redirigir_decisor` | `redirigir_decisor` | Pide datos del decisor |
| `agendar_llamada` | `agendar_llamada` | Propone llamada con decisor |
| `rechazo_duro_fin` | `rechazo_duro_fin` | Despedida profesional + HANDOFF |
| `fallback_fin` | `fallback_fin` | Pregunta abierta (fallback) |

Si una tactica ya esta en `used_arguments`, `_set_tactic()` retorna `FAILURE` y el Selector prueba la siguiente.

## Decoradores (`decorators.py`)

| Decorador | Logica |
|---|---|
| `confianza_70` | Pasa si `confidence >= 0.70` |
| `confianza_75` | Pasa si `confidence >= 0.75` |
| `slots_completos` | Pasa si hay `pain_point` y `customer_name` |
| `max_1_consecutivo` | Siempre True (la no-repeticion se maneja en `_set_tactic`) |
| `max_intentos_dinamico` | Limita intentos de objecion segun profundidad del arbol |

### `max_intentos_dinamico`

| Profundidad del arbol | Max intentos de objecion |
|---|---|
| < 6 turnos | 4 intentos |
| 6-12 turnos | 3 intentos |
| > 12 turnos | 2 intentos |

## Sistema de Tracing

Cada nodo registra su visita en `bb["bt_trace"]` con:
```json
{"id": "c_I", "type": "condition", "label": "estado_I", "status": "FAILURE"}
```

El trace se resetea en cada tick y se envia al frontend para visualizar el camino recorrido.

### Ejemplo de trace (objecion de precio)

```
[FAIL] condition   estado_I          ← No es I, falla
[FAIL] sequence    Camino Feliz      ← Hijo fallo, falla
[FAIL] condition   estado_IND        ← No es IND, falla
[FAIL] sequence    Ambiguedad        ← Hijo fallo, falla
[OK  ] condition   estado_NI         ← Es NI, pasa
[OK  ] condition   sub_precio        ← Es precio, pasa
[OK  ] action      reencuadrar_valor ← Primera tactica no usada
[OK  ] decorator   max1              ← Pasa
[OK  ] selector    Tacticas          ← Hijo exitoso
[OK  ] decorator   max_intentos      ← Dentro del limite
[OK  ] sequence    Obj Precio        ← Todos los hijos OK
[OK  ] selector    Tipo Objecion     ← Hijo exitoso
[OK  ] sequence    Objeciones        ← Todos OK
[OK  ] selector    Root              ← Exito
```
