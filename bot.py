import asyncio
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Forzar UTF-8 en la terminal de Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    description="🏴‍☠️ TCG Sensei — Tu coach de TCG con IA",
)

COGS = [
    "cogs.coach",
    "cogs.meta",
    "cogs.deck",
    "cogs.matchup",
    "cogs.cards",
    "cogs.regla",
    "cogs.precio",
    "cogs.resumen_reglas",
]


@bot.event
async def on_ready() -> None:
    print(f"✅ Bot conectado como {bot.user}")
    print(f"📡 En {len(bot.guilds)} servidor(es)")
    await bot.tree.sync()
    print("⚡ Slash commands sincronizados globalmente (puede tardar ~1 hora en Discord)")
    print("   → Usá '!sync' en tu servidor para sync instantáneo")
    try:
        from utils.card_api import _load_cards_index
        index = await _load_cards_index()
        print(f"📦 Cards index listo ({len(index)} cartas)")
    except Exception as e:
        print(f"⚠️  Cards index no pre-cargado: {e}")


@bot.tree.command(name="ping", description="Verificar que el bot está online")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "🏴‍☠️ ¡TCG Sensei está online y listo para coachear!"
    )


@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx: commands.Context) -> None:
    """Fuerza el sync de slash commands al servidor actual. Solo el dueño del bot."""
    try:
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(
            f"⚡ {len(synced)} slash commands sincronizados en **{ctx.guild.name}** al instante.\n"
            "Los comandos ya deberían aparecer. Si no, recargá Discord (Ctrl+R)."
        )
        print(f"[sync] {len(synced)} comandos sincronizados en '{ctx.guild.name}'")
    except Exception as e:
        await ctx.send(f"❌ Error al sincronizar: {e}")


async def main() -> None:
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"  ✓ Cog cargado: {cog}")
            except Exception as e:
                print(f"  ✗ Error en {cog}: {e}")
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("❌ ERROR: No se encontró DISCORD_TOKEN en el archivo .env")
            return
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
