# src/mycli/commands/who_old.py
from pathlib import Path
from mycli.utils import list_dirs, list_media_files, prompt_choice, open_with_default

def register_parser(subparsers):
    # registrar subcomando exacto "who-old"
    subparsers.add_parser('who-old', help='Navegar Doctor Who Clásico')

def run(args, cfg):
    base = cfg.get('who_classic_path')
    player = cfg.get('player_cmd')
    if not base:
        print("Error: who_classic_path no configurado en la config.")
        return
    base_path = Path(base)
    if not base_path.is_dir():
        print(f"La ruta configurada no existe: {base_path}")
        return

    seasons = list_dirs(str(base_path))
    if not seasons:
        print("No se encontraron temporadas (carpetas).")
        return

    print("Temporadas:")
    for i, s in enumerate(seasons, 1):
        print(f"[{i}] {s}")
    idx = prompt_choice(len(seasons), "Selecciona temporada")
    if idx is None:
        return

    season_folder = base_path / seasons[idx]
    episodes = list_media_files(str(season_folder))
    if not episodes:
        # buscar en subcarpetas
        subdirs = [d for d in season_folder.iterdir() if d.is_dir()]
        candidates = []
        for sd in subdirs:
            media = list_media_files(str(sd))
            for m in media:
                candidates.append((sd / m, f"{sd.name}/{m}"))
        if not candidates:
            print("No se encontraron episodios en esa temporada.")
            return
        print("Episodios encontrados:")
        for i, (_, display) in enumerate(candidates, 1):
            print(f"[{i}] {display}")
        c = prompt_choice(len(candidates), "Selecciona episodio")
        if c is None:
            return
        path_to_open = str(candidates[c][0])
        print(f"Abrir: {path_to_open}")
        open_with_default(path_to_open, player)
        return

    print("Episodios:")
    for i, ep in enumerate(episodes, 1):
        print(f"[{i}] {ep}")
    c = prompt_choice(len(episodes), "Selecciona episodio")
    if c is None:
        return
    path_to_open = str(season_folder / episodes[c])
    print(f"Abrir: {path_to_open}")
    open_with_default(path_to_open, player)
