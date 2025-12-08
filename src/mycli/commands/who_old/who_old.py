# src/mycli/commands/who_old/who_old.py
from pathlib import Path
from typing import List, Optional
import re

from mycli.utils import (
    list_media_files,
    list_episodes_for_season,
    detect_season_dirs,
    open_with_default,
    prompt_choice,
    _norm_name,
    looks_like_season_dir,
)

# --- ordinal helpers ---
ORDINAL_WORDS = {
    "primer": 1, "primero": 1, "primera": 1,
    "segundo": 2, "segunda": 2,
    "tercer": 3, "tercero": 3, "tercera": 3,
    "cuarto": 4, "cuarta": 4,
    "quinto": 5, "quinta": 5,
    "sexto": 6, "sexta": 6,
    "septimo": 7, "septima": 7, "séptimo": 7, "séptima": 7,
    "octavo": 8, "octava": 8,
    "noveno": 9, "novena": 9,
    "decimo": 10, "décimo": 10, "décima": 10,
    "undecimo": 11, "once": 11, "onceavo": 11,
    "doceavo": 12, "doce": 12,
}

def extract_ordinal_from_name(name: str) -> Optional[int]:
    n = _norm_name(name)
    # números explícitos
    m = re.search(r'\b(\d{1,3})\b', n)
    if m:
        return int(m.group(1))
    # sufijos ordinales
    m2 = re.search(r'\b(\d{1,3})(?:mo|º|th|st|nd|rd)\b', n)
    if m2:
        return int(m2.group(1))
    # palabras ordinales
    for word, val in ORDINAL_WORDS.items():
        if re.search(r'\b' + re.escape(word) + r'\b', n):
            return val
    # ingles
    eng = {
        "first":1,"second":2,"third":3,"fourth":4,"fifth":5,"sixth":6,
        "seventh":7,"eighth":8,"ninth":9,"tenth":10,"eleventh":11,"twelfth":12
    }
    for w, v in eng.items():
        if re.search(r'\b' + re.escape(w) + r'\b', n):
            return v
    return None

def is_doctor_dir(name: str) -> bool:
    n = _norm_name(name)
    if ("doctor" in n) or ("dr " in n) or n.startswith("dr.") or ("who" in n):
        return True
    if re.search(r'\b(dr|doctor|who)\b', n):
        return True
    return False

def register_parser(subparsers):
    subparsers.add_parser('who-old', help='Navegar Doctor Who Clásico')

def run(args, cfg):
    base = cfg.get('who_classic_path')
    player = cfg.get('player_cmd')
    if not base:
        print("Error: who_classic_path no configurado en la config.")
        return
    base_path = Path(base)
    if not base_path.exists():
        print(f"La ruta configurada no existe: {base_path}")
        return

    # detectar hijos directos que parezcan "Doctor X"
    children = [p for p in base_path.iterdir() if p.is_dir()]
    doctor_dirs = []
    for p in children:
        if is_doctor_dir(p.name):
            ord_val = extract_ordinal_from_name(p.name)
            doctor_dirs.append((p, p.name, ord_val if ord_val is not None else 10**6))

    # si no hay en nivel 1, buscar un nivel más
    if not doctor_dirs:
        for p in children:
            for sub in [d for d in p.iterdir() if d.is_dir()]:
                if is_doctor_dir(sub.name):
                    ord_val = extract_ordinal_from_name(sub.name)
                    doctor_dirs.append((sub, sub.name, ord_val if ord_val is not None else 10**6))

    if not doctor_dirs:
        print("No se detectaron carpetas de 'Doctor' en la ruta configurada.")
        return

    # ordenar por ordinal (None -> grande) y luego por nombre
    doctor_dirs.sort(key=lambda t: (t[2], _norm_name(t[1])))

    # mostrar lista de Doctors
    print("Doctores / grupos encontrados:")
    for i, (p, disp, ordv) in enumerate(doctor_dirs, 1):
        num = ordv if ordv < 10**6 else "-"
        print(f"[{i}] {disp}  ({p})  orden={num}")

    idx = prompt_choice(len(doctor_dirs), "Selecciona Doctor")
    if idx is None:
        return

    selected_doctor = doctor_dirs[idx][0]

    # dentro del Doctor: subcarpetas y archivos directos
    subdirs = [d for d in selected_doctor.iterdir() if d.is_dir()]
    media_here = list_media_files(selected_doctor)

    seasons = []
    for d in subdirs:
        if looks_like_season_dir(d.name) or list_media_files(d) or any(list_media_files(sd) for sd in d.iterdir() if sd.is_dir()):
            seasons.append(d)

    if seasons:
        print("Temporadas / carpetas internas:")
        for i, s in enumerate(seasons, 1):
            print(f"[{i}] {s.name}  ({s})")
        sidx = prompt_choice(len(seasons), "Selecciona temporada/carpeta")
        if sidx is None:
            return
        season_path = seasons[sidx]
        episodes = list_episodes_for_season(season_path)
        if not episodes:
            print("No se encontraron episodios en", season_path)
            return
        print("Episodios:")
        for i, ep in enumerate(episodes, 1):
            try:
                disp = str(Path(ep).relative_to(season_path))
            except Exception:
                disp = ep.name if isinstance(ep, Path) else Path(ep).name
            print(f"[{i}] {disp}")
        c = prompt_choice(len(episodes), "Selecciona episodio")
        if c is None:
            return
        ep_path = episodes[c]
        open_with_default(str(ep_path), player)
        return

    if media_here:
        print("Episodios directos en la carpeta del Doctor:")
        for i, ep in enumerate(media_here, 1):
            print(f"[{i}] {ep.name}")
        c = prompt_choice(len(media_here), "Selecciona episodio")
        if c is None:
            return
        open_with_default(str(media_here[c]), player)
        return

    # fallback: buscar temporadas más abajo
    candidates = detect_season_dirs(selected_doctor, max_depth=2)
    if not candidates:
        print("No se encontraron episodios ni temporadas bajo", selected_doctor)
        return

    print("Temporadas candidatas detectadas:")
    for i, (p, disp, score) in enumerate(candidates, 1):
        print(f"[{i}] {disp}  ({p})  score={score}")
    cidx = prompt_choice(len(candidates), "Selecciona temporada")
    if cidx is None:
        return
    season_path = candidates[cidx][0]
    episodes = list_episodes_for_season(season_path)
    if not episodes:
        print("No se encontraron episodios en", season_path)
        return
    for i, ep in enumerate(episodes, 1):
        print(f"[{i}] {ep.name}")
    c = prompt_choice(len(episodes), "Selecciona episodio")
    if c is None:
        return
    open_with_default(str(episodes[c]), player)
