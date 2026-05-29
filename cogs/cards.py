import discord
from discord.ext import commands
from discord import app_commands
from utils.card_api import (
    buscar_carta_onepiece,
    buscar_carta_punk_records,
    autocomplete_cartas,
)
from utils.embeds import embed_no_encontrado
from config import COLORS

# ── Mapeos visuales ───────────────────────────────────────────────────────────

_EMBED_COLOR = {
    "Red":    0xE74C3C,
    "Blue":   0x3498DB,
    "Green":  0x2ECC71,
    "Purple": 0x9B59B6,
    "Black":  0x2C3E50,
    "Yellow": 0xF1C40F,
}

_COLOR_CIRCLE = {
    "Red":    "🔴",
    "Blue":   "🔵",
    "Green":  "🟢",
    "Purple": "🟣",
    "Black":  "⚫",
    "Yellow": "🟡",
}

_TYPE_ICON = {
    "LEADER":    "👑",
    "CHARACTER": "⚔️",
    "EVENT":     "💥",
    "STAGE":     "🏝️",
}

_TYPE_LABEL = {
    "LEADER":    "Líder",
    "CHARACTER": "Personaje",
    "EVENT":     "Evento",
    "STAGE":     "Escenario",
}

_RARITY_LABEL = {
    "L":   "Leader",
    "C":   "Common",
    "UC":  "Uncommon",
    "R":   "Rare",
    "SR":  "Super Rare",
    "SEC": "Secret Rare",
    "SP":  "Special",
    "TR":  "Treasure Rare",
    "P":   "Promo",
}


def _embed_color_for(color_str: str) -> int:
    primary = (color_str or "").split("/")[0].strip()
    return _EMBED_COLOR.get(primary, COLORS["cards"])


def _color_display(color_str: str) -> str:
    if not color_str:
        return "—"
    parts = [c.strip() for c in color_str.split("/")]
    circles = "".join(_COLOR_CIRCLE.get(p, "") for p in parts)
    return f"{circles} {color_str}" if circles else color_str


def _build_card_embed(card: dict, fuente: str, fuente_parcial: bool) -> discord.Embed:
    card_type_raw = (card.get("type") or "").upper()
    type_icon  = _TYPE_ICON.get(card_type_raw, "🃏")
    type_label = _TYPE_LABEL.get(card_type_raw, card.get("type") or "?")
    color_str  = card.get("color") or ""
    rarity     = card.get("rarity") or ""
    card_id    = card.get("id") or ""

    embed = discord.Embed(
        title=card.get("name", "Carta desconocida"),
        color=_embed_color_for(color_str),
    )

    identity_parts = [f"{type_icon} **{type_label}**"]
    if color_str:
        identity_parts.append(_color_display(color_str))
    if rarity:
        rarity_display = _RARITY_LABEL.get(rarity.upper(), rarity)
        identity_parts.append(f"✦ {rarity_display}")
    if card_id:
        identity_parts.append(f"`{card_id}`")
    embed.description = "  ·  ".join(identity_parts)

    cost    = card.get("cost")
    power   = card.get("power")
    counter = card.get("counter")

    stats: list[str] = []
    if cost is not None:
        stats.append(f"💰 Costo **{cost}**")
    if power is not None:
        stats.append(f"⚡ Poder **{power}**")
    if counter is not None:
        stats.append(f"🛡️ Counter **+{counter}**")
    elif card_type_raw in ("CHARACTER", "LEADER"):
        stats.append("🛡️ Counter **—**")

    if stats:
        embed.add_field(name="\u200b", value="  ·  ".join(stats), inline=False)

    attribute = card.get("attribute") or ""
    feature   = card.get("feature") or ""
    if attribute:
        embed.add_field(name="⚔️ Atributo", value=attribute, inline=True)
    if feature:
        embed.add_field(name="🏴‍☠️ Feature", value=feature, inline=True)

    if bool(attribute) ^ bool(feature):
        embed.add_field(name="\u200b", value="\u200b", inline=True)

    effect = card.get("effect") or ""
    if effect:
        embed.add_field(name="📜 Efecto", value=str(effect)[:1024], inline=False)

    trigger = card.get("trigger") or ""
    if trigger:
        embed.add_field(name="✨ Trigger", value=str(trigger)[:256], inline=False)

    img_url = card.get("img_url")
    if img_url:
        embed.set_thumbnail(url=img_url)

    footer = f"Fuente: {fuente}"
    if fuente_parcial:
        footer += " · Efecto completo no disponible (Bandai sin respuesta)"
    footer += "  |  🃏 Sin límite de uso"
    embed.set_footer(text=footer)

    return embed


# ── Cog ───────────────────────────────────────────────────────────────────────

class Cards(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _autocomplete_nombre(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        try:
            opciones = await autocomplete_cartas(current)
            return [
                app_commands.Choice(name=label, value=value)
                for label, value in opciones
            ]
        except Exception as e:
            print(f"[autocomplete /carta] Error: {e}")
            return []

    @app_commands.command(name="carta", description="🃏 Buscar una carta de One Piece TCG por nombre")
    @app_commands.describe(nombre="Nombre de la carta — escribí para ver sugerencias")
    @app_commands.autocomplete(nombre=_autocomplete_nombre)
    async def carta(self, interaction: discord.Interaction, nombre: str) -> None:
        await interaction.response.defer()

        # Parsear formato "CARD_ID|nombre" que viene del autocomplete
        card_id: str | None = None
        if "|" in nombre:
            partes = nombre.split("|", 1)
            card_id       = partes[0].strip()
            nombre_buscar = partes[1].strip()
        else:
            nombre_buscar = nombre.strip()

        fuente         = "Bandai oficial"
        fuente_parcial = False
        datos          = None

        # 1. Bandai por nombre (efecto completo + imagen)
        try:
            datos = await buscar_carta_onepiece(nombre_buscar)
        except Exception:
            datos = None

        # 2. Fallback punk-records — usa el ID del autocomplete para lookup exacto
        if not datos:
            datos          = await buscar_carta_punk_records(nombre_buscar, card_id=card_id)
            fuente         = "punk-records"
            fuente_parcial = True

        if not datos:
            await interaction.followup.send(
                embed=embed_no_encontrado(
                    nombre_buscar,
                    "Probá con el nombre en inglés (ej: 'Enel', 'Monkey D. Luffy').",
                )
            )
            return

        card  = datos[0] if isinstance(datos, list) else datos
        embed = _build_card_embed(card, fuente, fuente_parcial)
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Cards(bot))
