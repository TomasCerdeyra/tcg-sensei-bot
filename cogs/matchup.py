import discord
from discord.ext import commands
from discord import app_commands
from utils.ai import ask_coach
from utils.card_api import autocomplete_lideres
from utils.rate_limit import puede_usar, get_uso
from utils.logger import log_usage
from utils.embeds import embed_limite, embed_error
from config import COLORS, AI_MAX_TOKENS_MATCHUP

MATCHUP_MAX_TOKENS = AI_MAX_TOKENS_MATCHUP


class Matchup(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def _autocomplete_mazo(
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
            print(f"[autocomplete /matchup] Error: {e}")
            return []

    @app_commands.command(name="matchup", description="⚔️ Cómo ganarle a un mazo específico")
    @app_commands.describe(
        mi_mazo="Tu mazo o líder — escribí para ver sugerencias",
        rival="El mazo o líder rival — escribí para ver sugerencias",
    )
    @app_commands.autocomplete(mi_mazo=_autocomplete_mazo, rival=_autocomplete_mazo)
    async def matchup(
        self,
        interaction: discord.Interaction,
        mi_mazo: str,
        rival: str,
    ) -> None:
        if not puede_usar(interaction.user.id, "matchup"):
            await interaction.response.send_message(
                embed=embed_limite(), ephemeral=True
            )
            return

        await interaction.response.defer()

        prompt = (
            f"Matchup One Piece TCG — meta OP-15:\n"
            f"MI MAZO: {mi_mazo}\n"
            f"RIVAL: {rival}\n\n"
            "Formato EXACTO — breve y directo, pensado para Discord:\n\n"
            "**VENTAJA:** [quién tiene ventaja — 1 oración con razón mecánica concreta]\n\n"
            "**PLAN DE JUEGO:**\n"
            "Mulligan: [1 línea — qué buscar]\n"
            "Turnos 1-3: [2 líneas — presión, setup o defensa]\n"
            "Turno 4+: [2 líneas — cómo cerrar o estabilizar]\n\n"
            "**MIS CARTAS CLAVE:** [3-4 cartas — Nombre: razón en 6 palabras max, sin IDs]\n\n"
            "**PELIGROS del rival:** [3-4 cartas — Nombre: razón en 6 palabras max]\n\n"
            "Reglas: mecánicas reales, sin side deck, meta OP-15."
        )

        try:
            respuesta = await ask_coach(prompt, max_tokens=MATCHUP_MAX_TOKENS)
        except Exception as e:
            await interaction.followup.send(
                embed=embed_error("Error al analizar el matchup", str(e)), ephemeral=True
            )
            return

        count = get_uso(interaction.user.id, "matchup")
        embed = discord.Embed(
            title=f"⚔️ {mi_mazo.title()} vs {rival.title()}",
            description=respuesta,
            color=COLORS["matchup"],
        )
        embed.set_footer(text=f"Consultas /matchup hoy: {count}/10 | Formato: OP-15")
        await interaction.followup.send(embed=embed)

        log_usage(interaction.user.id, len(prompt), len(respuesta), "matchup")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Matchup(bot))
