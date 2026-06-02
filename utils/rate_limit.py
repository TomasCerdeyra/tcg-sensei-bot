"""
Rate limiting por usuario y por comando con persistencia en SQLite.
Cada comando IA tiene su propio contador diario independiente.
Si SQLite falla (permisos, disco lleno), hace fallback a memoria en RAM.
"""
import os
import sqlite3
from collections import defaultdict
from datetime import date, datetime
from config import AI_DAILY_LIMIT, MAZO_DAILY_LIMIT

_DB_PATH = "data/rate_limit.db"

# Límites por comando
_LIMITES: dict[str, int] = {
    "coach":   AI_DAILY_LIMIT,
    "mazo":    MAZO_DAILY_LIMIT,
    "matchup": AI_DAILY_LIMIT,
    "regla":   AI_DAILY_LIMIT,
    "_global": AI_DAILY_LIMIT,
}

# ── Inicialización de la base de datos ───────────────────────────────────────

def _init_db() -> bool:
    """Crea la base de datos y la tabla si no existen. Retorna True si SQLite está disponible."""
    try:
        os.makedirs("data", exist_ok=True)
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    user_id  TEXT    NOT NULL,
                    command  TEXT    NOT NULL,
                    date     TEXT    NOT NULL,
                    count    INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_id, command, date)
                )
            """)
            conn.commit()
        return True
    except Exception as e:
        print(f"[rate_limit] SQLite no disponible, usando memoria RAM: {e}")
        return False


_USE_SQLITE: bool = _init_db()

# Fallback en memoria (si SQLite falla)
_memoria: dict = defaultdict(dict)


# ── Operaciones SQLite ────────────────────────────────────────────────────────

def _sqlite_get(user_id: int, comando: str, hoy: str) -> int:
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            row = conn.execute(
                "SELECT count FROM usage WHERE user_id=? AND command=? AND date=?",
                (str(user_id), comando, hoy),
            ).fetchone()
        return row[0] if row else 0
    except Exception:
        return 0


def _sqlite_increment(user_id: int, comando: str, hoy: str) -> int:
    """Incrementa el contador y devuelve el nuevo valor."""
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO usage (user_id, command, date, count) VALUES (?, ?, ?, 1)
                ON CONFLICT (user_id, command, date)
                DO UPDATE SET count = count + 1
                """,
                (str(user_id), comando, hoy),
            )
            conn.commit()
            row = conn.execute(
                "SELECT count FROM usage WHERE user_id=? AND command=? AND date=?",
                (str(user_id), comando, hoy),
            ).fetchone()
        return row[0] if row else 1
    except Exception:
        return 1


# ── API pública ───────────────────────────────────────────────────────────────

def puede_usar(user_id: int, comando: str = "_global") -> bool:
    """
    Verifica si el usuario puede hacer una consulta.
    Si puede, incrementa el contador. Si no, devuelve False sin modificar.
    """
    limite = _LIMITES.get(comando, _LIMITES["_global"])
    hoy = date.today().isoformat()

    if _USE_SQLITE:
        actual = _sqlite_get(user_id, comando, hoy)
        if actual >= limite:
            return False
        _sqlite_increment(user_id, comando, hoy)
        return True
    else:
        # Fallback en memoria
        key = (user_id, comando)
        entry = _memoria.get(key, {"fecha": None, "count": 0})
        if entry["fecha"] != hoy:
            entry = {"fecha": hoy, "count": 0}
        if entry["count"] >= limite:
            _memoria[key] = entry
            return False
        entry["count"] += 1
        _memoria[key] = entry
        return True


def get_uso(user_id: int, comando: str = "_global") -> int:
    """Devuelve la cantidad de consultas usadas hoy para ese comando."""
    hoy = date.today().isoformat()
    if _USE_SQLITE:
        return _sqlite_get(user_id, comando, hoy)
    key = (user_id, comando)
    entry = _memoria.get(key, {"fecha": None, "count": 0})
    return entry["count"] if entry["fecha"] == hoy else 0


def consultas_restantes(user_id: int, comando: str = "_global") -> int:
    """Devuelve las consultas restantes del día para ese comando."""
    limite = _LIMITES.get(comando, _LIMITES["_global"])
    return max(0, limite - get_uso(user_id, comando))


def get_uso_total(user_id: int) -> int:
    """Devuelve el total de consultas IA usadas hoy (todos los comandos)."""
    hoy = date.today().isoformat()
    if _USE_SQLITE:
        try:
            with sqlite3.connect(_DB_PATH) as conn:
                row = conn.execute(
                    "SELECT COALESCE(SUM(count),0) FROM usage WHERE user_id=? AND date=?",
                    (str(user_id), hoy),
                ).fetchone()
            return row[0] if row else 0
        except Exception:
            return 0
    return sum(
        e["count"] for (uid, _), e in _memoria.items()
        if uid == user_id and e.get("fecha") == hoy
    )
