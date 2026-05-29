"""
Endpoint HTTP para recibir webhooks de Limitless TCG.
Procesa notificaciones de torneos terminados y descarga standings/decklists.
Ejecutar: python scripts/webhook_handler.py
"""
import json
import os

import aiohttp
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

LIMITLESS_SECRET = os.getenv("LIMITLESS_WEBHOOK_SECRET")
LIMITLESS_API_KEY = os.getenv("LIMITLESS_API_KEY")
API_BASE = "https://play.limitlesstcg.com/api"


async def handle_tournament_ended(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    if data.get("secret") != LIMITLESS_SECRET:
        return web.Response(status=401, text="Unauthorized")

    event = data.get("event", {})
    if event.get("name") != "tournament:ended":
        return web.Response(status=200, text="OK")

    tournament_id = event.get("tournamentId")
    game = event.get("game")

    if game not in ("OPTCG", "PTCG"):
        return web.Response(status=200, text="OK")

    await fetch_and_update_tournament(tournament_id, game)
    return web.Response(status=200, text="OK")


async def fetch_and_update_tournament(tournament_id: str, game: str) -> None:
    headers = {"X-Access-Key": LIMITLESS_API_KEY}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/tournaments/{tournament_id}/details",
            headers=headers,
        ) as resp:
            details = await resp.json()

        async with session.get(
            f"{API_BASE}/tournaments/{tournament_id}/standings",
            headers=headers,
        ) as resp:
            standings = await resp.json()

    result = {
        "tournament": details.get("name"),
        "date": details.get("date"),
        "players": details.get("players"),
        "game": game,
        "top_8": standings[:8] if standings else [],
    }

    filename = f"knowledge/recent_tournaments_{game.lower()}.json"
    with open(filename, "a", encoding="utf-8") as f:
        f.write(json.dumps(result) + "\n")

    print(f"✅ Torneo actualizado: {details.get('name')} ({game})")


app = web.Application()
app.router.add_post("/webhook/tournament", handle_tournament_ended)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
