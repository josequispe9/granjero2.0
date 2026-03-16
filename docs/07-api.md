# API y Endpoints

**Archivos:** `src/main.py`, `src/config.py`, `src/db.py`

## Configuracion (`config.py`)

```python
haiku = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=300)   # Clasificacion
sonnet = ChatAnthropic(model="claude-haiku-4-5-20251001", max_tokens=600)  # Generacion (temporal)
```

Ambos LLMs leen `ANTHROPIC_API_KEY` del `.env`. El model de generacion esta configurado como Haiku temporalmente por limitaciones de la API key. Cuando se tenga acceso a Sonnet, se descomenta la linea correspondiente.

MongoDB se conecta via `motor` (async) usando `MONGODB_URI` y `MONGODB_DB_NAME` del `.env`.

## Persistencia (`db.py`)

### `load_session(session_id) -> dict | None`
Lee una sesion de MongoDB por `session_id`. Excluye `_id`.

### `save_session(session_id, state) -> None`
Guarda/actualiza la sesion con upsert. Agrega `updated_at` automaticamente y `created_at` solo en la primera insercion.

La coleccion es `chat_sessions`.

## Endpoints (`main.py`)

### `GET /health`
Health check simple. Retorna `{"status": "ok"}`.

### `GET /graph`
Retorna una imagen PNG del grafo LangGraph (generada por mermaid).

### `GET /conversation/{session_id}`
Retorna el estado completo de una sesion, incluyendo mensajes e historial del Blackboard.

### `POST /start`
Inicia una conversacion outbound. **El primer mensaje es hardcodeado** (no usa LLM, 0 requests API).

**Request:**
```json
{"customer_name": "Carlos"}
```

**Response:**
```json
{
  "response": "Hola Carlos! Soy Lucas de Movistar. Vi que estas en la zona...",
  "session_id": "uuid",
  "customer_name": "Carlos",
  "state": { /* blackboard completo sin messages */ }
}
```

El estado se inicializa con `current_state: "I"`, `cardone_phase: "saludo"`, `confidence: 1.0`.

### `POST /chat`
Procesa un mensaje del cliente a traves del grafo completo.

**Request:**
```json
{
  "message": "La verdad que anda bastante mal",
  "session_id": "uuid",
  "customer_name": "Carlos"  // opcional si ya existe sesion
}
```

**Flujo interno:**
1. Carga sesion de MongoDB (si existe)
2. Restaura el Blackboard desde el documento persistido
3. Agrega el mensaje del usuario al historial
4. Si la conversacion ya termino, retorna mensaje de finalizacion
5. Invoca el grafo LangGraph (5 nodos, 2 requests LLM)
6. Extrae respuesta del ultimo mensaje
7. Persiste el estado actualizado en MongoDB
8. Retorna respuesta + estado publico

**Response:**
```json
{
  "response": "Uh, que bajon. Y decime, que es lo que te molesta mas?",
  "session_id": "uuid",
  "customer_name": "Carlos",
  "state": {
    "current_state": "I",
    "sub_state": "descubrimiento",
    "confidence": 0.95,
    "cardone_phase": "descubrimiento",
    "pain_point": "internet con mal funcionamiento",
    "tactic": "avanzar_fase",
    "bt_trace": [ /* traza del BT */ ],
    "binary_tree": [{"state": "I", "sub_state": "descubrimiento", "turn": 1}],
    "metrics": {"total_turns": 1, "i_count": 1, "ni_count": 0, "reversion_rate": 0.0},
    ...
  }
}
```

## Estado Publico

`_public_state()` retorna todo el Blackboard excepto `messages` (para no duplicar data en el response). Los mensajes se envian por separado en el campo `response`.

## Docker

```yaml
# docker-compose.yml
services:
  api:
    build: .
    ports: ["8000:8000"]
    volumes: [./src:/app/src]  # Hot reload
  frontend:
    image: nginx:alpine
    ports: ["3000:80"]
    volumes: [./frontend:/usr/share/nginx/html:ro]
```

El Dockerfile usa `python:3.12-slim` con uvicorn y `--reload` para desarrollo.
