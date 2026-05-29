"""
Script para mantener el índice de cartas de One Piece TCG actualizado.
Fuente: punk-records (github.com/buhbbl/punk-records) — dataset oficial basado en Bandai.

Uso:
  python scripts/update_cards.py

Cron job semanal sugerido (Linux/Railway):
  0 3 * * 0 cd /app && python scripts/update_cards.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime

import aiohttp

# Paths relativos a la raíz del proyecto (ejecutar desde tcg-sensei/)
CARDS_INDEX_FILE = "knowledge/cards_index.json"
PACKS_CACHE_FILE  = "knowledge/packs_cache.json"

PUNK_INDEX_URL = (
    "https://raw.githubusercontent.com/buhbbl/punk-records/main"
    "/english/index/cards_by_id.json"
)
PUNK_PACKS_URL = (
    "https://raw.githubusercontent.com/buhbbl/punk-records/main"
    "/english/packs.json"
)


def _load_current_index() -> dict:
    try:
        with open(CARDS_INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _load_current_packs() -> dict:
    try:
        with open(PACKS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


async def update_cards_index(session: aiohttp.ClientSession) -> tuple[bool, int, int]:
    """
    Descarga el índice de cartas de punk-records y lo guarda localmente.
    Retorna (hubo_cambios, cantidad_anterior, cantidad_nueva).
    """
    print(f"  Descargando cards_by_id.json desde punk-records...")
    async with session.get(
        PUNK_INDEX_URL, timeout=aiohttp.ClientTimeout(total=60)
    ) as resp:
        if resp.status != 200:
            print(f"  ERROR: no se pudo descargar el índice (HTTP {resp.status})")
            return False, 0, 0
        new_data: dict = await resp.json(content_type=None)

    old_data = _load_current_index()
    old_count = len(old_data)
    new_count = len(new_data)

    os.makedirs("knowledge", exist_ok=True)
    with open(CARDS_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False)

    return new_count > old_count, old_count, new_count


async def update_packs(session: aiohttp.ClientSession) -> tuple[bool, list[str]]:
    """
    Descarga packs.json y detecta sets nuevos.
    Retorna (hubo_cambios, lista_de_sets_nuevos).
    """
    print(f"  Descargando packs.json desde punk-records...")
    async with session.get(
        PUNK_PACKS_URL, timeout=aiohttp.ClientTimeout(total=30)
    ) as resp:
        if resp.status != 200:
            print(f"  ERROR: no se pudo descargar packs (HTTP {resp.status})")
            return False, []
        new_packs: dict = await resp.json(content_type=None)

    old_packs = _load_current_packs()
    old_ids  = set(old_packs.keys())
    new_ids  = set(new_packs.keys())
    new_sets = sorted(new_ids - old_ids)

    with open(PACKS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(new_packs, f, ensure_ascii=False)

    return bool(new_sets), new_sets


async def main() -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Iniciando actualización de cartas (punk-records)...")
    print()

    async with aiohttp.ClientSession() as session:
        cards_changed, old_count, new_count = await update_cards_index(session)
        packs_changed, new_sets           = await update_packs(session)

    print()
    print("=== RESULTADO ===")

    if cards_changed:
        diff = new_count - old_count
        print(f"  CARTAS: {old_count} -> {new_count} (+{diff} nuevas entradas)")
    else:
        print(f"  CARTAS: sin cambios ({new_count} cartas en total)")

    if packs_changed:
        print(f"  SETS NUEVOS detectados: {new_sets}")
        print()
        print("  Acciones recomendadas tras un set nuevo:")
        print("    1. Esperar 2-3 semanas para que el meta se estabilice")
        print("    2. Actualizar knowledge/meta_opXX.txt con el nuevo tier list")
        print("    3. Agregar keywords nuevos en knowledge/rules_optcg.txt si los hay")
        print("    4. Reiniciar el bot para que cargue el nuevo índice")
    else:
        print(f"  SETS: sin cambios")

    print()
    print(f"  Archivo actualizado: {CARDS_INDEX_FILE}")
    print(f"  Archivo actualizado: {PACKS_CACHE_FILE}")


if __name__ == "__main__":
    # Asegurar que los paths relativos funcionen tanto desde tcg-sensei/ como desde scripts/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)

    asyncio.run(main())
