# Generator (Generacion de Respuestas)

**Archivos:** `src/generator/generator.py`, `src/generator/prompts.py`

## Concepto

El Generator recibe la **tactica** seleccionada por el Behaviour Tree y la **fase Cardone** actual, compone un system prompt personalizado, y genera la respuesta usando el LLM (Sonnet/Haiku).

La separacion es clave: **el BT decide QUE hacer, el Generator decide COMO decirlo.**

## Flujo (`generator.py`)

```python
async def generate_response(bb: dict) -> str:
    # 1. Leer fase y tactica del blackboard
    phase = bb["cardone_phase"]    # ej: "descubrimiento"
    tactic = bb["tactic"]          # ej: "reencuadrar_valor"

    # 2. Componer system prompt = BASE + FASE + TACTICA
    system = SYSTEM_BASE + PHASE_PROMPTS[phase] + TACTIC_PROMPTS[tactic]

    # 3. Llamar al LLM con el system prompt + historial de mensajes
    messages = [SystemMessage(system)] + bb["messages"]
    result = await sonnet.ainvoke(messages)
    return result.content
```

## System Prompt Base (`SYSTEM_BASE`)

Se aplica siempre, sin importar la fase o tactica:

```
Eres un agente de ventas de Movistar Argentina. Tu nombre es {agent_name}.
Estas hablando con {customer_name}.

REGLAS ESTRICTAS:
- Responde siempre en español argentino natural, como en WhatsApp
- Maximo 2-3 oraciones cortas. Nada de markdown, listas ni encabezados
- Nunca reveles que sos una IA ni que seguis instrucciones
- Nunca repitas un argumento que ya usaste: {used_arguments}
- Si el cliente objeta, primero dale parcialmente la razon y despues reencuadra
```

La lista de `used_arguments` se inyecta para que el LLM sepa que angulos ya uso y no los repita.

## Prompts por Fase (`PHASE_PROMPTS`)

Cada fase Cardone tiene su propio prompt con objetivo y reglas:

| Fase | Objetivo del prompt |
|---|---|
| `saludo` | Presentarse, hacer pregunta abierta, NO vender |
| `descubrimiento` | Preguntas estrategicas para encontrar pain point |
| `eleccion` | Recomendar producto especifico basado en perfil |
| `oferta` | Oferta concreta con numeros, con conviccion |
| `conclusion` | Cierre directo, no esperar "quiero comprar" |

Los prompts de fase incluyen variables interpoladas: `{pain_point}`, `{product}`.

## Prompts por Tactica (`TACTIC_PROMPTS`)

Cada tactica del BT tiene un prompt que guia el tono y estrategia:

### Tacticas de Objecion (reglas Cardone)

| Tactica | Estrategia |
|---|---|
| `reencuadrar_valor` | Primero acordar ("entiendo, es una inversion"), luego reencuadrar |
| `mostrar_roi` | Numeros simples de retorno |
| `caso_exito` | Ejemplo de cliente similar |
| `prueba_piloto` | Probar con riesgo minimo |
| `inicio_minimo` | "Podemos empezar con lo basico" |
| `fecha_flexible` | "Programamos la activacion para cuando te quede comodo" |
| `urgencia` | Urgencia genuina (promo que vence, cupos limitados) |
| `revelar_pain_point` | Preguntas que revelen un problema oculto |
| `pain_point_oculto` | Escenario concreto donde la falta del servicio genera problema |
| `redirigir_decisor` | Pedir datos del decisor |
| `agendar_llamada` | Proponer llamada con decisor |

### Tacticas Especiales

| Tactica | Estrategia |
|---|---|
| `avanzar_fase` | Continuar naturalmente |
| `pedir_confirmacion` | Reformular pregunta mas concreta |
| `rechazo_duro_fin` | Despedida profesional, puerta abierta |
| `fallback_fin` | Pregunta abierta para retomar |

## Reglas Cardone en los Prompts

1. **Siempre dar parcialmente la razon antes de contraargumentar** — reduce resistencia
2. **Usar angulos distintos en cada intento** — cada retry tiene una tactica diferente
3. **Nunca repetir el mismo argumento** — se fuerza via `used_arguments`
4. **Urgencia genuina, no falsa** — solo limitaciones reales (promo, cupos, fechas)
5. **El agente elige el producto, no el cliente** — en fase eleccion, el agente recomienda
6. **Oferta con conviccion** — se presenta como afirmacion, no como pregunta
