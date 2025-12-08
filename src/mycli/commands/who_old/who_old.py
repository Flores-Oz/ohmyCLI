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
    list_with_watch_status, 
    mark_watched, mark_unwatched, 
    mark_all_in_dir, 
    load_watch_state, 
    save_watch_state, 
    episode_key,
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
    #solo llega hasta el Octavo Dr
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
        "seventh":7,"eighth":8
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

    # --- Bucle principal: seleccionar doctor, volver aquí al pulsar 'q' en submenús ---
    while True:
        # mostrar lista de Doctors (solo nombre, sin path ni orden)
        print("\nDoctores / grupos encontrados:")
        for i, (p, disp, ordv) in enumerate(doctor_dirs, 1):
            print(f"[{i}] {disp}")

        idx = prompt_choice(len(doctor_dirs), "Selecciona Doctor (q para salir)")
        if idx is None:
            # el usuario quiere salir del subcomando who-old -> retornamos al main
            print("Saliendo de who-old.")
            return

        selected_doctor = doctor_dirs[idx][0]

        # dentro del Doctor: subcarpetas y archivos directos
        subdirs = [d for d in selected_doctor.iterdir() if d.is_dir()]
        media_here = list_media_files(selected_doctor)

        # detectar temporadas dentro del doctor
        seasons = []
        for d in subdirs:
            if looks_like_season_dir(d.name) or list_media_files(d) or any(list_media_files(sd) for sd in d.iterdir() if sd.is_dir()):
                seasons.append(d)

        # si hay temporadas, pedir seleccionar temporada; si no, usar media directos
        if seasons:
            print("\nTemporadas / carpetas internas:")
            for i, s in enumerate(seasons, 1):
                print(f"[{i}] {s.name}")
            sidx = prompt_choice(len(seasons), "Selecciona temporada/carpeta (q para volver)")
            if sidx is None:
                # volver al listado de doctors
                continue
            season_path = seasons[sidx]

            episodes = list_episodes_for_season(season_path)
            if not episodes:
                print("No se encontraron episodios en", season_path)
                # volver al listado de seasons/doctors
                continue

            # Llamada al menú interactivo (reproduce + marcar vistos)
            episode_menu_and_play(episodes, season_path, player, cfg)
            # al volver del menú de episodios, permanecemos en el doctor seleccionado (o volvemos a doctor list)
            continue

        # si no hay temporadas pero sí archivos multimedia directos en la carpeta del Doctor
        if media_here:
            episodes = media_here
            # usar el mismo menú interactivo, pasándole la carpeta del Doctor como 'season_path'
            episode_menu_and_play(episodes, selected_doctor, player, cfg)
            # al volver del menú de episodios regresamos al listado de doctors
            continue

        # fallback: buscar temporadas más abajo
        candidates = detect_season_dirs(selected_doctor, max_depth=2)
        if not candidates:
            print("No se encontraron episodios ni temporadas bajo", selected_doctor)
            # volver al listado de doctors
            continue

        print("\nTemporadas candidatas detectadas:")
        for i, (p, disp, score) in enumerate(candidates, 1):
            print(f"[{i}] {disp}  score={score}")
        cidx = prompt_choice(len(candidates), "Selecciona temporada (q para volver)")
        if cidx is None:
            continue
        season_path = candidates[cidx][0]
        episodes = list_episodes_for_season(season_path)
        if not episodes:
            print("No se encontraron episodios en", season_path)
            continue
        # usar menú interactivo
        episode_menu_and_play(episodes, season_path, player, cfg)
        # volver al listado de doctors
        continue


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

def episode_menu_and_play(episodes: list, season_path: Path, player: Optional[str], cfg: dict):
    """
    Muestra la lista de episodios con estado y permite:
      - reproducir (p. ej. 'p 3')
      - marcar visto 'm 3'
      - desmarcar 'u 3'
      - marcar todos 'ma'
      - desmarcar todos 'ua'
      - volver 'q'
    """
    state_path = cfg.get("state_path")  # puede ser None -> usa default
    while True:
        state = load_watch_state(state_path)
        with_status = list_with_watch_status(episodes, state, state_path)
        print("\nEpisodios:")
        for i, (ep, watched) in enumerate(with_status, 1):
            mark = "✓" if watched else " "
            try:
                disp = str(Path(ep).relative_to(season_path))
            except Exception:
                disp = Path(ep).name
            print(f"[{i}] [{mark}] {disp}")

        print("\nComandos: p # (play), m # (marcar visto), u # (desmarcar), ma (marcar todos), ua (desmarcar todos), q (volver)")
        cmd = input(">").strip().lower()
        if not cmd:
            continue
        if cmd == 'q':
            return
        if cmd == 'ma':
            mark_all_in_dir(str(season_path), watched=True, state=state, path=state_path)
            print("Marcado todo como visto.")
            continue
        if cmd == 'ua':
            mark_all_in_dir(str(season_path), watched=False, state=state, path=state_path)
            print("Desmarcado todo.")
            continue

        parts = cmd.split()
        if len(parts) == 2 and parts[0] in ('p','m','u'):
            action, num = parts[0], parts[1]
            if not num.isdigit():
                print("Número inválido.")
                continue
            idx = int(num) - 1
            if idx < 0 or idx >= len(episodes):
                print("Índice fuera de rango.")
                continue
            ep = episodes[idx]
            epstr = str(ep)
            if action == 'p':
                # reproducir
                open_with_default(epstr, player)
            elif action == 'm':
                mark_watched(epstr, state=state, path=state_path)
                print("Marcado como visto.")
            elif action == 'u':
                mark_unwatched(epstr, state=state, path=state_path)
                print("Desmarcado.")
            continue
        print("Comando desconocido.")