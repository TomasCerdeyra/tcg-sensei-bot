import re
import discord
from discord.ext import commands
from discord import app_commands
from utils.ai import ask_coach
from utils.card_api import (
    buscar_carta_onepiece,
    buscar_cartas_por_color,
    buscar_lideres_por_nombre,
    autocomplete_lideres,
)
from utils.rate_limit import puede_usar, get_uso
from utils.logger import log_usage
from utils.embeds import embed_limite, embed_error
from config import COLORS, AI_MAX_TOKENS_DECK

# Suficiente para 50 cartas bien explicadas + estrategia
DECK_MAX_TOKENS = AI_MAX_TOKENS_DECK

# Reglas reales de deckbuilding de One Piece TCG inyectadas en cada prompt
_DECKBUILDING_RULES = """\
REGLAS OBLIGATORIAS de One Piece TCG (aplicá sin excepción):
- El mazo principal tiene EXACTAMENTE 50 cartas. El líder y el mazo Don!! son aparte y NO se cuentan.
- Máximo 4 copias del mismo número de carta.
- Solo cartas del color del líder elegido.
- ANTES de escribir el mazo, sumá las cantidades línea por línea y verificá que den 50 exactas. Si no dan 50, corregí.

CRITERIOS ESTRATÉGICOS que DEBÉS cumplir:
1. COUNTER (defensa): incluí 14-18 cartas con valor counter (ctr 1000 o 2000). Sin counters el mazo pierde.
2. CURVA DE COSTO (distribución para 50 cartas):
   - Costo 0-2: 12-16 cartas  → presión temprana + counters baratos
   - Costo 3-4: 14-18 cartas  → backbone del mazo
   - Costo 5+:   8-12 cartas  → finishers / impacto alto
3. RATIO de tipos:
   - 35-42 personajes (Characters)
   - 8-15 eventos (Events) y/o escenarios (Stages)
4. COPIAS por rol:
   - 4x: cartas CORE del win condition o engine de búsqueda
   - 3x: soporte importante
   - 2x: secundarias / opcionales
   - 1x: tech cards situacionales
5. KEYWORDS PRIORITARIOS:
   - Rush: ataca el mismo turno → priorizar en mazos agresivos
   - Blocker: protege al líder → priorizar en mazos control/midrange
   - Trigger: efecto gratis al recibir daño → incluir siempre que sea posible
6. El mazo debe ser COHERENTE: las cartas deben apoyarse mutuamente con un plan claro de win condition.
"""


def _contar_cartas(texto: str) -> int:
    """
    Cuenta el total de cartas sumando las cantidades en líneas con formato 'Nx Nombre'.
    Acepta variantes: '4x', '4X', '4 x', '(4)', '4 cartas'.
    """
    total = 0
    for m in re.finditer(r"^\s*(\d+)\s*[xX]", texto, re.MULTILINE):
        total += int(m.group(1))
    return total


def _extraer_colores(leader_cards: list[dict]) -> list[str]:
    """Extrae los colores del líder desde resultados del scraper (fallback)."""
    for card in leader_cards:
        if card.get("type", "").upper() == "LEADER" and card.get("color"):
            return [c.strip() for c in card["color"].split("/")]
    for card in leader_cards:
        if card.get("color"):
            return [c.strip() for c in card["color"].split("/")]
    return []


def _formatear_pool(cards: list[dict]) -> str:
    """Formatea el pool con todos los datos relevantes para deckbuilding."""
    lineas = []
    for c in cards:
        card_id = c.get("id", "")
        exp = ""
        if card_id:
            m = re.match(r"([A-Z]+\d+)", card_id)
            exp = f" #{m.group(1)}" if m else ""

        tipo = c.get("type", "")
        costo = f" c:{c['cost']}" if c.get("cost") is not None else ""
        poder = f" p:{c['power']}" if c.get("power") is not None else ""
        counter = f" ctr:{c['counter']}" if c.get("counter") is not None else ""
        kw_list: list[str] = c.get("keywords") or []
        kw_str = f" [{', '.join(kw_list)}]" if kw_list else ""

        lineas.append(f"- {c['name']}{exp} ({tipo}{costo}{poder}{counter}{kw_str})")
    return "\n".join(lineas)


def _formatear_lideres(leaders: list[dict]) -> str:
    """Formatea la lista de líderes disponibles para el prompt."""
    return "\n".join(
        f"- {l['name']} ({l['id']}) — Color: {l['color']}"
        for l in leaders
    )


class Deck(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ── Autocomplete ─────────────────────────────────────────────────────────

    async def _autocomplete_lider(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        try:
            opciones = await autocomplete_lideres(current)
            return [
                app_commands.Choice(name=label[:100], value=value[:100])
                for label, value in opciones
            ]
        except Exception as e:
            print(f"[autocomplete /mazo] Error: {e}")
            return []

    # ── Comando /mazo ─────────────────────────────────────────────────────────

    @app_commands.command(name="mazo", description="🏗️ Te ayudo a armar un mazo competitivo")
    @app_commands.describe(
        lider="Líder que querés usar — escribí para ver sugerencias",
        presupuesto="Tu presupuesto aproximado",
        estilo="Estilo de juego preferido",
    )
    @app_commands.autocomplete(lider=_autocomplete_lider)
    @app_commands.choices(
        presupuesto=[
            app_commands.Choice(name="Bajo ($20-40)", value="bajo"),
            app_commands.Choice(name="Medio ($40-80)", value="medio"),
            app_commands.Choice(name="Alto ($80+)", value="alto"),
        ],
        estilo=[
            app_commands.Choice(name="Agresivo (ganar rápido)", value="agresivo"),
            app_commands.Choice(name="Control (dominar el juego)", value="control"),
            app_commands.Choice(name="Combo (sinergias fuertes)", value="combo"),
            app_commands.Choice(name="Lo que mejor vaya", value="flexible"),
        ],
    )
    async def mazo(
        self,
        interaction: discord.Interaction,
        lider: str,
        presupuesto: app_commands.Choice[str] = None,
        estilo: app_commands.Choice[str] = None,
    ) -> None:
        if not puede_usar(interaction.user.id, "mazo"):
            await interaction.response.send_message(
                embed=embed_limite(), ephemeral=True
            )
            return

        await interaction.response.defer()

        pres = presupuesto.value if presupuesto else "medio"
        est = estilo.value if estilo else "flexible"

        # Paso 1: buscar TODOS los líderes que coincidan con el nombre
        # (punk-records, sin depender del scraper de Bandai)
        all_leaders = await buscar_lideres_por_nombre(lider)

        # Si punk-records no encontró nada, fallback al scraper Bandai
        if not all_leaders:
            leader_results = await buscar_carta_onepiece(lider)
            fallback_colors = _extraer_colores(leader_results) if leader_results else []
            all_leaders = [
                {"id": "?", "name": lider, "colors": fallback_colors, "color": "/".join(fallback_colors)}
            ] if fallback_colors else []

        # Unión de todos los colores de todos los líderes encontrados
        all_colors: list[str] = []
        seen_colors: set[str] = set()
        for l in all_leaders:
            for c in l.get("colors") or []:
                if c not in seen_colors:
                    seen_colors.add(c)
                    all_colors.append(c)

        # Paso 2: pool de cartas de todos los colores combinados
        pool_texto = ""
        if all_colors:
            # Aumentar límite porque puede haber varios colores mezclados
            pool_limit = min(50 + 10 * len(all_colors), 80)
            pool_cards = await buscar_cartas_por_color(all_colors, limite=pool_limit)
            if pool_cards:
                pool_texto = (
                    f"POOL DE CARTAS REALES disponibles "
                    f"(colores: {'/'.join(all_colors)}, sets más recientes primero):\n"
                    f"{_formatear_pool(pool_cards)}\n\n"
                    "Usá estas cartas como base. Si necesitás completar el mazo y el pool no alcanza, "
                    "podés agregar cartas conocidas del mismo color SIN inventar nombres ni expansiones.\n\n"
                )

        # Sección de líderes disponibles
        if len(all_leaders) > 1:
            leaders_section = (
                f"LÍDERES DISPONIBLES con el nombre '{lider}':\n"
                f"{_formatear_lideres(all_leaders)}\n\n"
                f"ELEGÍ el líder más competitivo y meta-relevante para OP-15 "
                f"según tu conocimiento del meta actual. "
                f"Construí el mazo SOLO con cartas del color de ese líder.\n\n"
            )
        elif all_leaders:
            leaders_section = (
                f"LÍDER: {all_leaders[0]['name']} ({all_leaders[0]['id']}) — "
                f"Color: {all_leaders[0]['color']}\n\n"
            )
        else:
            leaders_section = ""

        prompt = (
            f"{_DECKBUILDING_RULES}\n"
            f"{leaders_section}"
            f"{pool_texto}"
            f"Armame un mazo competitivo de One Piece TCG para el líder '{lider}' "
            f"(presupuesto: {pres}, estilo: {est}).\n\n"
            "REGLA ABSOLUTA: Tomá siempre la mejor decisión posible con los datos disponibles. "
            "NUNCA hagas preguntas. NUNCA pidas aclaraciones. "
            "Si hay ambigüedad, elegí la opción más competitiva para el meta OP-15 y ejecutá.\n\n"
            "Seguí este formato EXACTO:\n\n"
            "**LÍDER:** [nombre y color]\n\n"
            "**MAZO (50 cartas exactas):**\n"
            "4x NombreCarta #EXP\n"
            "...\n\n"
            "**ESTRATEGIA:** [2-3 oraciones: win condition, curva y cómo se activa la sinergia principal]\n\n"
            "**FAVORABLE vs:** [mazo] — [razón mecánica]\n"
            "**DIFÍCIL vs:** [mazo] — [razón mecánica]\n\n"
            "FORMATO:\n"
            "- '4x NombreCarta #EXP' (ej: 4x Enel #OP15, 3x Nola #OP15)\n"
            "- Si no sabés la expansión, solo el nombre\n"
            "- NO inventar nombres de cartas"
        )

        try:
            respuesta = await ask_coach(prompt, max_tokens=DECK_MAX_TOKENS)
        except Exception as e:
            await interaction.followup.send(
                embed=embed_error("Error al armar el mazo", str(e)), ephemeral=True
            )
            return

        if len(respuesta) > 4000:
            respuesta = respuesta[:3997] + "..."

        total_cartas = _contar_cartas(respuesta)
        aviso_count = ""
        if total_cartas == 50:
            aviso_count = "50/50 cartas ✓"
        elif total_cartas > 0:
            aviso_count = f"{total_cartas}/50 cartas ⚠️"

        count = get_uso(interaction.user.id, "mazo")
        embed = discord.Embed(
            title=f"🏗️ Mazo: {lider.title()}",
            description=respuesta,
            color=COLORS["deck"],
        )
        colores_str = "/".join(all_colors) if all_colors else "?"
        footer_parts = [p for p in [
            aviso_count,
            f"Pool: {colores_str}",
            f"Presupuesto: {pres} | Estilo: {est} | Consultas /mazo hoy: {count}/10",
        ] if p]
        embed.set_footer(text=" | ".join(footer_parts))
        await interaction.followup.send(embed=embed)

        log_usage(interaction.user.id, len(prompt), len(respuesta), "mazo")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Deck(bot))
