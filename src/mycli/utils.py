import os
import sys
import subprocess
import re
import unicodedata
from pathlib import Path
from typing import List, Tuple
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

VIDEO_EXTS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.mpg', '.mpeg', '.flv', '.webm'}

def list_dirs(path):
    try:
        entries = [e for e in os.listdir(path) if os.path.isdir(os.path.join(path, e))]
        entries.sort()
        return entries
    except Exception as ex:
        print(f"Error leyendo '{path}': {ex}")
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


# --- normalización de nombres ---
def _norm_name(s: str) -> str:
    """Normaliza string: unicode -> ascii, minusculas, quitar puntos/guiones, multiples espacios."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.replace('.', ' ').replace('_', ' ').replace('-', ' ')
    s = re.sub(r'\s+', ' ', s).strip().lower()
    return s

# --- heurística para detectar 'temporada' o 'doctor N' ---
DOCTOR_KEYWORDS = [
    r'\bdoctor\b', r'\bdr\b', r'\bwho\b',
    # numerales y sufijos comunes: 1, 10, 10th, 10mo, 10º, decimo, décimo
    r'\b\d+(?:st|nd|rd|th|mo|º)?\b',
    r'\bdecim[oa]\b', r'\btenth\b', r'\bprimer\b', r'\bsegund[oa]\b'
]

DOCTOR_RE = re.compile("|".join(DOCTOR_KEYWORDS), re.IGNORECASE)

def looks_like_season_dir(name: str) -> bool:
    """Detecta si un nombre sugiere temporada/doctor/volumen."""
    n = _norm_name(name)
    # si contiene 'doctor' o 'who' y además alguna pista numérica, es muy probable
    if 'doctor' in n or 'who' in n or 'dr' in n:
        # si hay número u ordinal
        if re.search(r'\b\d+\b', n) or re.search(r'\b(decimo|tenth|10mo|10º|10th)\b', n):
            return True
        # si el nombre contiene "season" o "temporada"
        if re.search(r'\bseason\b|\btemporada\b|\btemporad\b', n):
            return True
        # si solo es "octavo doctor" también cuenta
        if re.search(r'\bprimer\b|\bsegund[ao]\b|\btercer\b|\bcuart[ao]\b|\bquint[ao]\b|\bsext[ao]\b|\bseptim[ao]\b|\boctav[ao]\b|\bnoven[ao]\b|\bdecim[ao]\b', n):
            return True
    # fallback: si contiene 'season' o 'temporada' aunque no tenga doctor
    if re.search(r'\bseason\b|\btemporada\b', n):
        return True
    return False

# --- listar archivos multimedia en una carpeta (no recursivo) ---
def list_media_files(path: Path) -> List[Path]:
    try:
        return sorted([p for p in path.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_EXTS])
    except Exception:
        return []

# --- detectar temporadas dentro de un base path ---
def detect_season_dirs(base_path: Path, max_depth: int = 2) -> List[Tuple[Path, str, int]]:
    """
    Busca carpetas candidatas que parezcan 'temporadas' bajo base_path.
    Retorna lista de (path, display_name, score) ordenada por score descendente.
    score heurístico: +20 si contiene videos directos, +10 si nombre sugiere temporada, +5 si subcarpetas contienen videos.
    max_depth controla cuánto profundiza (1 = solo hijos directos; 2 = hijos y nietos).
    """
    base = Path(base_path)
    if not base.exists():
        return []

    candidates = []
    # buscamos en árbol hasta profundidad max_depth
    def walk_dir(p: Path, depth: int):
        if depth > max_depth:
            return
        # comprobar si esta carpeta contiene videos directos
        media = list_media_files(p)
        score = 0
        if media:
            score += 20
        # comprobar nombre
        if looks_like_season_dir(p.name):
            score += 10
        # revisar subcarpetas si depth < max_depth
        sub_has_media = False
        if depth < max_depth:
            for sd in [d for d in p.iterdir() if d.is_dir()]:
                if list_media_files(sd):
                    sub_has_media = True
                    break
                # mirar un nivel más si allowed
                if depth + 1 <= max_depth:
                    for ssd in [d for d in sd.iterdir() if d.is_dir()]:
                        if list_media_files(ssd):
                            sub_has_media = True
                            break
                if sub_has_media:
                    break
        if sub_has_media:
            score += 5

        # solo añadir si hay alguna pista (videos directos o subcarpetas con videos o nombre sugerente)
        if score > 0:
            # display name: preferir nombre normalizado pero legible
            display = p.name
            candidates.append((p, display, score))

        # continuar recursión (solo si depth < max_depth)
        if depth < max_depth:
            for d in [d for d in p.iterdir() if d.is_dir()]:
                # evitar entrar en carpetas ocultas / system
                if d.name.startswith('.'):
                    continue
                walk_dir(d, depth + 1)

    # iniciar en hijos directos de base (no en base mismo para evitar duplicados)
    for child in [c for c in base.iterdir() if c.is_dir()]:
        walk_dir(child, 1)

    # También considerar base itself if it contains media (ej. Dr.Who/10mo Doctor/ podría ser base)
    if list_media_files(base):
        candidates.insert(0, (base, base.name, 25))

    # ordenar por score descendente y por nombre
    candidates = sorted(candidates, key=lambda t: (-t[2], _norm_name(t[1])))

    # eliminar duplicados (mismo path)
    seen = set()
    out = []
    for p, display, score in candidates:
        if str(p) in seen:
            continue
        seen.add(str(p))
        out.append((p, display, score))
    return out

# --- obtener episodios para una temporada (plan B: si no hay archivos directos, recoger de subcarpetas) ---
def list_episodes_for_season(season_path: Path) -> List[Path]:
    """
    Retorna lista de archivos multimedia que representan episodios dentro de season_path.
    Busca archivos directos; si no hay, busca en subcarpetas (1 nivel) y los devuelve.
    """
    season_path = Path(season_path)
    files = list_media_files(season_path)
    if files:
        return files
    # buscar 1 nivel en subfolders
    episodes = []
    for sd in [d for d in season_path.iterdir() if d.is_dir()]:
        episodes.extend(list_media_files(sd))
    # ordenar por nombre
    return sorted(episodes)

def default_state_path() -> Path:
    """Ruta por defecto para el archivo de estado según plataforma."""
    home = Path.home()
    if sys.platform.startswith("win"):
        # %APPDATA%\ohmycli\watched.json
        appdata = os.getenv("APPDATA") or (home / "AppData" / "Roaming")
        return Path(appdata) / "ohmycli" / "watched.json"
    else:
        # ~/.config/ohmycli/watched.json
        return home / ".config" / "ohmycli" / "watched.json"

def ensure_state_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def load_watch_state(path: Optional[str] = None) -> Dict[str, Any]:
    """Carga el JSON de estado (path opcional). Devuelve dict vacío si no existe."""
    p = Path(path) if path else default_state_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_watch_state(state: Dict[str, Any], path: Optional[str] = None) -> None:
    """Guarda el estado en JSON (crea el directorio si hace falta)."""
    p = Path(path) if path else default_state_path()
    ensure_state_dir(p)
    p.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

def episode_key(ep_path: str) -> str:
    """Clave única para un episodio. Usamos la ruta absoluta normalizada."""
    return str(Path(ep_path).resolve())

def is_watched(ep_path: str, state: Optional[Dict[str, Any]] = None, path: Optional[str] = None) -> bool:
    if state is None:
        state = load_watch_state(path)
    return bool(state.get(episode_key(ep_path), {}).get("watched"))

def mark_watched(ep_path: str, state: Optional[Dict[str, Any]] = None, path: Optional[str] = None) -> None:
    if state is None:
        state = load_watch_state(path)
    k = episode_key(ep_path)
    state[k] = {"watched": True, "ts": datetime.utcnow().isoformat()}
    save_watch_state(state, path)

def mark_unwatched(ep_path: str, state: Optional[Dict[str, Any]] = None, path: Optional[str] = None) -> None:
    if state is None:
        state = load_watch_state(path)
    k = episode_key(ep_path)
    if k in state:
        state[k]["watched"] = False
        state[k]["ts"] = datetime.utcnow().isoformat()
        save_watch_state(state, path)

def mark_all_in_dir(dir_path: str, watched: bool = True, state: Optional[Dict[str, Any]] = None, path: Optional[str] = None) -> None:
    """Marca todos los archivos multimedia (recursivo 1 nivel) dentro de dir_path."""
    if state is None:
        state = load_watch_state(path)
    dirp = Path(dir_path)
    for f in list_media_files(dirp):
        k = episode_key(str(f))
        state[k] = {"watched": bool(watched), "ts": datetime.utcnow().isoformat()}
    # también buscar en subcarpetas 1 nivel
    for sd in [d for d in dirp.iterdir() if d.is_dir()]:
        for f in list_media_files(sd):
            k = episode_key(str(f))
            state[k] = {"watched": bool(watched), "ts": datetime.utcnow().isoformat()}
    save_watch_state(state, path)

def list_with_watch_status(episodes: list, state: Optional[Dict[str, Any]] = None, path: Optional[str] = None) -> list:
    """Devuelve lista de tuples (Path, watched:bool)."""
    if state is None:
        state = load_watch_state(path)
    out = []
    for e in episodes:
        kp = episode_key(str(e))
        watched = bool(state.get(kp, {}).get("watched", False))
        out.append((e, watched))
    return out