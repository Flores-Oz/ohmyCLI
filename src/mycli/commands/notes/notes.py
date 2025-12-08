# src/mycli/commands/notes.py
from pathlib import Path
import datetime
import tempfile
import os
import subprocess
from typing import Optional

def register_parser(subparsers):
    notes_p = subparsers.add_parser('notes', help='Notas (add/list/view/del/edit)')
    notes_sub = notes_p.add_subparsers(dest='notes_cmd')
    add_p = notes_sub.add_parser('add', help='Agregar nota')
    add_p.add_argument('--name', '-n', help='Nombre de archivo (sin extensión), opcional')
    notes_sub.add_parser('list', help='Listar notas')
    view_p = notes_sub.add_parser('view', help='Ver nota por índice')
    view_p.add_argument('index', type=int)
    edit_p = notes_sub.add_parser('edit', help='Editar nota por índice')
    edit_p.add_argument('index', type=int)
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
        _add(notes_path, name=getattr(args, 'name', None))
    elif cmd == 'list':
        _list(notes_path)
    elif cmd == 'view':
        _view(notes_path, args.index)
    elif cmd == 'edit':
        _edit(notes_path, args.index)
    elif cmd == 'del':
        _del(notes_path, args.index, yes=args.yes)
    else:
        print("Uso: mycli notes add|list|view|edit|del")

# ---------- helpers ----------
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

def _safe_filename(name: str) -> str:
    # Normalizar nombre simple: quitar slashes, trim
    name = name.strip()
    name = name.replace('/', '_').replace('\\', '_')
    # si queda vacío, devolver None
    return name if name else None

# ---------- add ----------
def _add(notes_path, name: Optional[str] = None):
    p = Path(notes_path)
    if not _ensure_folder(p, create_if_missing=True):
        return

    # solicitar nombre si no viene por flag
    fname = None
    if name:
        safe = _safe_filename(name)
        if safe:
            fname = safe if safe.endswith(".txt") else f"{safe}.txt"
    else:
        ans = input("¿Deseas elegir un nombre de archivo para la nota? (y/N): ").strip().lower()
        if ans == 'y':
            entrada = input("Nombre (sin extensión): ").strip()
            safe = _safe_filename(entrada)
            if safe:
                fname = safe if safe.endswith(".txt") else f"{safe}.txt"

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
    if not fname:
        fname = f"nota_{ts}.txt"
    fpath = p / fname
    # si existe, preguntar si sobrescribir (evitar pisar)
    if fpath.exists():
        ans2 = input(f"El archivo {fpath.name} ya existe. ¿Sobrescribir? (y/N): ").strip().lower()
        if ans2 != 'y':
            print("Guardado cancelado.")
            return
    fpath.write_text(content + '\n', encoding='utf-8')
    print(f"Nota guardada en: {fpath}")

# ---------- list ----------
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

# ---------- view ----------
def _view(notes_path, index):
    p = Path(notes_path)
    if not _ensure_folder(p, create_if_missing=False):
        return
    files = sorted([f for f in p.iterdir() if f.is_file()])
    if index < 1 or index > len(files):
        print("Índice fuera de rango.")
        return
    target = files[index-1]
    print(f"=== {target.name} ===")
    print(target.read_text(encoding='utf-8'))

# ---------- edit ----------
def _edit(notes_path, index):
    p = Path(notes_path)
    if not _ensure_folder(p, create_if_missing=False):
        return
    files = sorted([f for f in p.iterdir() if f.is_file()])
    if index < 1 or index > len(files):
        print("Índice fuera de rango.")
        return
    target = files[index-1]
    # Preferir editor externo
    editor = os.environ.get('EDITOR')
    if not editor and os.name == 'nt':
        editor = 'notepad'  # fallback Windows
    if editor:
        # abrir temp copy para editar y luego mover a origen si cambió
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp", mode='w', encoding='utf-8') as tf:
            tf_name = tf.name
            tf.write(target.read_text(encoding='utf-8'))
        try:
            subprocess.run([editor, tf_name])
        except Exception as ex:
            print(f"No pude abrir el editor '{editor}': {ex}")
            # caemos a modo inline
            _edit_inline(target)
            try:
                os.unlink(tf_name)
            except Exception:
                pass
            return
        # después de editar, leer el temp y reemplazar
        new_content = Path(tf_name).read_text(encoding='utf-8')
        Path(tf_name).unlink(missing_ok=True)
        if new_content == target.read_text(encoding='utf-8'):
            print("No hubo cambios.")
            return
        target.write_text(new_content, encoding='utf-8')
        print(f"{target.name} actualizado.")
        return
    else:
        # editor no disponible -> modo inline
        _edit_inline(target)

def _edit_inline(target: Path):
    print(f"Editando (inline) {target.name}. Se mostrará contenido actual y podrás reescribirlo.")
    print("=== CONTENIDO ACTUAL ===")
    print(target.read_text(encoding='utf-8'))
    print("=== INGRESA NUEVO CONTENIDO. Termina con '.' en línea sola ===")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == '.':
            break
        lines.append(line)
    new = '\n'.join(lines).strip()
    if not new:
        ans = input("El nuevo contenido está vacío. ¿Deseas cancelar la edición? (y/N): ").strip().lower()
        if ans != 'y':
            target.write_text(new + '\n', encoding='utf-8')
            print(f"{target.name} actualizado (vacío).")
        else:
            print("Edición cancelada.")
        return
    target.write_text(new + '\n', encoding='utf-8')
    print(f"{target.name} actualizado.")

# ---------- delete ----------
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
