import urllib.parse
import discord
from discord.ext import commands
from discord import app_commands
from utils.card_api import autocomplete_cartas
from config import COLORS


def _cardmarket_url(nombre: str) -> str:
    query = urllib.parse.quote(nombre)
    return f"https://www.cardmarket.com/en/OnePiece/Products/Search?searchString={query}"


def _tcgplayer_url(nombre: str) -> str:
    query = urllib.parse.quote(nombre)
    return (
        f"https://www.tcgplayer.com/search/one-piece-card-game/product"
        f"?q={query}&view=grid"
    )


class Precio(commands.Cog):
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
            print(f"[autocomplete /precio] Error: {e}")
            return []

    @app_commands.command(
        name="precio",
        description="💰 Ver precio de mercado de una carta en Cardmarket y TCGPlayer",
    )
    @app_commands.describe(nombre="Nombre de la carta — escribí para ver sugerencias")
    @app_commands.autocomplete(nombre=_autocomplete_nombre)
    async def precio(self, interaction: discord.Interaction, nombre: str) -> None:
        cm_url = _cardmarket_url(nombre)
        tp_url = _tcgplayer_url(nombre)

        embed = discord.Embed(
            title=f"💰 Precios: {nombre}",
            description=(
                f"Consultá el precio de mercado actual en:\n\n"
                f"🇪🇺 **[Cardmarket]({cm_url})** — Mercado europeo (€)\n"
                f"🇺🇸 **[TCGPlayer]({tp_url})** — Mercado americano (USD)\n\n"
                "Los precios varían por idioma, condición y edición.\n"
                "Cardmarket suele tener mejores precios para el mercado hispano."
            ),
            color=COLORS["cards"],
        )
        embed.set_footer(text="💰 Comando ilimitado | Precios en tiempo real en los links")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Precio(bot))
