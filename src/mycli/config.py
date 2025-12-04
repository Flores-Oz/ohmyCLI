import os
import json
from pathlib import Path

DEFAULT_CONFIG_NAME = "config.json"

def load_config(proj_dir=None, env_prefix="MYCLI_"):
    """
    Carga (y mergea) config en este orden:
      1. config.json en el directorio de trabajo (proyecto)
      2. ~/.config/mycli/config.json (usuario)
      3. variables de entorno prefijadas MYCLI_*
    Devuelve dict.
    """
    cfg = {}
    # 1) proyecto
    if proj_dir is None:
        proj_dir = os.getcwd()
    proj_path = Path(proj_dir) / DEFAULT_CONFIG_NAME
    if proj_path.is_file():
        try:
            with proj_path.open(encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass

    # 2) usuario
    user_cfg = Path.home() / ".config" / "mycli" / DEFAULT_CONFIG_NAME
    if user_cfg.is_file():
        try:
            with user_cfg.open(encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass

    # 3) variables de entorno (p. ej. MYCLI_PLAYER_CMD)
    for k, v in os.environ.items():
        if k.startswith(env_prefix):
            key = k[len(env_prefix):].lower()
            cfg[key] = v

    return cfg
