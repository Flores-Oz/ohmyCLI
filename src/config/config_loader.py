import json
from pathlib import Path
from typing import Any, Dict, Optional

REQUIRED_KEYS = ["who_classic_path", "who_new_path", "notes_path"]


class ConfigError(Exception):
    pass


def load_local_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Carga y valida ./config.json por defecto.
    - Verifica que existan las claves requeridas y que sean strings.
    - Si create_notes_if_missing==true y notes_path no existe, la crea.
    - Lanza ConfigError con mensaje claro si algo falla.
    """
    if config_path is None:
        config_path = Path.cwd() / "config.json"
    else:
        config_path = Path(config_path)

    config_path = config_path.expanduser()

    if not config_path.exists():
        raise ConfigError(f"Config no encontrada en: {config_path}")

    try:
        text = config_path.read_text(encoding="utf-8")
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ConfigError(f"JSON inválido en {config_path}: {e}")
    except Exception as e:
        raise ConfigError(f"Error leyendo {config_path}: {e}")

    # Validar claves obligatorias
    for key in REQUIRED_KEYS:
        if key not in data:
            raise ConfigError(f"Falta clave obligatoria en config: '{key}'")
        if not isinstance(data[key], str) or data[key].strip() == "":
            raise ConfigError(f"Clave '{key}' debe ser una cadena no vacía")

    # Campos opcionales
    create_notes = data.get("create_notes_if_missing", True)
    # Aceptar 'true'/'false' string? nos ceñimos a bool o cast seguro:
    if isinstance(create_notes, str):
        create_notes = create_notes.lower() in ("1", "true", "yes", "y")
    else:
        create_notes = bool(create_notes)

    player_cmd = data.get("player_cmd")
    if isinstance(player_cmd, str) and player_cmd.strip() == "":
        player_cmd = None
    elif player_cmd is not None:
        player_cmd = str(player_cmd)

    # Normalizar paths
    who_classic = Path(data["who_classic_path"]).expanduser()
    who_new = Path(data["who_new_path"]).expanduser()
    notes = Path(data["notes_path"]).expanduser()

    # Opcional: resolver rutas relativas respecto al config file
    # si las rutas son relativas, interpretarlas respecto al directorio del config
    cfg_dir = config_path.parent
    if not who_classic.is_absolute():
        who_classic = (cfg_dir / who_classic).resolve()
    if not who_new.is_absolute():
        who_new = (cfg_dir / who_new).resolve()
    if not notes.is_absolute():
        notes = (cfg_dir / notes).resolve()

    # Comprobar existencia de who paths (advertencia — no obligatorio)
    if not who_classic.exists():
        # puedes cambiar esto a raise ConfigError si prefieres fallar
        print(f"Warning: who_classic_path no existe: {who_classic}")
    if not who_new.exists():
        print(f"Warning: who_new_path no existe: {who_new}")

    # Si create_notes_if_missing y no existe, crear
    if create_notes and not notes.exists():
        try:
            notes.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ConfigError(f"No se pudo crear notes_path '{notes}': {e}")

    # Retornar una config limpia (strings para compatibilidad con resto del código)
    return {
        "who_classic_path": str(who_classic),
        "who_new_path": str(who_new),
        "notes_path": str(notes),
        "player_cmd": player_cmd,
        "create_notes_if_missing": create_notes,
    }


if __name__ == "__main__":
    # Ejecución rápida para probar manualmente
    try:
        cfg = load_local_config()
        print("Config cargada correctamente:")
        for k, v in cfg.items():
            print(f"  {k}: {v}")
    except ConfigError as e:
        print("Error cargando config:", e)
