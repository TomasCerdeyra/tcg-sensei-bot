import re
import discord
from discord.ext import commands
from discord import app_commands
from config import COLORS, CURRENT_META, META_LAST_UPDATED

_META_FILE = "knowledge/meta_op15.txt"
_TIER_EMOJI = {"S": "🏆", "A": "⭐", "B": "📊"}


def _parse_meta_file() -> dict:
    try:
        with open(_META_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        return {}

    result: dict = {
        "tiers": {},
        "torneos_recientes": [],
        "proximos": [],
        "actualizacion": META_LAST_UPDATED,
    }

    m = re.search(r"actualización:\s*(.+)", content, re.IGNORECASE)
    if m:
        result["actualizacion"] = m.group(1).strip()

    tier_blocks = re.split(r"^## TIER ([A-Z])", content, flags=re.MULTILINE)
    i = 1
    while i + 1 < len(tier_blocks):
        tier_letter = tier_blocks[i].strip()
        tier_content = tier_blocks[i + 1]
        decks: list[str] = []

        deck_blocks = re.split(r"^### ", tier_content, flags=re.MULTILINE)
        for db in deck_blocks[1:]:
            lines = db.strip().splitlines()
            if not lines:
                continue
            deck_name = lines[0].strip()
            wr_match = re.search(r"Winrate[:\s~]+([0-9]+)%", db)
            ms_match = re.search(r"Meta share[:\s~]+([^\n]+)", db)

            extras = []
            if wr_match:
                extras.append(f"{wr_match.group(1)}% WR")
            if ms_match:
                share = ms_match.group(1).strip().rstrip(",")
                extras.append(share + " del meta" if "%" in share else share)

            entry = f"**{deck_name}**"
            if extras:
                entry += f" — {', '.join(extras)}"
            decks.append(entry)

        if decks:
            result["tiers"][tier_letter] = decks
        i += 2

    recent_block = re.search(
        r"## TORNEOS RECIENTES\n(.*?)(?=^##|\Z)", content,
        re.MULTILINE | re.DOTALL,
    )
    if recent_block:
        for line in recent_block.group(1).splitlines():
            line = line.strip().lstrip("- ").strip()
            if line:
                result["torneos_recientes"].append(line)

    proximos_block = re.search(
        r"## PRÓXIMOS TORNEOS\n(.*?)(?=^##|\Z)", content,
        re.MULTILINE | re.DOTALL,
    )
    if proximos_block:
        for line in proximos_block.group(1).splitlines():
            line = line.strip().lstrip("- ").strip()
            if line:
                result["proximos"].append(line)

    return result


class Meta(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="meta",
        description="📊 Ver el tier list y meta actual de One Piece TCG",
    )
    async def meta(self, interaction: discord.Interaction) -> None:
        data = _parse_meta_file()

        if not data:
            await interaction.response.send_message(
                "No se pudo cargar el archivo de meta. Avisale al admin.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"📊 Meta {CURRENT_META}",
            description="Adventure on Kami's Island",
            color=COLORS["meta"],
        )

        for tier_letter in ("S", "A", "B"):
            decks = data["tiers"].get(tier_letter)
            if not decks:
                continue
            emoji = _TIER_EMOJI.get(tier_letter, "▪️")
            embed.add_field(
                name=f"{emoji} Tier {tier_letter}",
                value="\n".join(decks),
                inline=False,
            )

        if data["torneos_recientes"]:
            embed.add_field(
                name="🏟️ Torneos recientes",
                value="\n".join(data["torneos_recientes"][:5]),
                inline=False,
            )

        if data["proximos"]:
            embed.add_field(
                name="📅 Próximos torneos",
                value="\n".join(data["proximos"]),
                inline=False,
            )

        embed.set_footer(
            text=f"Datos: Limitless TCG + opmetagame.com | Actualizado: {data['actualizacion']}"
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Meta(bot))
