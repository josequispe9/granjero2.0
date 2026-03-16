# Frontend

**Archivo:** `frontend/index.html`

## Arquitectura

Aplicacion single-page en HTML/CSS/JS vanilla, servida por nginx en el puerto 3000. No usa frameworks. Se comunica con la API en `localhost:8000`.

## Layout

Tres paneles horizontales:

```
[BT Panel 380px] [Chat 380px] [Blackboard 240px]
```

### Panel Izquierdo: Behaviour Tree
Visualizacion del arbol de comportamiento completo con el camino recorrido en la ultima respuesta.

- **Fondo oscuro** estilo terminal
- Arbol renderizado como texto indentado con conectores Unicode (`├─`, `└─`)
- Iconos por tipo de nodo: `?` Selector, `→` Sequence, `◆` Condition, `◔` Decorator, `►` Action
- **Colores por tipo:** azul (Selector), verde (Sequence), amarillo (Condition), violeta (Decorator), cyan (Action)
- **Nodos no visitados:** gris tenue
- **Nodos visitados con SUCCESS:** verde brillante con glow
- **Nodos visitados con FAILURE:** rojo atenuado
- **Accion final seleccionada:** fondo verde resaltado
- Cada nodo muestra status `OK` o `FAIL` a la derecha
- Leyenda de colores en la parte inferior

### Panel Central: Chat
- Modal de inicio pidiendo nombre del cliente
- Header azul con nombre del agente y boton "+ Nueva"
- Burbujas de chat (azul = usuario, gris = bot)
- Input con boton de enviar
- Mensajes de sistema en amarillo (ej: "Conversacion finalizada: PODA")
- Cuando la conversacion termina, se desactiva el input

### Panel Derecho: Blackboard
Muestra el estado actual del Blackboard con todos los campos relevantes:

- **Estado:** Badge verde (I), rojo (NI), o amarillo (IND)
- **Subestado:** Texto
- **Confianza:** Porcentaje
- **Fase Cardone:** Badge azul
- **Pain Point / Producto:** Texto
- **Tactica:** Texto de la tactica seleccionada por el BT
- **Objecion:** Tipo de objecion activa
- **NI Consecutivos:** Contador
- **Terminacion:** Badge negro o "activa"
- **Score / Injection:** Contadores
- **Binary Tree:** Cuadraditos verde (I) / rojo (NI) en fila
- **Metricas:** Turnos, I/NI, tasa de reversion
- **Args Usados:** Lista de tacticas ya utilizadas

## Flujo de Interaccion

### Inicio
1. Si hay `session_id` en localStorage → carga historial via `GET /conversation/{id}`
2. Si no → muestra modal de nombre

### Nueva Conversacion
1. Usuario ingresa nombre
2. Frontend llama `POST /start`
3. Muestra saludo hardcodeado
4. Actualiza Blackboard y BT (vacios)

### Enviar Mensaje
1. Agrega burbuja de usuario
2. Muestra "Escribiendo..."
3. Llama `POST /chat`
4. Reemplaza typing por respuesta
5. Actualiza panel Blackboard con `data.state`
6. Re-renderiza BT con `data.state.bt_trace`
7. Si `termination` no es null, muestra mensaje de sistema y desactiva input

### Renderizado del BT (`renderBTTree`)
La estructura del arbol esta definida como constante JS (`BT_TREE`) que replica exactamente la estructura Python de `engine.py`. Para cada respuesta:

1. Se construye un mapa `traceMap` de `node_id → status` desde `bt_trace`
2. Se recorre el arbol recursivamente
3. Cada nodo se renderiza con su estado de visita:
   - No visitado → gris
   - Visitado SUCCESS → verde
   - Visitado FAILURE → rojo
   - Accion final → resaltado

## Persistencia Local
- `session_id` y `customer_name` en `localStorage`
- Boton "+ Nueva" limpia localStorage y recarga
