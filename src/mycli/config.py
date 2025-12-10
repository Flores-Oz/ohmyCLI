# src/mycli/config.py
from pathlib import Path
import json
import os
from typing import Dict, Any, Optional

GLOBAL_CONFIG_PATH = Path.home() / ".ohmycli" / "config.json"
REQUIRED_KEYS = ["who_classic_path", "who_new_path", "notes_path"]

class ConfigError(RuntimeError):
    """Excepción levantada cuando la configuración es inválida o no encontrada."""
    pass

def _ensure_folder(path: Path, create: bool = True) -> None:
    """Asegura que exista la carpeta; la crea si create=True."""
    if not path.exists():
        if create:
            path.mkdir(parents=True, exist_ok=True)
        else:
            raise ConfigError(f"La carpeta no existe y no se permite crearla: {path}")

def _safe_resolve(p: Path) -> str:
    """Resuelve una Path a absolute sin fallar si la ruta no existe (resolve strict=False)."""
    try:
        return str(p.resolve(strict=False))
    except TypeError:
        # Fallback para versiones antiguas de pathlib
        return str(p.absolute())

def load_global_config() -> Dict[str, Any]:
    """
    Carga exclusivamente ~/.ohmycli/config.json.
    Si no existe lanza ConfigError con mensaje claro.
    Crea notes_path si create_notes_if_missing == true.
    """
    cfg_file = GLOBAL_CONFIG_PATH

    if not cfg_file.exists():
        raise ConfigError(
            f"No existe el archivo de configuración global:\n  {cfg_file}\n"
            "Crea uno con las claves obligatorias (who_classic_path, who_new_path, notes_path)."
        )

    try:
        raw = cfg_file.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSON inválido en {cfg_file}: {e}")
    except Exception as e:
        raise ConfigError(f"Error leyendo {cfg_file}: {e}")

    # Validar claves mínimas
    for key in REQUIRED_KEYS:
        if key not in data or not str(data[key]).strip():
            raise ConfigError(f"Config inválida: falta el campo obligatorio '{key}'")

    # Expandir rutas (sin resolver estrictamente)
    who_classic = Path(data["who_classic_path"]).expanduser()
    who_new = Path(data["who_new_path"]).expanduser()
    notes = Path(data["notes_path"]).expanduser()

    # Crear carpeta de notas si se permite
    create_notes = bool(data.get("create_notes_if_missing", True))
    _ensure_folder(notes, create=create_notes)

    player_cmd = data.get("player_cmd")
    state_path_raw = data.get("state_path")

    return {
        "who_classic_path": _safe_resolve(who_classic),
        "who_new_path": _safe_resolve(who_new),
        "notes_path": _safe_resolve(notes),
        "player_cmd": player_cmd,
        "create_notes_if_missing": create_notes,
        "state_path": _safe_resolve(Path(state_path_raw).expanduser()) if state_path_raw else None,
        "config_source": str(cfg_file),
    }

# Alias para compatibilidad con código que importe `load_config`
load_config = load_global_config

__all__ = [
    "GLOBAL_CONFIG_PATH",
    "load_global_config",
    "load_config",
    "ConfigError",
]
