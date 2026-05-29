import os
import discord
from discord.ext import commands
from discord import app_commands
from config import COLORS

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PDF_PATH = os.path.join(_BASE_DIR, "knowledge", "Resumen-manual-tcg.pdf")
_PDF_NAME = "Resumen-Reglas-OPTCG.pdf"


class ResumenReglas(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="resumen-reglas",
        description="📄 Descargá el resumen visual oficial de las reglas de One Piece TCG",
    )
    async def resumen_reglas(self, interaction: discord.Interaction) -> None:
        if not os.path.exists(_PDF_PATH):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Archivo no encontrado",
                    description="El PDF de resumen no está disponible en este momento.",
                    color=COLORS["error"],
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            file = discord.File(_PDF_PATH, filename=_PDF_NAME)
            embed = discord.Embed(
                title="📄 Resumen Visual de Reglas — One Piece TCG",
                description=(
                    "Resumen oficial de las reglas del juego en formato visual.\n\n"
                    "Podés abrirlo directamente en Discord o descargarlo.\n\n"
                    "Para preguntas específicas sobre reglas usá `/regla`."
                ),
                color=COLORS["coach"],
            )
            embed.set_footer(text="📄 Sin límite de uso | Manual Oficial Bandai")
            await interaction.followup.send(embed=embed, file=file)

        except Exception as e:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="❌ Error al enviar el archivo",
                    description=f"No se pudo enviar el PDF: {e}",
                    color=COLORS["error"],
                ),
                ephemeral=True,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ResumenReglas(bot))
