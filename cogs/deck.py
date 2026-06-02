import re
import random
from typing import Optional
import discord
from discord.ext import commands
from discord import app_commands
from utils.ai import ask_coach
from utils.card_api import (
    buscar_carta_onepiece,
    buscar_carta_por_id,
    buscar_pool_para_mazo,
    buscar_lideres_por_nombre,
    autocomplete_lideres,
)
from utils.rate_limit import puede_usar, get_uso
from utils.logger import log_usage
from utils.embeds import embed_limite, embed_error
from config import COLORS, AI_MAX_TOKENS_DECK, AI_MODEL_DECK

# Suficiente para 50 cartas bien explicadas + estrategia
DECK_MAX_TOKENS = AI_MAX_TOKENS_DECK

# Reglas reales de deckbuilding de One Piece TCG inyectadas en cada prompt
_DECKBUILDING_RULES = """\
REGLAS OBLIGATORIAS de One Piece TCG (aplicá sin excepción):
- El mazo principal tiene EXACTAMENTE 50 cartas. El líder y el mazo Don!! son aparte y NO se cuentan.
- Máximo 4 copias del mismo número de carta.
- COLOR MULTICOLOR: Si el líder tiene dos colores (ej. Green/Black), podés usar cualquier carta que comparta AL MENOS UNO de esos colores. No necesitás que la carta tenga AMBOS colores.
- Antes de escribir la lista final, contá INTERNAMENTE las cartas línea por línea. Si no dan 50, ajustá cantidades hasta que den exactamente 50. NO incluyas ese conteo ni verificación en tu respuesta — es un paso interno tuyo.
- SILENCIO ABSOLUTO SOBRE EL POOL: Nunca menciones el pool de cartas, nunca analices qué cartas son compatibles, nunca expliques por qué elegiste o descartaste cartas del pool. Esa es tu lógica interna. Solo mostrá el resultado final.

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
    """Suma las cantidades en todas las líneas con formato 'Nx Nombre'."""
    total = 0
    for m in re.finditer(r"^\s*(\d+)\s*[xX]", texto, re.MULTILINE):
        total += int(m.group(1))
    return total


def _ajustar_a_50(respuesta: str) -> str:
    """
    Ajusta las cantidades de la lista de cartas para que sumen exactamente 50.
    No llama a la API — opera directamente sobre el texto generado por Claude.
    Modifica el mínimo de líneas posible: sube/baja copies de cartas existentes.
    Respeta el límite de 4 copias por carta y el mínimo de 1.
    """
    total = _contar_cartas(respuesta)
    if total == 50:
        return respuesta

    lineas = respuesta.split("\n")
    patron = re.compile(r"^(\s*)(\d+)(\s*[xX])(.+)$")

    # Localizar índice y cantidad de cada línea de carta
    entradas: list[tuple[int, int]] = []
    for i, linea in enumerate(lineas):
        if patron.match(linea):
            m = patron.match(linea)
            entradas.append((i, int(m.group(2))))  # type: ignore[union-attr]

    if not entradas:
        return respuesta

    diferencia = 50 - total  # positivo = faltan cartas, negativo = sobran

    def _set_qty(linea: str, nueva_qty: int) -> str:
        return re.sub(r"^(\s*)\d+", lambda m: f"{m.group(1)}{nueva_qty}", linea)

    if diferencia > 0:
        # Faltan cartas: aumentar en las que tienen menos de 4x (de mayor a menor qty)
        candidatos = sorted([(i, q) for i, q in entradas if q < 4], key=lambda x: -x[1])
        for idx, qty in candidatos:
            if diferencia <= 0:
                break
            aumento = min(4 - qty, diferencia)
            lineas[idx] = _set_qty(lineas[idx], qty + aumento)
            diferencia -= aumento
    else:
        # Sobran cartas: reducir en las que tienen más copies (de mayor a menor qty)
        candidatos = sorted([(i, q) for i, q in entradas if q > 1], key=lambda x: -x[1])
        for idx, qty in candidatos:
            if diferencia >= 0:
                break
            reduccion = min(qty - 1, -diferencia)
            lineas[idx] = _set_qty(lineas[idx], qty - reduccion)
            diferencia += reduccion

    return "\n".join(lineas)


_BUDGET_RARITY = {
    "bajo":  "PRESUPUESTO BAJO: priorizá cartas C (Common) y UC (Uncommon). Máximo 4 cartas SR (Super Rare) en el mazo. Evitá SP y SEC.",
    "medio": "PRESUPUESTO MEDIO: podés incluir cartas R (Rare) y hasta 8 SR (Super Rare). Evitá SP y SEC.",
    "alto":  "PRESUPUESTO ALTO: sin restricción de rareza. Priorizá el poder competitivo por sobre el costo.",
}

# Líderes meta OP-15 por estilo. Selección aleatoria para dar variedad al usuario.
_META_LIDERES = {
    "agresivo": ["Lucy", "Luffy"],
    "control":  ["Sakazuki", "Nami"],
    "combo":    ["Enel", "Luffy"],
    "flexible": ["Enel", "Sakazuki", "Nami", "Lucy", "Luffy"],
}


def _elegir_lider_meta(est: str) -> str:
    """Selecciona aleatoriamente un líder del meta OP-15 según estilo de juego."""
    pool = _META_LIDERES.get(est, _META_LIDERES["flexible"])
    return random.choice(pool)


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
    """Formatea el pool con datos completos incluyendo efecto para deckbuilding."""
    lineas = []
    for c in cards:
        card_id = c.get("id", "")
        clean_id = re.sub(r"_(p|r)\d+$", "", card_id) if card_id else ""
        exp = f" #{clean_id}" if clean_id else ""

        tipo = c.get("type", "")
        raridad = c.get("rarity", "")
        raridad_str = f" {raridad}" if raridad else ""
        costo = f" c:{c['cost']}" if c.get("cost") is not None else ""
        poder = f" p:{c['power']}" if c.get("power") is not None else ""
        counter = f" ctr:{c['counter']}" if c.get("counter") is not None else ""
        kw_list: list[str] = c.get("keywords") or []
        kw_str = f" [{', '.join(kw_list)}]" if kw_list else ""

        efecto = (c.get("effect") or "").strip()
        efecto_str = f"\n  → {efecto[:160]}" if efecto else ""

        lineas.append(f"- {c['name']}{exp} ({tipo}{raridad_str}{costo}{poder}{counter}{kw_str}){efecto_str}")
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

    @app_commands.command(name="mazo", description="🏗️ Armá un mazo competitivo — todos los parámetros son opcionales")
    @app_commands.describe(
        lider="Líder que querés usar (opcional — el coach elige el mejor si no ponés nada)",
        presupuesto="Tu presupuesto aproximado (opcional)",
        estilo="Estilo de juego preferido (opcional)",
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
        lider: Optional[str] = None,
        presupuesto: Optional[app_commands.Choice[str]] = None,
        estilo: Optional[app_commands.Choice[str]] = None,
    ) -> None:
        if not puede_usar(interaction.user.id, "mazo"):
            await interaction.response.send_message(
                embed=embed_limite(5), ephemeral=True
            )
            return

        await interaction.response.defer()

        pres = presupuesto.value if presupuesto else "medio"
        est = estilo.value if estilo else "flexible"

        all_leaders: list[dict] = []
        all_colors: list[str] = []
        pool_texto = ""
        leader_effect = ""
        lider_auto = False

        # Si no se especificó líder, elegir aleatoriamente del meta OP-15
        if not lider:
            lider = _elegir_lider_meta(est)
            lider_auto = True

        if lider:
            # Buscar líderes por nombre en punk-records
            all_leaders = await buscar_lideres_por_nombre(lider)

            # Fallback al scraper de Bandai si punk-records no encontró nada
            if not all_leaders:
                leader_results = await buscar_carta_onepiece(lider)
                fallback_colors = _extraer_colores(leader_results) if leader_results else []
                all_leaders = [
                    {"id": "?", "name": lider, "colors": fallback_colors, "color": "/".join(fallback_colors)}
                ] if fallback_colors else []

            # Unión de todos los colores
            seen_colors: set[str] = set()
            for l in all_leaders:
                for c in l.get("colors") or []:
                    if c not in seen_colors:
                        seen_colors.add(c)
                        all_colors.append(c)

            # Efecto del líder desde Bandai (solo match único para no agregar latencia)
            if len(all_leaders) == 1:
                leader_id = all_leaders[0].get("id", "")
                if leader_id and leader_id != "?":
                    bandai_leader = await buscar_carta_por_id(leader_id)
                    if bandai_leader:
                        leader_effect = bandai_leader[0].get("effect", "")

            # Pool completo con efectos desde Bandai
            if all_colors:
                pool_cards = await buscar_pool_para_mazo(all_colors)
                if pool_cards:
                    color_rule = (
                        f"REGLA MULTICOLOR: El líder tiene colores {'/'.join(all_colors)}. "
                        f"Podés usar cualquier carta que tenga AL MENOS UNO de esos colores. "
                        f"Todas las cartas de este pool ya cumplen esa condición — son todas válidas.\n"
                    )
                    pool_texto = (
                        f"POOL DE CARTAS DISPONIBLES ({len(pool_cards)} cartas — todas jugables con este líder):\n"
                        f"{color_rule}"
                        f"{_formatear_pool(pool_cards)}\n\n"
                        "RESTRICCIÓN ABSOLUTA: Solo podés usar cartas de este pool. No uses cartas que no estén en esta lista.\n"
                        "NO MENCIONES EL POOL EN TU RESPUESTA. No analices, no expliques, no hagas referencia al pool. "
                        "Pasá directamente al mazo.\n\n"
                    )

        # Sección de líderes en el prompt
        if lider and len(all_leaders) > 1:
            leaders_section = (
                f"LÍDERES DISPONIBLES con el nombre '{lider}':\n"
                f"{_formatear_lideres(all_leaders)}\n\n"
                "ELEGÍ el líder más competitivo para OP-15. "
                "Construí el mazo SOLO con cartas de su color.\n\n"
            )
        elif lider and all_leaders:
            effect_str = f"\nEfecto del líder: {leader_effect}" if leader_effect else ""
            leaders_section = (
                f"LÍDER: {all_leaders[0]['name']} ({all_leaders[0]['id']}) — "
                f"Color: {all_leaders[0]['color']}{effect_str}\n\n"
            )
        elif lider:
            leaders_section = f"Líder pedido: '{lider}' (no encontrado en el índice — usá tu conocimiento del meta OP-15).\n\n"
        else:
            leaders_section = ""

        lider_display = (all_leaders[0]['name'] if all_leaders else lider) or "meta OP-15"

        pool_rule = (
            "2. Usá ÚNICAMENTE cartas del pool provisto. No uses cartas que no estén en esa lista. "
            "Ignorá todo conocimiento previo de mazos — el pool es tu única fuente válida.\n"
            if pool_texto else
            "2. Usá únicamente cartas reales y conocidas de One Piece TCG.\n"
        )

        budget_guide = _BUDGET_RARITY.get(pres, _BUDGET_RARITY["medio"])

        prompt = (
            f"{_DECKBUILDING_RULES}\n"
            f"{leaders_section}"
            f"{pool_texto}"
            f"Armame un mazo competitivo de One Piece TCG "
            f"(estilo: {est}).\n"
            f"{budget_guide}\n\n"
            "REGLAS DE EJECUCIÓN — OBLIGATORIAS:\n"
            "1. NUNCA hagas preguntas ni pidas aclaraciones. Ejecutá siempre con criterio propio.\n"
            f"{pool_rule}"
            "3. PROHIBIDO en la respuesta: cualquier mención al pool (ni una palabra), análisis de compatibilidad "
            "de cartas, explicaciones de por qué elegiste cartas, secciones de verificación, totales matemáticos, "
            "conteos visibles, o cualquier texto fuera del formato de abajo. Si lo incluís, la respuesta es incorrecta.\n\n"
            "FORMATO EXACTO:\n\n"
            "**LÍDER:** [nombre] ([ID del pool]) — [color]\n\n"
            "**MAZO (50 cartas exactas):**\n"
            "4x NombreCarta #OP15-067\n"
            "3x OtraCarta #OP14-083\n"
            "... (OBLIGATORIO: cada carta lleva su #ID exacto del pool — NO inventes IDs)\n\n"
            "**ESTRATEGIA:** [2-3 oraciones: win condition, curva, sinergia principal]\n\n"
            "**FAVORABLE vs:** [mazo] — [razón mecánica]\n"
            "**DIFÍCIL vs:** [mazo] — [razón mecánica]"
        )

        try:
            respuesta = await ask_coach(prompt, max_tokens=DECK_MAX_TOKENS, model=AI_MODEL_DECK)
        except Exception as e:
            await interaction.followup.send(
                embed=embed_error("Error al armar el mazo", str(e)), ephemeral=True
            )
            return

        respuesta = _ajustar_a_50(respuesta)
        total_cartas = _contar_cartas(respuesta)

        if len(respuesta) > 4000:
            respuesta = respuesta[:3997] + "..."

        aviso_count = "50/50 cartas ✓" if total_cartas == 50 else (
            f"{total_cartas}/50 cartas ⚠️" if total_cartas > 0 else ""
        )

        count = get_uso(interaction.user.id, "mazo")
        embed = discord.Embed(
            title=f"🏗️ Mazo: {lider_display.title()}",
            description=respuesta,
            color=COLORS["deck"],
        )
        colores_str = "/".join(all_colors) if all_colors else "meta"
        auto_str = "Líder auto" if lider_auto else None
        footer_parts = [p for p in [
            aviso_count,
            auto_str,
            f"Pool: {colores_str}",
            f"Presupuesto: {pres} | Estilo: {est} | Consultas /mazo hoy: {count}/5",
        ] if p]
        embed.set_footer(text=" | ".join(footer_parts))
        await interaction.followup.send(embed=embed)

        log_usage(interaction.user.id, len(prompt), len(respuesta), "mazo")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Deck(bot))
