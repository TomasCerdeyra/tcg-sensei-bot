<div align="center">

# 🏴‍☠️ TCG Sensei

**Bot de Discord con IA especializado en One Piece TCG**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.3%2B-5865F2?logo=discord&logoColor=white)](https://discordpy.readthedocs.io/)
[![Claude](https://img.shields.io/badge/AI-Claude%20(Anthropic)-D97757?logo=anthropic&logoColor=white)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/status-personal%20project-lightgrey)]()

Preguntá estrategia, armá mazos competitivos de 50 cartas, analizá matchups y consultá el meta — todo en español, desde slash commands.

</div>

> Bot no oficial. No afiliado con Bandai ni con One Piece Card Game.

## Índice

- [Qué hace](#qué-hace)
- [Cómo está construido](#cómo-está-construido)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Deploy 24/7](#deploy-247-opcional)
- [Solución de problemas](#solución-de-problemas)

## Qué hace

| Comando | Con IA | Límite/día | Descripción |
|---|:---:|:---:|---|
| `/coach [pregunta]` | ✅ | 10 | Preguntas libres de estrategia, reglas o meta |
| `/mazo [líder] [presupuesto] [estilo]` | ✅ | 5 | Arma un mazo competitivo de 50 cartas exactas. Todos los parámetros son opcionales — si no elegís líder, el bot elige uno del meta actual |
| `/matchup [mi_mazo] [rival]` | ✅ | 10 | Plan de juego, cartas clave y peligros contra un mazo rival |
| `/regla [término]` | ✅* | 10* | Explica una mecánica del juego. Términos comunes (Rush, Blocker, Counter, Trigger, DON!!...) responden desde un glosario estático sin usar IA ni consumir límite |
| `/meta` | — | ∞ | Tier list actual (S/A/B), winrates y próximos torneos |
| `/carta [nombre]` | — | ∞ | Busca una carta: costo, poder, counter, efecto, trigger |
| `/precio [carta]` | — | ∞ | Links directos a Cardmarket y TCGPlayer para esa carta |
| `/resumen-reglas` | — | ∞ | Descarga el resumen visual oficial de reglas (PDF) |
| `/help` | — | ∞ | Lista todos los comandos |

Los límites diarios son por usuario y se resetean a medianoche.

## Cómo está construido

- **Bot:** `discord.py` con slash commands (`app_commands`), arquitectura basada en cogs — un módulo independiente por comando.
- **IA:** Anthropic Claude, con dos modelos según la tarea — Haiku para respuestas rápidas (`/coach`, `/matchup`, `/regla`) y Sonnet para `/mazo`, donde se necesita conteo preciso de 50 cartas. El *system prompt* y las reglas del juego se cargan desde `knowledge/` con cache y hot-reload cada 1 hora.
- **Cartas:** búsqueda contra la API oficial de Bandai, con [punk-records](https://github.com/buhbbl/punk-records) como fallback si Bandai no responde.
- **Persistencia:** rate limiting por usuario/comando en SQLite (`data/rate_limit.db`), con fallback automático a memoria si SQLite no está disponible.
- **Meta:** tier list cargada y parseada desde `knowledge/meta_op15.txt` (fuente: Limitless TCG + opmetagame.com).

## Requisitos

- **Python 3.10 o superior**
- Una cuenta de **Discord** para crear la aplicación del bot
- Una cuenta de **Anthropic** con API key (billing activado) para los comandos con IA

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/TomasCerdeyra/tcg-sensei-bot.git
cd tcg-sensei-bot
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Crear tu bot de Discord

1. Andá a [discord.com/developers/applications](https://discord.com/developers/applications) e iniciá sesión.
2. **New Application** → nombre `TCG Sensei` → **Create**.
3. Menú lateral → **Bot** → **Reset Token** → copiá el token (es tu `DISCORD_TOKEN`).
4. En la misma página, bajá hasta **Privileged Gateway Intents** y activá:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
5. **Save Changes**.
6. Menú lateral → **OAuth2** → **URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: Send Messages, Embed Links, Attach Files, Read Message History, Use Slash Commands
7. Copiá la URL generada, abrila en el navegador y autorizá el bot en tu servidor de prueba.

### 4. Obtener tu API key de Anthropic

1. Andá a [console.anthropic.com](https://console.anthropic.com) y creá una cuenta.
2. **Settings → Billing** → agregá un método de pago (el modelo Haiku es muy barato, unos centavos por consulta; podés poner un límite de gasto mensual en **Settings → Limits**).
3. **API Keys → Create Key** → copiá la key (empieza con `sk-ant-...`).

### 5. Configurar variables de entorno

Copiá el archivo de ejemplo y completalo con tus propios valores:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Editá `.env`:

```env
DISCORD_TOKEN=tu_token_de_discord
ANTHROPIC_API_KEY=sk-ant-tu_api_key
LIMITLESS_API_KEY=pendiente
LIMITLESS_WEBHOOK_SECRET=pendiente
PDF_DRIVE_URL=
```

- `DISCORD_TOKEN` y `ANTHROPIC_API_KEY` son obligatorios para que el bot funcione con IA.
- `LIMITLESS_API_KEY` / `LIMITLESS_WEBHOOK_SECRET` solo son necesarios si vas a usar `scripts/webhook_handler.py` para automatizar la actualización del meta desde torneos de Limitless TCG.
- `PDF_DRIVE_URL` es opcional: un link de Google Drive para `/resumen-reglas`. Si lo dejás vacío, el comando intenta servir el PDF local en `knowledge/`.

⚠️ Nunca subas tu `.env` a GitHub — ya está incluido en `.gitignore`.

### 6. Ejecutar el bot

```bash
python bot.py
```

Deberías ver en la consola:

```
✅ Bot conectado como TCG Sensei#XXXX
📡 En N servidor(es)
⚡ Slash commands sincronizados globalmente (puede tardar ~1 hora en Discord)
```

El sync global de slash commands puede tardar hasta una hora en aparecer en Discord. Para probarlo al instante en tu servidor de prueba, usá `!sync` (solo funciona para el dueño del bot).

### 7. Probar en Discord

- `/ping` → confirma que el bot está online
- `/meta` → muestra el tier list actual
- `/carta enel` → busca una carta
- `/coach ¿qué mazo me recomendás para empezar?` → primer test con IA

## Estructura del proyecto

```
tcg-sensei/
├── bot.py                    # Punto de entrada: carga cogs y arranca el bot
├── config.py                 # Límites diarios, modelos de IA, colores de embeds
├── requirements.txt
├── Procfile                  # Para deploy en Railway
├── .env                       # Tokens y API keys (no se sube a git)
│
├── cogs/                      # Un archivo por comando slash
│   ├── coach.py                 # /coach
│   ├── deck.py                  # /mazo
│   ├── matchup.py                # /matchup
│   ├── meta.py                    # /meta
│   ├── cards.py                   # /carta
│   ├── regla.py                    # /regla
│   ├── precio.py                    # /precio
│   ├── resumen_reglas.py             # /resumen-reglas
│   └── help.py                        # /help
│
├── knowledge/                 # Contexto que se inyecta al system prompt de la IA
│   ├── system_prompt.txt
│   ├── rules_optcg.md
│   └── meta_op15.txt
│
├── utils/
│   ├── ai.py                   # Wrapper de la API de Anthropic + cache de knowledge
│   ├── card_api.py               # Búsqueda de cartas (Bandai + punk-records)
│   ├── rate_limit.py              # Límite diario por usuario/comando (SQLite)
│   ├── embeds.py                    # Embeds reutilizables (error, límite, etc.)
│   └── logger.py                     # Log de uso de IA en data/usage_log.json
│
├── scripts/
│   ├── update_cards.py           # Actualización periódica del índice de cartas
│   └── webhook_handler.py          # Webhook de Limitless TCG para nuevos torneos
│
└── data/                       # Datos generados en runtime (SQLite, logs) — no se sube a git
```

## Deploy 24/7 (opcional)

Para que el bot corra sin depender de tu PC, la opción más simple es **[Railway](https://railway.app)**:

1. Subí el repo a GitHub (verificá que `.env` no esté incluido).
2. En Railway: **New Project → Deploy from GitHub Repo** → seleccioná el repo.
3. En **Variables**, agregá `DISCORD_TOKEN` y `ANTHROPIC_API_KEY`.
4. Railway detecta el `Procfile` (`worker: python bot.py`) y deploya automáticamente.

## Solución de problemas

- **El bot no responde a slash commands:** esperá hasta 1 hora tras el primer arranque (sync global) o usá `!sync` en el servidor.
- **Error 401 de Claude:** la `ANTHROPIC_API_KEY` es incorrecta o expiró.
- **Error 429 de Claude:** se excedió el rate limit de la cuenta de Anthropic, esperá unos segundos.
- **`/coach` responde "La IA no está configurada":** falta o es inválido el valor de `ANTHROPIC_API_KEY` en `.env`.
- **Falla un import al arrancar:** verificá que instalaste `requirements.txt` dentro del entorno virtual activado.
