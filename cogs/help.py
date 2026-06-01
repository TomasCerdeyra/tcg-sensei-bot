import discord
from discord.ext import commands
from discord import app_commands
from config import COLORS


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="📋 Ver todos los comandos disponibles")
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="🏴‍☠️ TCG Sensei — Comandos",
            description="Coach de One Piece TCG con IA en español. Preguntá sobre meta, armá mazos y analizá matchups.",
            color=COLORS["coach"],
        )

        embed.add_field(
            name="🤖 Con IA — 10 consultas por día",
            value=(
                "`/coach [pregunta]` — Estrategia, reglas, meta, lo que quieras\n"
                "`/mazo [líder]` — Mazo competitivo (líder, presupuesto y estilo son opcionales)\n"
                "`/matchup [mi_mazo] [rival]` — Plan de juego para ganarle a un rival"
            ),
            inline=False,
        )

        embed.add_field(
            name="🆓 Sin límite de uso",
            value=(
                "`/meta` — Tier list y winrates del meta actual OP-15\n"
                "`/carta [nombre]` — Buscar una carta: costo, poder, counter, efecto\n"
                "`/regla [término]` — Consultar una regla o mecánica específica\n"
                "`/precio [carta]` — Precio de mercado en Cardmarket y TCGPlayer\n"
                "`/resumen-reglas` — Descargar el resumen visual oficial de las reglas"
            ),
            inline=False,
        )

        embed.add_field(
            name="💡 Tips",
            value=(
                "• En `/mazo` podés no poner líder — el coach elige el mejor del meta\n"
                "• El límite de 10/día aplica solo a los comandos con IA\n"
                "• Si un comando tarda, es normal — está consultando la IA en tiempo real"
            ),
            inline=False,
        )

        embed.set_footer(
            text="Bot no oficial · No afiliado con Bandai ni One Piece Card Game · Datos: Bandai, Limitless TCG"
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
