# src/mycli/main.py
import sys
import argparse
import json
from pathlib import Path
from .config import load_config
from .commands import who_old, who_new, notes
from mycli.banner import print_banner

COMMAND_MODULES = [who_old, who_new, notes]


def build_parser():
    parser = argparse.ArgumentParser(prog='mycli', description='CLI simple para Doctor Who y notas')
    subparsers = parser.add_subparsers(dest='cmd')
    for mod in COMMAND_MODULES:
        mod.register_parser(subparsers)
    parser.add_argument('--config', help='Archivo config.json (sobrescribe búsqueda por defecto)')
    parser.add_argument('--player', help='Comando/ejecutable para reproducir vídeos (sobrescribe config)')
    return parser


def main(argv=None):
    # Normalizar argv para que siempre sea una lista (útil en tests)
    if argv is None:
      argv = sys.argv[1:]

    # Mostrar banner *solo* si no hay argumentos (ejecución: `ohmycli`)
    if len(argv) == 0:
        try:
            print_banner()
        except Exception:
            # no queremos que un fallo en el banner impida ejecutar el CLI
            pass

    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = load_config()
    if getattr(args, 'config', None):
        try:
            override_path = Path(args.config)
            cfg.update(json.loads(override_path.read_text(encoding='utf-8')))
        except Exception as ex:
            print(f"Error cargando config {args.config}: {ex}")
    if getattr(args, 'player', None):
        cfg['player_cmd'] = args.player

    if args.cmd is None:
        parser.print_help()
        return

    for mod in COMMAND_MODULES:
        name = mod.__name__.split('.')[-1]
        if args.cmd == name.replace('_', '-'):
            mod.run(args, cfg)
            return

    print("Comando no reconocido.")
