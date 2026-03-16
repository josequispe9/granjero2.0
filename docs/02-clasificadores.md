# Clasificadores

**Archivos:** `src/classifiers/unified_classifier.py`, `src/classifiers/phase_classifier.py`

## Clasificador Unificado (`unified_classifier.py`)

Una **unica llamada a Haiku** que realiza 3 analisis simultaneos. Se unifico para respetar el rate limit de 5 req/min (antes eran 3 llamadas paralelas).

### Input
- Ultimos 6 mensajes de la conversacion
- Contexto actual: pain_point, product_interested, customer_name

### Output (JSON)
```json
{
  "estado": "I",
  "subestado": "descubrimiento",
  "confianza": 0.95,
  "injection": false,
  "pain_point": "internet lento",
  "product_interested": null,
  "customer_name": null
}
```

### Los 3 analisis en una sola llamada:

**1. Estado Conversacional**
Clasifica el ultimo mensaje del cliente en:
- **I (Interes):** El cliente muestra interes, hace preguntas, responde positivamente
- **NI (No Interes):** El cliente objeta o rechaza
- **IND (Indeterminado):** Mensaje ambiguo, monosilabo, emoji sin contexto

La `confianza` es un float 0.0-1.0. Si es menor a 0.6, se fuerza `IND` automaticamente.

**2. Deteccion de Prompt Injection**
Detecta si el mensaje intenta:
- Cambiar el rol del agente
- Extraer informacion del sistema
- Inyectar instrucciones

Si `injection: true`, se incrementa el contador `prompt_injection_attempts`. Con 3 intentos se dispara `HANDOFF`.

**3. Revision de Perfil**
Extrae informacion nueva del cliente:
- `pain_point`: problema mencionado (ej: "se me corta internet")
- `product_interested`: producto especifico mencionado
- `customer_name`: nombre si el cliente lo dice

Solo se actualizan los campos cuando el clasificador devuelve un valor no-null.

### Reglas de Clasificacion

| Mensaje del cliente | Estado | Subestado |
|---|---|---|
| "No me interesa" / "Dejame en paz" | NI | rechazo_duro |
| "Es muy caro" / "No tengo presupuesto" | NI | precio |
| "No es el momento" / "Ahora no puedo" | NI | tiempo |
| "No lo necesito" / "Ya tengo" | NI | necesidad |
| "Tengo que consultarlo" | NI | autoridad |
| Preguntas sobre el producto | I | segun fase |
| "ok" / "jaja" / emojis | IND | ambiguo |

## Clasificador de Fase (`phase_classifier.py`)

Logica **pura Python** (sin LLM) que evalua si la fase Cardone debe avanzar. Se ejecuta despues del clasificador unificado.

### Regla fundamental
**NI nunca avanza fase.** El cliente debe resolver su objecion y volver a I antes de que la fase avance.

### Condiciones de avance

| Transicion | Condicion |
|---|---|
| saludo → descubrimiento | Cliente responde con estado I (cualquier respuesta sin rechazo) |
| descubrimiento → eleccion | Se identifico al menos 1 `pain_point` |
| eleccion → oferta | Cliente en estado I con subestado `eleccion` (preguntas de implementacion) |
| oferta → conclusion | Cliente en estado I con subestado `oferta` (no rechaza la oferta) |

### Las 5 Fases Cardone

1. **Saludo:** Establecer rapport, tomar control. Agente inicia con mensaje hardcodeado.
2. **Descubrimiento:** Preguntas estrategicas para encontrar el pain point. Loop hasta descubrir uno.
3. **Eleccion:** Agente recomienda el producto ideal basado en el perfil. Solo aspectos relevantes.
4. **Oferta:** Oferta concreta con precio, fecha y condiciones. Se presenta con conviccion.
5. **Conclusion:** Cierre directo. "Arrancamos esta semana o la proxima?"

## Consumo de API

| Accion | Llamadas LLM |
|---|---|
| `POST /start` | 0 (saludo hardcodeado) |
| `POST /chat` | 2 (1 clasificador + 1 generator) |

Con un rate limit de 5 req/min, se pueden enviar **2 mensajes por minuto**.
