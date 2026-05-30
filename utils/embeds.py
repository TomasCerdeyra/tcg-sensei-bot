"""
Utilidades para embeds de error consistentes en todos los comandos.
"""
import discord
from config import COLORS


def embed_error(titulo: str, descripcion: str) -> discord.Embed:
    """Embed rojo para errores inesperados."""
    return discord.Embed(
        title=f"❌ {titulo}",
        description=descripcion,
        color=COLORS["error"],
    )


def embed_limite() -> discord.Embed:
    """Embed amarillo para cuando se alcanzó el límite diario."""
    return discord.Embed(
        title="⏳ Límite diario alcanzado",
        description=(
            "Usaste tus **10 consultas** de este comando para hoy.\n"
            "El contador se reinicia a medianoche.\n\n"
            "Cada comando IA tiene su propio límite de 10/día:\n"
            "- `/coach` — 10 preguntas libres\n"
            "- `/mazo` — 10 sugerencias de mazo\n"
            "- `/matchup` — 10 análisis de matchup\n"
            "- `/regla` — 10 consultas complejas (glosario es ilimitado)\n\n"
            "Los comandos `/meta`, `/carta`, `/precio` y `/resumen-reglas` son **ilimitados**."
        ),
        color=COLORS["limit"],
    )


def embed_no_encontrado(nombre: str, sugerencia: str = "") -> discord.Embed:
    """Embed para cuando no se encuentra una carta o recurso."""
    desc = f"No encontré resultados para **{nombre}**.\nVerificá la escritura e intentá de nuevo."
    if sugerencia:
        desc += f"\n\n💡 {sugerencia}"
    return discord.Embed(
        title="🔍 Sin resultados",
        description=desc,
        color=COLORS["error"],
    )
