# Grafo LangGraph

**Archivo:** `src/graph.py`

## Concepto

El grafo orquesta los 5 nodos del sistema en secuencia lineal. Se ejecuta **una vez por mensaje** del cliente. No hay loops internos — la terminacion esta garantizada por construccion.

## Nodos

```
START → classify → update_tree → decide_action → generate → check_end → END
```

### 1. `classify` (async)
- Llama al clasificador unificado (1 request Haiku)
- Escribe: `current_state`, `sub_state`, `confidence`, `cardone_phase`, `pain_point`, `product_interested`, `customer_name`, `prompt_injection_attempts`, `objection`
- Tambien ejecuta el clasificador de fase (Python puro, sin LLM)

### 2. `update_tree` (sync)
- Agrega nodo al Binary Tree (IND se ignora)
- Calcula NI consecutivos
- Escribe: `binary_tree`, `consecutive_ni`

### 3. `decide_action` (sync)
- Ejecuta un tick del Behaviour Tree
- El BT recorre el arbol y selecciona la tactica optima
- Registra la tactica en `used_arguments` si no es trivial
- Escribe: `tactic`, `bt_action_id`, `bt_trace`, `used_arguments`, `termination` (si BT la setea)

### 4. `generate` (async)
- Compone system prompt (base + fase + tactica)
- Llama al LLM de generacion (1 request Sonnet/Haiku)
- Escribe: `messages` (agrega respuesta del asistente)

### 5. `check_end` (sync)
- Evalua condiciones de terminacion
- Escribe: `termination`, `bought`

## Compilacion

```python
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
```

## Llamadas LLM por Invocacion

| Nodo | LLM | Modelo |
|---|---|---|
| classify | Haiku | 1 request |
| update_tree | Ninguno | Python puro |
| decide_action | Ninguno | Python puro |
| generate | Sonnet/Haiku | 1 request |
| check_end | Ninguno | Python puro |

**Total: 2 requests LLM por mensaje del cliente.**

## Flujo de Datos

```
Blackboard (input)
    ↓
[classify] → current_state=NI, sub_state=precio, confidence=0.9, pain_point="internet lento"
    ↓
[update_tree] → binary_tree=[..., {state: NI, sub_state: precio, turn: 3}], consecutive_ni=1
    ↓
[decide_action] → tactic="reencuadrar_valor", bt_trace=[...14 nodos...], used_arguments=["reencuadrar_valor"]
    ↓
[generate] → messages += "Entiendo, es una inversion importante. Pero mira..."
    ↓
[check_end] → termination=None (conversacion continua)
    ↓
Blackboard (output) → se persiste en MongoDB
```
