# Reglas Oficiales — ONE PIECE Card Game
**Manual Oficial v1.11**
> Si hay alguna discrepancia entre este manual y el texto de una carta, el texto de la carta tiene prioridad.

---

## Sobre el Juego

ONE PIECE Card Game es un juego de cartas coleccionables en el que te enfrentás a tu oponente. Armás tu propia tripulación alrededor de una carta Líder y atacás la tripulación rival. El objetivo es reducir los Life del Líder rival a 0 para lograr la victoria.

---

## Tipos de Cartas

### Carta Líder (Leader Card)
La carta principal de tu mazo. Siempre empieza en juego boca arriba.

Campos de una carta Líder:
- **Poder (Power):** Fuerza de ataque del Líder. En combate, gana la carta con mayor poder.
- **Atributo (Attribute)**
- **Efectos (Effects):** Habilidades especiales del Líder.
- **Color (Color)**
- **Categoría (Card Category)**
- **Nombre (Card Name)**
- **Life:** Cantidad de cartas de vida con las que empieza.
- **Tipo (Type)**
- **Número de carta (Card Number)**
- **Rareza (Rarity)**
- **Símbolo de bloque (Block Symbol)**

---

### Carta Personaje (Character Card)
Se juegan en el área de personajes pagando su costo con DON!!

Campos:
- **Costo (Cost):** DON!! necesarios para jugarla en el campo.
- **Poder (Power):** Fuerza en combate.
- **Atributo (Attribute)**
- **Counter:** Aumento de poder que se puede activar durante el Counter Step.
- **Efectos (Effects):** Habilidades especiales.
- **Efecto Trigger:** Se activa cuando el Líder recibe daño y se agrega una carta a la mano desde el área de Life.
- **Color / Categoría / Nombre / Tipo / Número / Rareza / Símbolo de bloque**

---

### Carta Evento (Event Card)
Efecto de un solo uso. Se paga su costo y va al trash.

Campos:
- **Costo (Cost):** DON!! para activar el Evento.
- **Efectos (Effects):** Se resuelven al activar.
- **Efecto Trigger:** Se activa cuando el Líder recibe daño.
- **Color / Categoría / Nombre / Tipo / Número / Rareza / Símbolo de bloque**

> ⚠️ Los efectos **Trigger** NO se pueden activar desde la mano.

---

### Carta Stage (Stage Card)
Permanece en el campo con efectos continuos. Solo puede haber 1 en el campo a la vez.

Campos:
- **Costo (Cost):** DON!! para jugarla en el área de Stage.
- **Efectos (Effects):** Habilidades especiales de Stage.
- **Color / Categoría / Nombre / Tipo / Número / Rareza / Símbolo de bloque**

---

### Carta DON!! (DON!! Card)
Recurso principal del juego.

- Se usan para **pagar costos** de cartas (descansando DON!! activos del área de costos).
- También se pueden **dar** a cartas Personaje o Líder colocándolas debajo de esa carta.
- Cada carta DON!! adjunta otorga **+1000 de poder durante tu turno**.

---

## Áreas del Campo

| # | Área | Descripción |
|---|------|-------------|
| ① | **Área de Personajes** | Donde se colocan las cartas Personaje. Máximo 5. |
| ② | **Área del Líder** | La carta Líder siempre está boca arriba desde el inicio. |
| ③ | **Área de Stage** | Máximo 1 carta Stage a la vez. |
| ④ | **Mazo (Deck)** | El mazo principal de 50 cartas. |
| ⑤ | **Trash** | Personajes eliminados en combate y Eventos activados. |
| ⑥ | **Área de Costos** | Donde se colocan las cartas DON!! del mazo DON!! |
| ⑦ | **Mazo DON!!** | El mazo de 10 cartas DON!! |
| ⑧ | **Life** | Cartas boca abajo igual al valor de Life del Líder. Cuando el Líder recibe daño, se pierden cartas de aquí. Si recibe daño con 0 Life, ese jugador pierde. |

> El Área del Líder, Área de Personajes, Área de Stage y Área de Costos se denominan colectivamente **"el campo"**.

---

## Construcción del Mazo

Para jugar ONE PIECE Card Game se necesita:

- **1 carta Líder**
- **Mazo principal:** 50 cartas exactas (Personajes, Eventos y Stages)
  - Solo puede contener cartas del color del Líder.
  - Máximo 4 copias de una misma carta (mismo número).
- **Mazo DON!!:** 10 cartas DON!!

---

## Preparación del Juego

1. Mezclar el mazo y colocarlo en su área.
2. Colocar la carta Líder boca arriba en el Área del Líder.
3. Definir quién empieza con Piedra-Papel-Tijera. El ganador elige si empieza primero o segundo.
4. Robar 5 cartas del mazo.
5. Cada jugador puede optar por devolver **todas** las cartas de su mano al mazo, mezclar y robar 5 nuevamente (**una sola vez por partida**). El jugador que empieza primero decide primero.
6. Robar cartas iguales al valor de **Life** del Líder desde la cima del mazo, de a una, y colocarlas boca abajo en el Área de Life sin mirarlas. (La primera carta del mazo queda en el fondo del área de Life.)
7. ¡El jugador que empieza inicia su turno!

---

## Condiciones de Victoria

Ganás la partida si ocurre alguna de las siguientes condiciones:

- **Ganás un combate contra el Líder rival cuando este tiene 0 Life.**
- **El mazo del rival se reduce a 0 cartas.**
  - Si el mazo llega a 0 cartas, todos los efectos continuos se cancelan y ese jugador pierde.

---

## Estados: Activo y Descansado

- **Activo (Active):** La carta está erguida. Estado normal al jugar Personajes y Stages.
- **Descansado (Rested):** La carta está girada de lado (90°). Se descansa al atacar, bloquear, o pagar costos.

Volver una carta descansada a activa = **activarla**.
Girar una carta activa a descansada = **descansarla (restarla)**.

---

## Pagar Costos

Para jugar Personajes, Stages o activar Eventos, se paga el costo **descansando** la cantidad indicada de cartas DON!! **activas** del área de costos.

---

## Flujo del Turno

```
① Refresh Phase
② Draw Phase
③ DON!! Phase
④ Main Phase
⑤ End Phase
```

### ① Refresh Phase
- Activar (enderezar) **todas** las cartas descansadas propias.
- Devolver todas las cartas DON!! adjuntas a cartas al área de costos en estado **activo**.

### ② Draw Phase
- Robar **1 carta** del mazo.
- ⚠️ El jugador que empieza **NO roba** en su primer turno.

### ③ DON!! Phase
- Colocar **2 cartas DON!!** del mazo DON!! en el área de costos en estado activo.
- Si solo queda 1 carta en el mazo DON!!, colocar solo 1.
- ⚠️ El jugador que empieza solo coloca **1 DON!!** en su primer turno.

### ④ Main Phase
La fase principal. Se pueden realizar las acciones A, B, C y D en cualquier orden y tantas veces como sea posible.

**A — Jugar Cartas**
- Jugar Cartas Personaje
- Jugar Cartas Stage
- Activar Cartas Evento

**B — Activar Efectos de Cartas**
- Se pueden activar efectos de cartas Líder, Personaje, Evento y Stage.

**C — Dar Cartas DON!!**
- Se puede dar 1 carta DON!! activa del área de costos a una carta Líder o Personaje colocándola debajo de esa carta (visible).
- No hay límite de veces siempre que haya DON!! para dar.
- Cada DON!! adjunto otorga **+1000 de poder durante tu turno**.

**D — Batalla**
- Ver sección "Flujo de Batalla" abajo.

> ⚠️ Ningún jugador puede atacar en su primer turno.

La fase principal termina cuando el jugador declara su fin, pasando a la End Phase.

### ⑤ End Phase
El End Phase se resuelve en este orden:
1. Se activan y resuelven los efectos del jugador activo que se activan al final del turno.
2. Se activan y resuelven los efectos del oponente que se activan al final del turno.
3. Se cancelan los efectos del jugador activo restringidos a "durante este turno".
4. Se cancelan los efectos del oponente restringidos a "durante este turno".
5. El turno termina y empieza el turno del oponente.

---

## Flujo de Batalla

### ① Declaración de Ataque (Attack Declaration)
- Solo pueden atacar Líderes y Personajes del Área de Personajes.
- Para atacar: **descansar** (girar) la carta Líder o Personaje atacante y declarar el ataque.
- Elegir el objetivo del ataque:
  - El **Líder** del oponente, **o**
  - Un **Personaje descansado** en el Área de Personajes del oponente.
- En este punto se activan los efectos **[When Attacking]** y similares.

### ② Block Step
- El jugador atacado puede activar el efecto **[Blocker]** de uno de sus Personajes.
- El Blocker reemplaza al Líder o Personaje que estaba siendo atacado.

### ③ Counter Step
El jugador que está siendo atacado puede realizar las siguientes acciones en cualquier orden y tantas veces como quiera:

**a) Activar el efecto [Counter] de una carta Personaje:**
- Enviar al trash una carta Personaje con Counter desde la mano.
- El Líder o uno de los Personajes gana poder igual al valor de Counter indicado **durante este combate**.

**b) Jugar una carta Evento [Counter]:**
- Enviar al trash una carta Evento con Counter desde la mano para activar su efecto.

### ④ Damage Step
- Se compara el poder de la carta atacante y la carta defensora.
- **La carta atacante gana si su poder es mayor o igual al poder de la carta defendida.**

**Si el oponente ataca al Líder y gana:**
- El Líder recibe **1 daño** (se voltea la carta superior del área de Life).
- Si el Líder tiene **0 Life** y recibe daño → el jugador atacante **gana la partida**.

**Si el oponente ataca a un Personaje y gana:**
- El Personaje es **eliminado (KO'd)** y va al trash.

**Si el poder atacante es menor que el defensor:**
- El ataque falla. No ocurre nada. Se procede al ⑤.

#### Daño al Líder — detalle
Cuando tu Líder recibe daño:
- Revisás (sin mostrar al oponente) la carta superior de tu área de Life.
- Si esa carta tiene efecto **Trigger**, podés revelarla y activar el Trigger **en lugar de agregarla a tu mano**.
- También podés optar por **no activar** el Trigger. En ese caso, la carta va a tu mano sin revelarla.
- Si el Líder recibe 2 o más daños a la vez (por efectos como Double Attack), el proceso se repite por cada daño.

### ⑤ Fin del Combate
- El combate termina.
- Se activan los efectos que se activan al final del combate (si los hay).
- Todos los efectos que aplican "durante este combate" se cancelan.

---

## Jugar Cartas — Detalle

### Jugar Carta Personaje
1. Colocar la carta en el Área de Personajes en estado **activo**.
2. Pagar el costo descansando DON!! del área de costos.
3. La carta está en juego.

> Si ya tenés **5 Personajes** y querés jugar uno nuevo, podés hacerlo enviando uno de los Personajes existentes al **trash**.

### Jugar Carta Stage
1. Colocar la Stage en el Área de Stage en estado **activo**.
2. Pagar el costo.

> Si ya hay una Stage en el campo y querés jugar una nueva, enviás la existente al **trash**.

### Activar Carta Evento
1. Revelar la carta Evento de tu mano.
2. Pagar el costo de activación.
3. El efecto Main de la carta se activa.
4. La carta va al **trash**.

> Los efectos **Trigger** no pueden activarse desde la mano.

---

## Reglas Adicionales

### Orden de Activación de Efectos
- Si una carta tiene múltiples efectos que ocurren al mismo tiempo, el dueño de la carta decide el orden de activación.
- Si ambos jugadores tienen efectos que ocurren al mismo tiempo, **el jugador activo (cuyo turno es) activa primero**. Después de resolver todos los suyos, el otro jugador activa los propios.

### Cartas Multicolor
- Una carta puede tener más de un color.
- Las cartas multicolor se tratan como teniendo **todos** sus colores simultáneamente.
- Ejemplo: una carta Rojo/Verde se considera tanto Roja como Verde al mismo tiempo.

### DON!! al Dejar el Campo
Cuando un Personaje con cartas DON!! adjuntas deja el campo (por ser eliminado en combate o devuelto a la mano por un efecto):
- Las cartas DON!! adjuntas se devuelven al **área de costos** en estado **descansado**.

---

## Glosario de Palabras Clave

| Keyword | Descripción |
|---------|-------------|
| **On Play** | Efecto que se activa cuando jugás el Personaje en el campo. |
| **Activate:Main** | Efecto que se puede activar durante tu Main Phase. |
| **Your Turn** | Efecto que se activa durante tu turno. |
| **End of Your Turn** | Efecto que se activa durante la End Phase de tu turno. |
| **Main** | Efecto de carta Evento que se juega durante tu Main Phase. |
| **Counter** | Efecto de carta Evento que se juega durante el Counter Step del turno del oponente. |
| **Once Per Turn** | Efecto que solo se puede activar una vez por turno. |
| **DON!!×1 / DON!!×2** | Efecto que se activa cuando se dan 1 o más cartas DON!! al Personaje. El número indica cuántas DON!! se deben dar. |
| **① (costo de activación)** | Efecto que se activa descansando cartas DON!! del área de costos. El número indica cuántas. |
| **DON!!−1** | Efecto que se activa devolviendo una carta DON!! desde el campo (Líder, Personaje o área de costos) al mazo DON!!. Podés devolver DON!! adjuntos sin importar si están activos o descansados. |
| **Blocker** | Efecto que se activa durante el Block Step. La carta reemplaza al Líder o Personaje que estaba siendo atacado. |
| **Rush** | Permite al Personaje atacar en el mismo turno en que fue jugado. |
| **Double Attack** | Cuando este Personaje causa daño al Líder rival en un ataque, causa **2 daños** en vez de 1. |
| **Banish** | Cuando este Personaje causa daño al Líder rival, la carta de Life se **envía al trash** sin activar su efecto Trigger. |
| **Trigger** | Efecto que se puede activar cuando el Líder recibe daño y se agrega una carta al mano desde el área de Life. |

---

## Resumen Rápido — Estructura del Turno

```
REFRESH PHASE  → Activar todas las cartas descansadas + devolver DON!! adjuntos al área de costos (activos)
DRAW PHASE     → Robar 1 carta (el primer jugador NO roba en su primer turno)
DON!! PHASE    → Colocar 2 DON!! del mazo DON!! al área de costos (1 en el primer turno del primer jugador)
MAIN PHASE     → Jugar cartas / Activar efectos / Dar DON!! / Batallar (en cualquier orden)
END PHASE      → Resolver efectos de fin de turno → cancelar efectos temporales → pasar el turno
```

---

## Colores y Estrategias del Meta

Cada color tiene una identidad de juego definida:

| Color | Identidad | Estrategia típica |
|-------|-----------|-------------------|
| **Rojo** | Agresivo | Poder alto, Rush, presión constante, cerrar rápido |
| **Verde** | Combo / Ramp | DON!! extra, personajes con Rush, generar ventaja de recursos |
| **Azul** | Control | Devolver cartas a la mano rival, robar cartas, bloquear |
| **Púrpura** | Trash / Reanimate | Sinergias con el trash, KO por costo, manipulación de DON!! |
| **Negro** | Control agresivo | Reducir costo de cartas rivales, KO a costo 0, removal |
| **Amarillo** | Life / Defensa | Life manipulation, Trigger heavy, resistencia y control tardío |

Los mazos multicolor combinan estas identidades. Ejemplo: Red/Blue mezcla presión con control.

---

## Notas para el Coach

- Un mazo necesita al menos **14-18 cartas con Counter** para defenderse efectivamente.
- La **curva de DON!!** ideal: 10-15 cartas de costo 1-2, 14-18 de costo 3-4, 8-12 de costo 5+.
- **Double Attack** y **Banish** son keywords de alto impacto — Double Attack hace 2 daños al Líder en un ataque, Banish manda la carta de Life al trash sin Trigger.
- Solo se puede atacar a **Personajes descansados**, nunca a los activos.
- **Rush NO bypasea el Blocker**: Rush solo permite que el Personaje ataque el mismo turno que fue jugado. El flujo de batalla sigue siendo normal: después del Attack Declaration viene el Block Step, y el rival PUEDE usar Blocker para redirigir el ataque, incluso contra un atacante con Rush. Rush no tiene ninguna interacción con Blocker.
- El **Block Step** ocurre antes del Counter Step — si el rival usa Blocker, los counters se aplican al Blocker, no al Líder original.
- Un Personaje con Rush que ataca en el turno que fue jugado: queda descansado tras atacar, por lo que en el turno rival SÍ puede ser atacado.
