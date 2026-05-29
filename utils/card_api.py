import re
import json
import time
import os
import asyncio
import html
import aiohttp

_BANDAI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# punk-records: dataset pre-generado con TODAS las cartas del juego
_PUNK_INDEX_URL = (
    "https://raw.githubusercontent.com/buhbbl/punk-records/main"
    "/english/index/cards_by_id.json"
)
_PUNK_NAMES_URL = (
    "https://raw.githubusercontent.com/buhbbl/punk-records/main"
    "/english/index/by_name.json"
)
# Path absoluto relativo al directorio de este archivo (evita problemas de CWD)
_CARDS_INDEX_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "knowledge", "cards_index.json"
)
_INDEX_TTL = 3600 * 24 * 7  # 7 días antes de re-descargar

_INDEX_CACHE: dict = {}
_INDEX_LOADED_AT: float = 0.0

# Mapa de tipos en español → categoría punk-records
_TYPE_KEYWORD_MAP: dict[str, str] = {
    "lider": "Leader", "líder": "Leader", "líderes": "Leader", "lideres": "Leader",
    "leader": "Leader", "leaders": "Leader",
    "evento": "Event", "eventos": "Event", "event": "Event", "events": "Event",
    "personaje": "Character", "personajes": "Character",
    "character": "Character", "characters": "Character",
    "escenario": "Stage", "escenarios": "Stage", "stage": "Stage", "stages": "Stage",
}

_TYPE_LABEL_ES: dict[str, str] = {
    "Leader": "Líder", "Event": "Evento",
    "Character": "Personaje", "Stage": "Escenario",
}

# Mapa de colores en español/variantes → nombre exacto en punk-records
_COLOR_MAP = {
    "red": "Red", "rojo": "Red", "r": "Red",
    "blue": "Blue", "azul": "Blue", "b": "Blue",
    "green": "Green", "verde": "Green", "g": "Green",
    "purple": "Purple", "purpura": "Purple", "púrpura": "Purple", "p": "Purple",
    "black": "Black", "negro": "Black", "bk": "Black",
    "yellow": "Yellow", "amarillo": "Yellow", "y": "Yellow",
}


def _set_sort_key(card_id: str) -> tuple:
    """Ordena sets del más reciente al más antiguo (OP15 > OP14 > ST29 > ...)."""
    m = re.match(r"^([A-Z]+)(\d+)", card_id)
    if not m:
        return (9, 0)
    prefix, num = m.group(1), int(m.group(2))
    # Prioridad de prefijo: OP primero, luego ST, EB, PRB
    prefix_order = {"OP": 0, "ST": 1, "EB": 2, "PRB": 3}
    return (prefix_order.get(prefix, 9), -num)  # -num = descendente


# ── Índice local de cartas (punk-records) ──────────────────────────────────


def _read_index_from_file(path: str) -> dict:
    """Lee y parsea el JSON del índice de forma síncrona (llamar via asyncio.to_thread)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_index_to_file(path: str, data: dict) -> None:
    """Guarda el índice en disco de forma síncrona (llamar via asyncio.to_thread)."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


async def _load_cards_index() -> dict:
    """Carga el índice de cartas desde caché, archivo local o GitHub."""
    global _INDEX_CACHE, _INDEX_LOADED_AT
    now = time.time()

    # 1. Caché en memoria (válido por TTL)
    if _INDEX_CACHE and (now - _INDEX_LOADED_AT) < _INDEX_TTL:
        return _INDEX_CACHE

    # 2. Archivo local (válido por TTL desde la fecha de modificación)
    try:
        file_age = now - os.path.getmtime(_CARDS_INDEX_FILE)
        if file_age < _INDEX_TTL:
            # Usar to_thread para no bloquear el event loop con el JSON de 1.2MB
            data = await asyncio.to_thread(_read_index_from_file, _CARDS_INDEX_FILE)
            _INDEX_CACHE = data
            _INDEX_LOADED_AT = now
            print(f"[cards] Index cargado desde archivo ({len(_INDEX_CACHE)} cartas)")
            return _INDEX_CACHE
    except (FileNotFoundError, OSError):
        print(f"[cards] Archivo no encontrado o no accesible: {_CARDS_INDEX_FILE}")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[cards] Error parseando JSON del índice: {e}")

    # 3. Descargar desde GitHub (punk-records)
    print("[cards] Descargando index desde GitHub (punk-records)...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                _PUNK_INDEX_URL, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    _INDEX_CACHE = data
                    _INDEX_LOADED_AT = now
                    knowledge_dir = os.path.dirname(_CARDS_INDEX_FILE)
                    os.makedirs(knowledge_dir, exist_ok=True)
                    await asyncio.to_thread(_write_index_to_file, _CARDS_INDEX_FILE, data)
                    print(f"[cards] Index descargado y guardado ({len(data)} cartas)")
                    return data
                else:
                    print(f"[cards] GitHub respondió {resp.status}")
    except Exception as e:
        print(f"⚠️ Error descargando cards index: {e}")

    return {}


# ── HTML scraper Bandai (para /carta — datos completos con efecto) ─────────


def _parse_onepiece_html(html: str) -> list[dict]:
    cards = []
    blocks = re.split(r'<dl class="modalCol"', html)
    for block in blocks[1:]:
        card: dict = {}
        m = re.match(r'\s+id="([^"]+)"', block)
        if m:
            card["id"] = m.group(1)
        info = re.search(
            r'class="infoCol">\s*<span>([^<]+)</span>\s*\|\s*<span>([^<]+)</span>\s*\|\s*<span>([^<]+)</span>',
            block,
        )
        if info:
            card["rarity"] = info.group(2).strip()
            card["type"] = info.group(3).strip()
        name = re.search(r'class="cardName">([^<]+)<', block)
        if name:
            card["name"] = name.group(1).strip()
        for field in ["cost", "power", "counter", "color"]:
            m2 = re.search(rf'class="{field}"><h3>[^<]+</h3>([^<]+)<', block)
            if m2:
                val = m2.group(1).strip()
                card[field] = None if val == "-" else val
        attr = re.search(
            r'class="attribute">\s*<h3>[^<]+</h3>\s*([^<\n]+?)\s*<', block
        )
        if attr:
            val = attr.group(1).strip()
            card["attribute"] = None if val in ("-", "") else val
        feat = re.search(r'class="feature"><h3>[^<]+</h3>([^<]+)<', block)
        if feat:
            card["feature"] = feat.group(1).strip()
        effect = re.search(
            r'class="text"><h3>[^<]+</h3>(.*?)</div>', block, re.DOTALL
        )
        if effect:
            card["effect"] = re.sub(r"<[^>]+>", "", effect.group(1)).strip()
        trigger = re.search(
            r'class="trigger"><h3>[^<]+</h3>(.*?)</div>', block, re.DOTALL
        )
        if trigger:
            t = re.sub(r"<[^>]+>", "", trigger.group(1)).strip()
            if t:
                card["trigger"] = t
        card_set = re.search(r'class="getInfo"><h3>[^<]+</h3>([^<]+)<', block)
        if card_set:
            card["set"] = card_set.group(1).strip()
        if card.get("name"):
            # Imagen: data-src="../images/cardlist/card/OP15-001.png?xxxxxx"
            img_match = re.search(r'data-src="([^"]+cardlist/card/[^"]+)"', block)
            if img_match:
                # Normalizar path: "../images/..." → "/images/..."
                path = img_match.group(1).split("?")[0]
                path = re.sub(r"^\.\./", "/", path)  # quitar "../" inicial
                if not path.startswith("http"):
                    path = f"https://en.onepiece-cardgame.com{path}"
                card["img_url"] = path
            cards.append(card)

    seen_base_ids: set[str] = set()
    unique: list[dict] = []
    for c in cards:
        base_id = re.sub(r"_[a-z]\d+$", "", c.get("id", ""))
        if base_id not in seen_base_ids:
            seen_base_ids.add(base_id)
            unique.append(c)

    # Reordenar: LEADER > CHARACTER > EVENT/STAGE para que el resultado
    # más relevante aparezca primero en /carta
    _TYPE_ORDER = {"LEADER": 0, "CHARACTER": 1, "EVENT": 2, "STAGE": 3}
    unique.sort(key=lambda c: _TYPE_ORDER.get(c.get("type", "").upper(), 9))
    return unique


async def buscar_carta_por_id(card_id: str) -> list[dict] | None:
    """
    Busca una carta en Bandai por ID exacto (card_num[]=OP14-038).
    Más rápido y preciso que la búsqueda por texto libre.
    """
    url = "https://en.onepiece-cardgame.com/cardlist/"
    params = [("card_num[]", card_id), ("search", "true")]

    async def _fetch() -> list[dict] | None:
        async with aiohttp.ClientSession(headers=_BANDAI_HEADERS) as session:
            async with session.get(
                url, params=params,
                timeout=aiohttp.ClientTimeout(connect=4, total=10),
            ) as resp:
                if resp.status == 200:
                    html_text = await resp.text()
                    cards = _parse_onepiece_html(html_text)
                    return cards[:1] if cards else None
        return None

    try:
        return await asyncio.wait_for(_fetch(), timeout=12)
    except asyncio.TimeoutError:
        print(f"[Bandai] timeout buscando ID '{card_id}'")
    except Exception as e:
        print(f"[Bandai] error buscando ID '{card_id}': {e}")
    return None


async def buscar_carta_onepiece(nombre: str) -> list[dict] | None:
    """
    Busca carta en Bandai (datos completos incluyendo efecto e imagen).
    Timeout agresivo: connect=4s, total=10s + asyncio.wait_for como guardia final.
    Si Bandai cuelga, devuelve None rápidamente para que el fallback tome el control.
    """
    url = "https://en.onepiece-cardgame.com/cardlist/"
    params = {"freewords": nombre, "search": "true"}

    async def _fetch() -> list[dict] | None:
        async with aiohttp.ClientSession(headers=_BANDAI_HEADERS) as session:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(connect=4, total=10),
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    cards = _parse_onepiece_html(html)
                    return cards[:5] if cards else None
        return None

    try:
        # Guard adicional: si aiohttp no lanza en 12s, cancelamos
        return await asyncio.wait_for(_fetch(), timeout=12)
    except asyncio.TimeoutError:
        print(f"[Bandai] timeout buscando '{nombre}'")
    except Exception as e:
        print(f"[Bandai] error buscando '{nombre}': {e}")
    return None


def _punk_record_to_dict(card_id: str, card: dict) -> dict:
    keywords = card.get("keywords") or []
    return {
        "id": card_id,
        "name": html.unescape(card.get("name", "")),
        "type": card.get("category", ""),
        "cost": card.get("cost"),
        "power": card.get("power"),
        "counter": card.get("counter"),
        "color": "/".join(card.get("colors") or []),
        "rarity": card.get("rarity", ""),
        "attribute": ", ".join(card.get("attributes") or []) or None,
        "feature": ", ".join(card.get("types") or []) or None,
        "effect": f"[{', '.join(keywords)}]" if keywords else None,
        "_source": "punk-records (sin efecto completo)",
    }


async def buscar_carta_punk_records(
    nombre: str, card_id: str | None = None
) -> list[dict] | None:
    """
    Fallback para /carta cuando Bandai no responde.
    Si se provee card_id, hace lookup O(1) exacto.
    De lo contrario busca por nombre (coincidencia parcial).
    """
    index = await _load_cards_index()
    if not index:
        return None

    # Lookup directo por ID (exacto, sin ambigüedad)
    if card_id:
        # Normalizar: ignorar sufijos de arte alternativa
        base_id = re.sub(r"_(p|r)\d+$", "", card_id)
        if base_id in index:
            return [_punk_record_to_dict(base_id, index[base_id])]

    nombre_lower = nombre.lower().strip()
    matches: list[tuple[str, dict]] = []

    for cid, card in index.items():
        if re.search(r"_(p|r)\d+$", cid):
            continue
        if nombre_lower in card.get("name", "").lower():
            matches.append((cid, card))

    if not matches:
        return None

    matches.sort(key=lambda x: _set_sort_key(x[0]))
    return [_punk_record_to_dict(cid, card) for cid, card in matches[:5]]


def _parse_type_hints(query: str) -> tuple[str | None, str]:
    """
    Extrae un hint de tipo del inicio del query.
    "evento luffy" → ("Event", "luffy")
    "lider" → ("Leader", "")
    "personaje nami" → ("Character", "nami")
    """
    words = query.lower().strip().split()
    if not words:
        return None, query
    type_filter = _TYPE_KEYWORD_MAP.get(words[0])
    if type_filter:
        return type_filter, " ".join(words[1:])
    return None, query


def _parse_color_hints(nombre: str) -> tuple[list[str], str]:
    """
    Extrae hints de color del nombre y devuelve (colores_filtro, nombre_limpio).
    Ej: "Green Luffy" → (["Green"], "luffy")
    """
    _QUERY_COLOR_MAP = {
        "red": "Red", "rojo": "Red",
        "blue": "Blue", "azul": "Blue",
        "green": "Green", "verde": "Green",
        "purple": "Purple", "purpura": "Purple", "púrpura": "Purple",
        "black": "Black", "negro": "Black",
        "yellow": "Yellow", "amarillo": "Yellow",
    }
    words = nombre.lower().strip().split()
    query_colors = [_QUERY_COLOR_MAP[w] for w in words if w in _QUERY_COLOR_MAP]
    name_clean = " ".join(w for w in words if w not in _QUERY_COLOR_MAP).strip()
    return query_colors, (name_clean or nombre.lower().strip())


async def buscar_lideres_por_nombre(nombre: str) -> list[dict]:
    """
    Devuelve TODOS los líderes que coincidan con el nombre (hasta 6),
    ordenados del más reciente al más antiguo.
    Soporta hints de color: "Green Luffy" filtra a líderes con color Green.
    El prompt de deck.py le pasa esta lista a Claude para que elija el más meta-relevante.
    """
    index = await _load_cards_index()
    if not index:
        return []

    query_colors, name_clean = _parse_color_hints(nombre)

    matches: list[tuple[str, dict]] = []
    for card_id, card in index.items():
        if card.get("category") != "Leader":
            continue
        if re.search(r"_(p|r)\d+$", card_id):
            continue
        card_name = card.get("name", "").lower()
        if name_clean not in card_name:
            continue
        if query_colors:
            card_colors = set(card.get("colors") or [])
            if not any(qc in card_colors for qc in query_colors):
                continue
        matches.append((card_id, card))

    if not matches:
        return []

    matches.sort(key=lambda x: _set_sort_key(x[0]))

    result: list[dict] = []
    for card_id, card in matches[:6]:
        result.append({
            "id": card_id,
            "name": html.unescape(card.get("name", "")),
            "colors": card.get("colors") or [],
            "color": "/".join(card.get("colors") or []),
            "type": "LEADER",
        })
    return result


async def buscar_lider_por_nombre(nombre: str) -> dict | None:
    """Devuelve el líder más reciente. Wrapper de buscar_lideres_por_nombre."""
    leaders = await buscar_lideres_por_nombre(nombre)
    return leaders[0] if leaders else None


# ── Búsqueda por color (punk-records → fallback Bandai) ───────────────────


async def buscar_cartas_por_color(
    colores: list[str], limite: int = 40
) -> list[dict] | None:
    """
    Busca cartas reales por color(es).
    Usa punk-records (datos locales/GitHub) con fallback al scraper de Bandai.
    """
    index = await _load_cards_index()

    if not index:
        # Fallback: scraper Bandai
        return await _buscar_cartas_bandai_color(colores, limite)

    # Normalizar colores
    normalized: set[str] = {
        _COLOR_MAP.get(c.lower().strip(), c.capitalize()) for c in colores
    }

    candidates: list[tuple[str, dict]] = []
    seen_names: set[str] = set()

    for card_id, card in index.items():
        # Ignorar artes alternativas (OP15-001_p1, OP15-001_r1, etc.)
        if re.search(r"_(p|r)\d+$", card_id):
            continue
        # Solo cartas jugables (no Don!!, no Líder en el pool)
        if card.get("category") in ("Don", "Leader"):
            continue
        # Verificar que el color coincide
        card_colors: set[str] = set(card.get("colors") or [])
        if not card_colors & normalized:
            continue
        # Deduplicar por nombre
        name = card.get("name", "")
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        candidates.append((card_id, card))

    if not candidates:
        return None

    # Ordenar: sets más recientes primero
    candidates.sort(key=lambda x: _set_sort_key(x[0]))

    result: list[dict] = []
    for card_id, card in candidates[:limite]:
        # Filtrar solo los keywords jugables más relevantes
        all_kw: list[str] = card.get("keywords") or []
        key_kw = [k for k in all_kw if k in ("Rush", "Blocker", "Trigger")]
        result.append(
            {
                "id": card_id,
                "name": card.get("name", ""),
                "type": card.get("category", ""),
                "cost": card.get("cost"),
                "power": card.get("power"),
                "counter": card.get("counter"),
                "color": "/".join(card.get("colors") or []),
                "rarity": card.get("rarity", ""),
                "keywords": key_kw,
            }
        )

    return result or None


async def _buscar_cartas_bandai_color(
    colores: list[str], limite: int = 40
) -> list[dict] | None:
    """Fallback: scraper de Bandai para búsqueda por color."""
    url = "https://en.onepiece-cardgame.com/cardlist/"
    params = [("search", "true")]
    for c in colores:
        normalized = _COLOR_MAP.get(c.lower().strip(), c.capitalize())
        params.append(("color[]", normalized))
    try:
        async with aiohttp.ClientSession(headers=_BANDAI_HEADERS) as session:
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    cards = _parse_onepiece_html(html)
                    non_leaders = [
                        c for c in cards if c.get("type", "").upper() != "LEADER"
                    ]
                    return non_leaders[:limite] if non_leaders else None
    except Exception as e:
        print(f"⚠️ Error scraping Bandai por color: {e}")
    return None


async def autocomplete_cartas(query: str) -> list[tuple[str, str]]:
    """
    Devuelve hasta 25 cartas para autocomplete de Discord.
    Soporta filtros por tipo: "evento luffy", "lider", "personaje nami", "escenario".
    El value incluye el ID para lookup exacto: "OP15-023|Nami".
    """
    index = await _load_cards_index()
    if not index:
        return []

    type_filter, name_query = _parse_type_hints(query)
    query_lower = name_query.lower().strip()

    matches: list[tuple[str, dict]] = []

    for card_id, card in index.items():
        if re.search(r"_(p|r)\d+$", card_id):
            continue
        if card.get("category") == "Don":
            continue
        if type_filter and card.get("category") != type_filter:
            continue
        card_name = card.get("name", "").lower()
        if query_lower and query_lower not in card_name:
            continue
        matches.append((card_id, card))

    if not matches:
        return []

    matches.sort(key=lambda x: _set_sort_key(x[0]))

    result: list[tuple[str, str]] = []

    for card_id, card in matches:
        name     = html.unescape(card.get("name", ""))
        color    = "/".join(card.get("colors") or [])
        category = card.get("category", "")
        cost     = card.get("cost")
        type_es  = _TYPE_LABEL_ES.get(category, category)

        cost_str = f" c:{cost}" if cost is not None else ""
        label = f"{name} [{color}]{cost_str} — {card_id} {type_es}"
        # Value incluye el ID para que el comando haga lookup exacto
        value = f"{card_id}|{name}"

        result.append((label[:100], value[:100]))
        if len(result) >= 25:
            break

    return result


async def obtener_precio_onepiece(card_id: str) -> dict | None:
    return None


async def autocomplete_lideres(query: str) -> list[tuple[str, str]]:
    """
    Devuelve hasta 25 líderes que coincidan con el query para autocomplete de Discord.
    Retorna lista de (label_para_mostrar, value_para_usar).
    """
    index = await _load_cards_index()
    if not index:
        return []

    query_colors, name_clean = _parse_color_hints(query)
    query_lower = name_clean.lower().strip()

    matches: list[tuple[str, dict]] = []
    for card_id, card in index.items():
        if card.get("category") != "Leader":
            continue
        if re.search(r"_(p|r)\d+$", card_id):
            continue
        card_name = card.get("name", "").lower()
        if query_lower and query_lower not in card_name:
            continue
        if query_colors:
            card_colors = set(card.get("colors") or [])
            if not any(qc in card_colors for qc in query_colors):
                continue
        matches.append((card_id, card))

    if not matches:
        return []

    matches.sort(key=lambda x: _set_sort_key(x[0]))

    result: list[tuple[str, str]] = []
    seen_labels: set[str] = set()
    for card_id, card in matches:
        color = "/".join(card.get("colors") or [])
        name  = html.unescape(card.get("name", ""))
        label = f"{name} [{color}] — {card_id}"
        value = f"{name} {color}"  # incluye color para que buscar_lideres filtre bien
        if label not in seen_labels:
            seen_labels.add(label)
            result.append((label[:100], value[:100]))
        if len(result) >= 25:
            break

    return result
