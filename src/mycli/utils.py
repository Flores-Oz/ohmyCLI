import os
import sys
import subprocess
from pathlib import Path

VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.mpg', '.mpeg'}

def list_dirs(path):
    try:
        entries = [e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e))]
        entries.sort()
        return entries
    except Exception as ex:
        print(f"Error leyendo '{path}': {ex}")
        return []

def list_media_files(path):
    try:
        files = [f for f in os.listdir(path)
                 if os.path.isfile(os.path.join(path, f)) and Path(f).suffix.lower() in VIDEO_EXTS]
        files.sort()
        return files
    except Exception as ex:
        print(f"Error leyendo archivos en '{path}': {ex}")
        return []

def prompt_choice(max_n, prompt_text="Selecciona una opción"):
    while True:
        try:
            s = input(f"{prompt_text} [1-{max_n}] (q para salir): ").strip()
            if s.lower() == 'q':
                return None
            n = int(s)
            if 1 <= n <= max_n:
                return n - 1
            else:
                print("Número fuera de rango.")
        except ValueError:
            print("Entrada inválida. Ingresa un número.")

def open_with_default(path, player_cmd=None):
    try:
        if player_cmd:
            subprocess.Popen([player_cmd, path])
        else:
            if sys.platform.startswith('win'):
                os.startfile(path)
            elif sys.platform.startswith('darwin'):
                subprocess.Popen(['open', path])
            else:
                subprocess.Popen(['xdg-open', path])
    except Exception as ex:
        print(f"No pude abrir '{path}': {ex}")
