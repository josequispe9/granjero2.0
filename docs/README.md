# Vendedor IA - Agente CBST

Sistema de ventas outbound basado en la metodologia de Grant Cardone, implementado como un agente autonomo que combina **Binary Tree**, **Behaviour Tree** y **Blackboard** (CBST) para tomar decisiones tacticas en cada turno de conversacion.

## Arquitectura General

```
[Mensaje del cliente]
        |
  classify          Haiku clasifica estado + injection + perfil (1 llamada)
        |
  update_tree        Agrega nodo al Binary Tree
        |
  decide_action      Behaviour Tree selecciona tactica
        |
  generate           Haiku/Sonnet genera respuesta con tactica + fase
        |
  check_end          Evalua CIERRE / PODA / HANDOFF
        |
    END
```

Cada mensaje del cliente dispara **una sola invocacion** del grafo LangGraph (5 nodos secuenciales). No hay loops internos: la terminacion esta garantizada por construccion.

## Stack Tecnologico

| Componente | Tecnologia |
|---|---|
| Backend | FastAPI (Python) |
| Orquestacion | LangGraph |
| Clasificacion | Claude Haiku 4.5 |
| Generacion | Claude Haiku 4.5 (temporalmente; diseñado para Sonnet) |
| Base de datos | MongoDB Atlas (motor async) |
| Trazabilidad | LangSmith |
| Frontend | HTML/CSS/JS vanilla (servido por nginx) |
| Deploy | Docker Compose |

## Estructura de Archivos

```
src/
  main.py                     API FastAPI (endpoints slim)
  config.py                   LLMs y MongoDB
  state.py                    Blackboard (TypedDict)
  graph.py                    Grafo LangGraph (5 nodos)
  db.py                       Persistencia MongoDB
  termination.py              Logica de terminacion
  classifiers/
    unified_classifier.py     Clasificador unico (estado + injection + perfil)
    phase_classifier.py       Avance de fase Cardone
  binary_tree/
    tree.py                   Append, consecutive NI, pruning
    metrics.py                Tasa de reversion, conteos
  behaviour_tree/
    status.py                 Enum SUCCESS/FAILURE/RUNNING
    engine.py                 Motor BT + arbol completo
    conditions.py             9 condiciones (estado_I, sub_precio, etc.)
    actions.py                16 acciones (tacticas de venta)
    decorators.py             5 decoradores (confianza, max_intentos, etc.)
  generator/
    prompts.py                Prompts por fase y por tactica
    generator.py              Compone system prompt y llama al LLM
frontend/
  index.html                  Chat + Blackboard + visualizacion BT
docs/                         Esta documentacion
```

## Documentacion por Modulo

- [Blackboard (Estado)](./01-blackboard.md) - El estado compartido entre todos los componentes
- [Clasificadores](./02-clasificadores.md) - Como se interpreta cada mensaje del cliente
- [Binary Tree](./03-binary-tree.md) - Historial de estados y metricas de conversacion
- [Behaviour Tree](./04-behaviour-tree.md) - Motor de decisiones tacticas
- [Generator](./05-generator.md) - Generacion de respuestas con prompts Cardone
- [Grafo LangGraph](./06-grafo.md) - Orquestacion de los 5 nodos
- [API y Endpoints](./07-api.md) - FastAPI, persistencia y flujo HTTP
- [Frontend](./08-frontend.md) - Interfaz de chat y visualizacion del BT
- [Terminacion](./09-terminacion.md) - Condiciones de fin de conversacion

## Inicio Rapido

```bash
# Crear .env con ANTHROPIC_API_KEY, MONGODB_URI, etc.
docker-compose up --build
# Frontend: http://localhost:3000
# API: http://localhost:8000
# Health check: http://localhost:8000/health
```

## Flujo de una Conversacion

1. Frontend llama `POST /start` con nombre del cliente
2. Backend responde con saludo hardcodeado (sin LLM)
3. Cliente responde, frontend llama `POST /chat`
4. El grafo ejecuta 5 nodos secuenciales (2 llamadas LLM)
5. Se persiste el estado completo en MongoDB
6. Frontend muestra respuesta + actualiza Blackboard y BT visual
7. Repite desde paso 3 hasta terminacion (CIERRE/PODA/HANDOFF)
