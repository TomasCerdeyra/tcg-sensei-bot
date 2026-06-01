AI_DAILY_LIMIT = 10

# Tokens máximos por comando (ajustables sin tocar los cogs)
AI_MAX_TOKENS        = 700   # /coach  — respuestas de estrategia y reglas
AI_MAX_TOKENS_DECK   = 1200  # /mazo   — lista de 50 cartas + estrategia
AI_MAX_TOKENS_MATCHUP = 750  # /matchup — análisis estructurado

AI_MODEL        = "claude-haiku-4-5-20251001"   # /coach, /matchup, /regla, /carta
AI_MODEL_DECK   = "claude-sonnet-4-6"           # /mazo — requiere conteo preciso

COLORS = {
    "coach": 0x9B59B6,
    "meta": 0xE74C3C,
    "deck": 0x2ECC71,
    "matchup": 0xE67E22,
    "cards": 0x3498DB,
    "error": 0xE74C3C,
    "limit": 0xF39C12,
}

CURRENT_META = "OP-15"
META_LAST_UPDATED = "Mayo 2026"
