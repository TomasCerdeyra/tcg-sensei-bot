import os
import time
import json

from anthropic import AsyncAnthropic
from config import AI_MAX_TOKENS, AI_MODEL, AI_MODEL_DECK

_knowledge_cache: dict = {"content": "", "last_loaded": 0}
RELOAD_INTERVAL = 3600  # recargar cada 1 hora

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if _client is None:
        _client = AsyncAnthropic(api_key=api_key)
    return _client

# Directorio base del proyecto (un nivel arriba de utils/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_knowledge() -> str:
    now = time.time()
    if now - _knowledge_cache["last_loaded"] < RELOAD_INTERVAL:
        return _knowledge_cache["content"]

    knowledge_files = [
        os.path.join(_BASE_DIR, "knowledge", "system_prompt.txt"),
        os.path.join(_BASE_DIR, "knowledge", "rules_optcg.md"),
        os.path.join(_BASE_DIR, "knowledge", "meta_op15.txt"),
    ]

    knowledge = ""
    for filepath in knowledge_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                knowledge += f.read() + "\n\n"
        except FileNotFoundError:
            print(f"[ai] Archivo no encontrado: {filepath}")

    try:
        with open(os.path.join(_BASE_DIR, "knowledge", "recent_tournaments_optcg.json"), "r", encoding="utf-8") as f:
            lines = f.readlines()[-5:]
            tournaments = [json.loads(line) for line in lines if line.strip()]
            knowledge += "\n## Últimos torneos registrados:\n"
            for t in tournaments:
                knowledge += f"- {t['tournament']} ({t['date'][:10]}): {t['players']} jugadores\n"
    except FileNotFoundError:
        pass

    _knowledge_cache["content"] = knowledge
    _knowledge_cache["last_loaded"] = now
    print(f"[ai] Knowledge recargado ({len(knowledge)} chars)")
    return knowledge


async def ask_coach(
    pregunta: str,
    contexto: str = "",
    max_tokens: int | None = None,
    model: str | None = None,
) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "pendiente":
        return "⚠️ La IA no está configurada todavía. Pedile al admin que configure la API key de Anthropic."

    user_message = pregunta
    if contexto:
        user_message = f"Contexto adicional: {contexto}\n\nPregunta: {pregunta}"

    tokens = max_tokens or AI_MAX_TOKENS
    model_id = model or AI_MODEL

    try:
        client = _get_client()
        message = await client.messages.create(
            model=model_id,
            max_tokens=tokens,
            system=load_knowledge(),
            messages=[{"role": "user", "content": user_message}],
        )
        return message.content[0].text
    except Exception as e:
        return f"⚠️ Error al consultar la IA: {str(e)}"
