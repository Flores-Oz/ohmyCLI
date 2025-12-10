# src/mycli/main.py
import sys
import argparse
import json
from pathlib import Path

# Import loader (compatibilizado en config.py)
from .config import load_config, ConfigError

# Comandos (cada módulo debe exponer register_parser(subparsers) y run(args, cfg))
from .commands import who_old, who_new, notes
from .banner import print_banner

COMMAND_MODULES = [who_old, who_new, notes]
COMMAND_HELP = {
    "who-old": "Navegar Doctor Who Clásico",
    "who-new": "Navegar Doctor Who",
    "notes": "Notas (add/list/view/del)",
}

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='mycli',
        description='Doctor Who y Notas',
        add_help=False,
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='cmd')

    for mod in COMMAND_MODULES:
        # cada módulo debe exponer register_parser(subparsers)
        mod.register_parser(subparsers)

    # argumentos globales (help manual)
    parser.add_argument('-h', '--help', action='store_true', help='Mostrar este help personalizado')
    parser.add_argument('--config', help='Archivo config.json (sobrescribe búsqueda por defecto)')
    parser.add_argument('--player', help='Comando/ejecutable para reproducir vídeos (sobrescribe config)')
    return parser

def print_custom_help() -> None:
    """Imprime help breve y limpio en el formato pedido por el usuario."""
    cmds = ",".join(sorted(COMMAND_HELP.keys()))
    print("CLI simple para Doctor Who y Notas {" + cmds + "}")
    for name in sorted(COMMAND_HELP.keys()):
        print(f"{name.ljust(10)} {COMMAND_HELP[name]}")

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Banner solo cuando no hay argumentos
    if len(argv) == 0:
        try:
            print_banner()
        except Exception:
            pass

    parser = build_parser()
    args = parser.parse_args(argv)

    # Mostrar help personalizado si se solicita
    if getattr(args, 'help', False):
        print_custom_help()
        return

    # Cargar configuración (load_config apunta a load_global_config por compatibilidad)
    try:
        cfg = load_config()
    except ConfigError as e:
        print("Error cargando configuración global:")
        print(e)
        return
    except Exception as e:
        print("Error inesperado cargando configuración:")
        print(e)
        return

    # Mostrar de dónde vino la config (si el loader lo reporta)
    try:
        src = cfg.get("config_source")
        if src:
            print("Cargando config desde:", src)
    except Exception:
        pass

    # Override con --config (archivo específico)
    if getattr(args, 'config', None):
        try:
            override_path = Path(args.config)
            override_text = override_path.read_text(encoding='utf-8')
            cfg.update(json.loads(override_text))
            print(f"Config override cargada desde: {override_path}")
        except Exception as ex:
            print(f"Error cargando config {args.config}: {ex}")

    # Override player desde CLI
    if getattr(args, 'player', None):
        cfg['player_cmd'] = args.player

    # Si no hay subcomando, imprimimos help minimal
    if args.cmd is None:
        print_custom_help()
        return

    # Despachar al comando correcto
    for mod in COMMAND_MODULES:
        name = mod.__name__.split('.')[-1]
        if args.cmd == name.replace('_', '-'):
            mod.run(args, cfg)
            return

    print("Comando no reconocido.")

## python -m pip install --user pipx
## python -m pipx ensurepath
## pipx uninstall ohmycli
## pipx install .