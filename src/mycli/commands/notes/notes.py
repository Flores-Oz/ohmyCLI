# src/mycli/commands/notes.py
from pathlib import Path
import datetime
from mycli.utils import list_dirs, list_media_files, prompt_choice, open_with_default

def register_parser(subparsers):
    notes_p = subparsers.add_parser('notes', help='Notas (add/list/view/del)')
    notes_sub = notes_p.add_subparsers(dest='notes_cmd')
    notes_sub.add_parser('add', help='Agregar nota')
    notes_sub.add_parser('list', help='Listar notas')
    view_p = notes_sub.add_parser('view', help='Ver nota por índice')
    view_p.add_argument('index', type=int)
    del_p = notes_sub.add_parser('del', help='Borrar nota por índice')
    del_p.add_argument('index', type=int)
    del_p.add_argument('--yes', action='store_true', help='Confirmar borrado sin preguntar')

def run(args, cfg):
    notes_path = cfg.get('notes_path')
    if not notes_path:
        print("notes_path no configurado.")
        return
    cmd = args.notes_cmd
    if cmd == 'add':
        _add(notes_path)
    elif cmd == 'list':
        _list(notes_path)
    elif cmd == 'view':
        _view(notes_path, args.index)
    elif cmd == 'del':
        _del(notes_path, args.index, yes=args.yes)
    else:
        print("Uso: mycli notes add|list|view|del")

def _ensure_folder(p: Path, create_if_missing=True):
    if not p.exists():
        if create_if_missing:
            p.mkdir(parents=True, exist_ok=True)
            print(f"Carpeta de notas creada en: {p}")
            return True
        else:
            print(f"Carpeta de notas no existe: {p}")
            return False
    return True

def _add(notes_path):
    p = Path(notes_path)
    if not _ensure_folder(p, create_if_missing=True):
        return
    print("Escribe tu nota. Termina con una línea que contenga solo un punto '.' y presiona Enter.")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == '.':
            break
        lines.append(line)
    content = '\n'.join(lines).strip()
    if not content:
        ans = input("Nota vacía. ¿Deseas guardarla? (y/N): ").strip().lower()
        if ans != 'y':
            print("Nota descartada.")
            return
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    fname = f"nota_{ts}.txt"
    fpath = p / fname
    fpath.write_text(content + '\n', encoding='utf-8')
    print(f"Nota guardada en: {fpath}")

def _list(notes_path):
    p = Path(notes_path)
    if not _ensure_folder(p, create_if_missing=False):
        return
    files = sorted([f for f in p.iterdir() if f.is_file()])
    if not files:
        print("No hay notas.")
        return
    for i, f in enumerate(files, 1):
        mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{i}] {f.name} ({mtime})")

def _view(notes_path, index):
    p = Path(notes_path)
    if not _ensure_folder(p, create_if_missing=False):
        return
    files = sorted([f for f in p.iterdir() if f.is_file()])
    if index < 1 or index > len(files):
        print("Índice fuera de rango.")
        return
    print(f"=== {files[index-1].name} ===")
    print(files[index-1].read_text(encoding='utf-8'))

def _del(notes_path, index, yes=False):
    p = Path(notes_path)
    if not _ensure_folder(p, create_if_missing=False):
        return
    files = sorted([f for f in p.iterdir() if f.is_file()])
    if index < 1 or index > len(files):
        print("Índice fuera de rango.")
        return
    target = files[index-1]
    if not yes:
        ans = input(f"¿Eliminar {target.name}? (y/N): ").strip().lower()
        if ans != 'y':
            print("Operación cancelada.")
            return
    target.unlink()
    print(f"{target.name} eliminado.")
