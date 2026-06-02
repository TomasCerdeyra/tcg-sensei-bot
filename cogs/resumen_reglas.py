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
        drive_url = os.getenv("PDF_DRIVE_URL", "").strip()

        embed = discord.Embed(
            title="📄 Resumen Visual de Reglas — One Piece TCG",
            color=COLORS["coach"],
        )
        embed.set_footer(text="📄 Sin límite de uso | Manual Oficial Bandai")

        # Si hay URL de Drive configurada, mostrar el link
        if drive_url:
            embed.description = (
                "Resumen oficial de las reglas del juego en formato visual.\n\n"
                f"[Descargar PDF desde Google Drive]({drive_url})\n\n"
                "Para preguntas específicas sobre reglas usá `/regla`."
            )
            await interaction.response.send_message(embed=embed)
            return

        # Fallback: intentar enviar el archivo local (dev / entorno con el PDF)
        if not os.path.exists(_PDF_PATH):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ PDF no disponible",
                    description=(
                        "El PDF no está disponible en este momento.\n"
                        "Configurá `PDF_DRIVE_URL` en el `.env` para habilitarlo."
                    ),
                    color=COLORS["error"],
                ),
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            file = discord.File(_PDF_PATH, filename=_PDF_NAME)
            embed.description = (
                "Resumen oficial de las reglas del juego en formato visual.\n\n"
                "Podés abrirlo directamente en Discord o descargarlo.\n\n"
                "Para preguntas específicas sobre reglas usá `/regla`."
            )
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
