import re
import discord
from discord.ext import commands
from discord import app_commands
from utils.ai import ask_coach
from utils.rate_limit import puede_usar, get_uso
from utils.embeds import embed_error, embed_limite
from config import COLORS

REGLA_MAX_TOKENS = 500

# ── Glosario estático ─────────────────────────────────────────────────────────
# Términos fijos del juego que siempre tienen la misma definición.
# Clave: término en minúsculas (y variantes). Valor: texto del embed.

_GLOSARIO: dict[str, dict] = {
    "rush": {
        "titulo": "⚡ Rush",
        "texto": (
            "**Definición:** Una carta con Rush puede atacar el mismo turno que se juega, "
            "sin esperar al turno siguiente.\n\n"
            "**Regla normal:** Los personajes recién jugados están 'activos' pero no pueden "
            "atacar hasta el turno siguiente (porque para atacar se giran/descansan, "
            "y una carta recién jugada ya está en posición activa).\n\n"
            "**Con Rush:** La carta puede girar para atacar inmediatamente en el turno "
            "que entra al campo, ignorando esa restricción.\n\n"
            "**Ejemplo:** Jugás un personaje con Rush en tu turno 3 → ese mismo turno "
            "podés usarlo para atacar al líder o a un personaje descansado del rival."
        ),
    },
    "blocker": {
        "titulo": "🛡️ Blocker",
        "texto": (
            "**Definición:** Una carta con Blocker puede interceptar un ataque dirigido "
            "al Líder durante el turno del rival.\n\n"
            "**Cómo funciona:** Cuando el rival declara un ataque a tu Líder, podés activar "
            "el Blocker girando (descansando) el personaje con esa habilidad. El ataque "
            "se redirige al Blocker en vez de a tu Líder.\n\n"
            "**Importante:**\n"
            "- Solo se puede bloquear ataques al **Líder**, no a otros personajes.\n"
            "- El Blocker debe estar **activo** (no descansado) para poder usarse.\n"
            "- Podés usar múltiples Blockers en el mismo ataque (cada uno gira).\n\n"
            "**Ejemplo:** Tu rival ataca tu Líder con un personaje de 6000 poder. "
            "Girás tu Blocker de 5000 y el ataque va al Blocker, que queda descansado."
        ),
    },
    "counter": {
        "titulo": "🛡️ Counter",
        "texto": (
            "**Definición:** El valor Counter de una carta indica cuánto poder adicional "
            "podés sumar a una carta en defensa durante el turno del rival.\n\n"
            "**Cómo funciona:** Cuando el rival te ataca, podés revelar una o más cartas "
            "de tu mano que tengan valor Counter. Cada una suma su valor (1000 o 2000) "
            "al poder de la carta defensora (Líder o personaje) solo para ese ataque.\n\n"
            "**Reglas clave:**\n"
            "- Solo se puede usar en el turno del **rival**, nunca en el tuyo.\n"
            "- Las cartas usadas como Counter van al **trash** (descarte).\n"
            "- Podés usar múltiples cartas Counter en el mismo ataque.\n"
            "- Solo cartas del color del Líder (o sin restricción de color) pueden usarse.\n\n"
            "**Ejemplo:** Tu Líder tiene 5000 poder y recibe un ataque de 7000. "
            "Descartás una carta con Counter 2000 → tu Líder sube a 7000 → empate → "
            "el ataque **no conecta** (necesitás >= para que conecte)."
        ),
    },
    "trigger": {
        "titulo": "✨ Trigger",
        "texto": (
            "**Definición:** Una carta con Trigger tiene un efecto que se activa "
            "**gratis** cuando esa carta es revelada como daño de vida.\n\n"
            "**Cómo funciona:** Cuando el rival te hace daño en el Líder y conecta, "
            "revelás la carta superior de tu mazo de vida. Si esa carta tiene Trigger, "
            "podés activar su efecto sin pagar ningún costo.\n\n"
            "**Ejemplos de efectos Trigger comunes:**\n"
            "- Agregar la carta a tu mano.\n"
            "- Poner en juego un personaje de costo bajo.\n"
            "- Agregar un DON!! extra.\n"
            "- Dar +2000 poder a una carta tuya.\n\n"
            "**Importante:** El Trigger es opcional — podés elegir no activarlo. "
            "La carta revelada se puede agregar a la mano (dependiendo del efecto)."
        ),
    },
    "don": {
        "titulo": "💰 DON!!",
        "texto": (
            "**Definición:** El DON!! es el recurso principal para jugar cartas y "
            "potenciar atacantes. Tenés un mazo separado de **10 cartas DON!!**.\n\n"
            "**Cómo funciona cada turno:**\n"
            "1. En tu DON!! Phase robás **2 cartas DON!!** de tu mazo DON!! "
            "(solo 1 en el primer turno del primer jugador).\n"
            "2. Esas cartas DON!! quedan activas y podés usarlas para pagar costos "
            "o adjuntarlas a cartas.\n\n"
            "**Usos del DON!!:**\n"
            "- **Pagar costo:** Girás (descansás) DON!! para jugar cartas. "
            "Un personaje de costo 3 requiere girar 3 DON!!.\n"
            "- **Adjuntar (attach):** Adjuntás 1 DON!! a una carta activa para darle "
            "+1000 de poder hasta el fin de tu turno. Podés adjuntar varios.\n\n"
            "**Al final del turno:** Todos los DON!! adjuntos vuelven a tu área DON!! "
            "y se activan al inicio de tu siguiente turno (Refresh Phase)."
        ),
    },
    "on play": {
        "titulo": "🎴 On Play",
        "texto": (
            "**Definición:** Efecto que se activa en el momento en que la carta "
            "entra al campo de juego.\n\n"
            "**Cuándo se activa:** Exactamente cuando jugás la carta pagando su costo "
            "(o poniéndola en juego por otro efecto). El efecto ocurre antes de que el "
            "rival pueda responder.\n\n"
            "**Importante:** Si la carta es devuelta a la mano antes de que el efecto "
            "resuelva (muy raro), el efecto se cancela. Generalmente los On Play "
            "son instantáneos e inevitables.\n\n"
            "**Ejemplo:** Un personaje con 'On Play: dale -2 al costo de una carta rival' "
            "aplica ese efecto en el momento en que lo jugás."
        ),
    },
    "when attacking": {
        "titulo": "⚔️ When Attacking",
        "texto": (
            "**Definición:** Efecto que se activa cuando la carta declara un ataque.\n\n"
            "**Cuándo se activa:** Al inicio de la declaración de ataque, antes de que "
            "el rival pueda contraatacar o usar Counter.\n\n"
            "**Frecuencia:** Se puede activar **una vez por ataque**. Si la carta ataca "
            "varias veces en un turno (por efectos especiales), se activa cada vez.\n\n"
            "**Ejemplo:** Una carta con 'When Attacking: robá 1 carta' te da una carta "
            "cada vez que esa carta ataca durante tu turno."
        ),
    },
    "activate": {
        "titulo": "🔄 Activate:Main",
        "texto": (
            "**Definición:** Efecto que podés activar voluntariamente durante tu "
            "Main Phase, generalmente girando la carta o pagando un costo.\n\n"
            "**Cómo funciona:** Ves el costo del efecto (ej: 'Activate:Main [Girar esta carta]'). "
            "Durante tu Main Phase podés girarlo para activar el efecto.\n\n"
            "**Una vez por turno:** La mayoría de los efectos Activate:Main solo se pueden "
            "usar una vez por turno por carta.\n\n"
            "**Importante:** La carta debe estar **activa** (no girada) para poder activar "
            "su efecto. Una vez que la girás para el efecto, no puede atacar ese turno."
        ),
    },
    "life": {
        "titulo": "❤️ Life (Vida)",
        "texto": (
            "**Definición:** Al inicio de la partida, cada jugador tiene "
            "**5 cartas de vida** (face-down en su zona de vida).\n\n"
            "**Cómo funciona el daño:** Cuando tu Líder recibe un ataque exitoso "
            "(poder atacante >= poder defensor sin counter), revelás la carta superior "
            "de tu pila de vida. Si tiene Trigger, podés activarlo.\n\n"
            "**Condición de victoria:** Si tu rival tiene **0 cartas de vida** y recibe "
            "cualquier daño → **pierde la partida**.\n\n"
            "**Mulligan:** Al inicio puedes ver tus cartas de vida (sin mostrar al rival) "
            "y reemplazar hasta 5 cartas entre tu mano y tu vida (barajando).\n\n"
            "**Importante:** Las cartas de vida se revelan solo cuando recibís daño, "
            "no puedes verlas libremente durante la partida."
        ),
    },
}

# Alias y variantes de términos
_ALIASES: dict[str, str] = {
    "vida": "life",
    "vidas": "life",
    "don": "don",
    "don!!": "don",
    "mazo don": "don",
    "rush": "rush",
    "blocker": "blocker",
    "bloquear": "blocker",
    "bloqueo": "blocker",
    "counter": "counter",
    "contrarrestar": "counter",
    "trigger": "trigger",
    "disparador": "trigger",
    "on play": "on play",
    "al jugar": "on play",
    "when attacking": "when attacking",
    "al atacar": "when attacking",
    "activate": "activate",
    "activate:main": "activate",
    "activar": "activate",
}

# Términos para el autocomplete
_TERMINOS_AUTOCOMPLETE = [
    "Rush", "Blocker", "Counter", "Trigger", "DON!!",
    "On Play", "When Attacking", "Activate:Main", "Life (Vida)",
]


def _buscar_en_glosario(pregunta: str) -> dict | None:
    """
    Busca la pregunta en el glosario estático.
    Retorna la entrada del glosario si es una coincidencia clara, None si no.
    """
    p = pregunta.lower().strip().rstrip("?").strip()

    # Coincidencia exacta con alias
    if p in _ALIASES:
        return _GLOSARIO.get(_ALIASES[p])

    # Coincidencia exacta con clave del glosario
    if p in _GLOSARIO:
        return _GLOSARIO[p]

    # La pregunta ES solo el nombre del término (una sola palabra o término corto)
    # Ej: "rush?", "¿qué es blocker?", "cómo funciona el don!!"
    for alias, clave in _ALIASES.items():
        # Si el alias aparece en la pregunta Y la pregunta es corta (≤6 palabras)
        if alias in p and len(p.split()) <= 6:
            return _GLOSARIO.get(clave)

    return None


# ── Cog ───────────────────────────────────────────────────────────────────────

class Regla(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _autocomplete_pregunta(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        current_lower = current.lower()
        matches = [
            term for term in _TERMINOS_AUTOCOMPLETE
            if current_lower in term.lower()
        ]
        return [
            app_commands.Choice(name=term, value=term)
            for term in matches[:25]
        ]

    @app_commands.command(
        name="regla",
        description="📖 Consultar una regla o mecánica de One Piece TCG — sin límite de uso",
    )
    @app_commands.describe(
        pregunta="Término del glosario (Rush, Blocker...) o pregunta específica de reglas"
    )
    @app_commands.autocomplete(pregunta=_autocomplete_pregunta)
    async def regla(self, interaction: discord.Interaction, pregunta: str) -> None:
        # 1. Glosario estático (0 tokens, instantáneo)
        entrada = _buscar_en_glosario(pregunta)
        if entrada:
            embed = discord.Embed(
                title=entrada["titulo"],
                description=entrada["texto"],
                color=COLORS["coach"],
            )
            embed.set_footer(text="📖 Glosario estático | Sin límite de uso")
            await interaction.response.send_message(embed=embed)
            return

        # 2. IA para preguntas complejas — verificar rate limit
        if not puede_usar(interaction.user.id, "regla"):
            await interaction.response.send_message(
                embed=embed_limite(), ephemeral=True
            )
            return

        await interaction.response.defer()

        prompt = (
            f"Explicá esta regla o mecánica de One Piece TCG:\n"
            f"{pregunta}\n\n"
            "Respondé con este formato:\n\n"
            "**Regla:** [explicación clara en 2-3 oraciones]\n\n"
            "**Ejemplo práctico:** [situación de juego concreta paso a paso]\n\n"
            "**Aclaración frecuente:** [el error o confusión más común]\n\n"
            "No uses headers ## ni tablas markdown."
        )

        try:
            respuesta = await ask_coach(prompt, max_tokens=REGLA_MAX_TOKENS)
        except Exception as e:
            await interaction.followup.send(
                embed=embed_error("Error al consultar la IA", str(e)), ephemeral=True
            )
            return

        embed = discord.Embed(
            title="📖 Reglas — TCG Sensei",
            description=respuesta,
            color=COLORS["coach"],
        )
        embed.set_footer(
            text="📖 Sin límite de uso | Glosario disponible: Rush, Blocker, Counter, Trigger, DON!!, On Play..."
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Regla(bot))
