# src/mycli/main.py
import sys
import argparse
import json
from pathlib import Path
from .config import load_config
from .commands import who_old, who_new, notes
from mycli.banner import print_banner

# Lista de módulos de comando y su descripción corta (usada para imprimir el help)
COMMAND_MODULES = [who_old, who_new, notes]
# Mapeo manual de ayuda para mostrar en el formato exacto que quieres
COMMAND_HELP = {
    "who-old": "Navegar Doctor Who Clásico",
    "who-new": "Navegar Doctor Who",
    "notes": "Notas (add/list/view/del)",
}

def build_parser():
    # Deshabilitamos el help automático y dejamos un -h/--help manual
    parser = argparse.ArgumentParser(
        prog='mycli',
        description='Doctor Who y Notas',
        add_help=False,  # desactivamos help automático para controlar la salida
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='cmd')

    # Registrar parsers de los módulos (siguen necesitando register_parser)
    for mod in COMMAND_MODULES:
        mod.register_parser(subparsers)

    # argumentos globales (incluimos -h/--help manual)
    parser.add_argument('-h', '--help', action='store_true', help='Mostrar este help personalizado')
    parser.add_argument('--config', help='Archivo config.json (sobrescribe búsqueda por defecto)')
    parser.add_argument('--player', help='Comando/ejecutable para reproducir vídeos (sobrescribe config)')
    return parser

def print_custom_help():
    """Imprime el help exactamente en el formato pedido por el usuario."""
    cmds = ",".join(sorted(COMMAND_HELP.keys()))
    # Primera línea (descripción + listado corto)
    print("CLI simple para Doctor Who y Notas {" + cmds + "}")
    # Luego cada comando en su propia línea con su descripción
    for name in sorted(COMMAND_HELP.keys()):
        # Alineado simple: comando padded a 10 chars
        print(f"{name.ljust(10)} {COMMAND_HELP[name]}")

def main(argv=None):
    # Normalizar argv para que siempre sea una lista (útil en tests)
    if argv is None:
        argv = sys.argv[1:]

    # Mostrar banner *solo* si no hay argumentos (ejecución: `ohmycli`)
    if len(argv) == 0:
        try:
            print_banner()
        except Exception:
            pass  # no queremos romper el CLI si el banner falla

    parser = build_parser()
    args = parser.parse_args(argv)

    # Si piden help, imprimimos nuestro help personalizado
    if getattr(args, 'help', False):
        print_custom_help()
        return

    cfg = load_config()
    if getattr(args, 'config', None):
        try:
            override_path = Path(args.config)
            cfg.update(json.loads(override_path.read_text(encoding='utf-8')))
        except Exception as ex:
            print(f"Error cargando config {args.config}: {ex}")
    if getattr(args, 'player', None):
        cfg['player_cmd'] = args.player

    # Si no se especificó subcomando mostramos el mismo help minimal
    if args.cmd is None:
        print_custom_help()
        return

    # Despachar al subcomando correspondiente
    for mod in COMMAND_MODULES:
        name = mod.__name__.split('.')[-1]
        if args.cmd == name.replace('_', '-'):
            mod.run(args, cfg)
            return

    print("Comando no reconocido.")
