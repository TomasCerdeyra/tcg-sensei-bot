import discord
from discord.ext import commands
from discord import app_commands
from utils.ai import ask_coach
from utils.rate_limit import puede_usar, get_uso
from utils.logger import log_usage
from utils.embeds import embed_limite, embed_error
from config import COLORS


class Coach(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="coach", description="💬 Preguntale lo que quieras al coach de TCG")
    @app_commands.describe(pregunta="Tu pregunta sobre TCG (reglas, estrategia, mazos, etc.)")
    async def coach(self, interaction: discord.Interaction, pregunta: str) -> None:
        if not puede_usar(interaction.user.id, "coach"):
            await interaction.response.send_message(
                embed=embed_limite(), ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            respuesta = await ask_coach(pregunta)
        except Exception as e:
            await interaction.followup.send(
                embed=embed_error("Error al consultar la IA", str(e)), ephemeral=True
            )
            return

        count = get_uso(interaction.user.id, "coach")
        embed = discord.Embed(
            title="🏴‍☠️ TCG Sensei",
            description=respuesta,
            color=COLORS["coach"],
        )
        embed.set_footer(text=f"Consultas /coach hoy: {count}/10")
        await interaction.followup.send(embed=embed)

        log_usage(interaction.user.id, len(pregunta), len(respuesta), "coach")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Coach(bot))
