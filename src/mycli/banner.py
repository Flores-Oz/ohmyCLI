def print_banner():
    BLUE = "\033[94m"
    RED = "\033[91m"
    WHITE = "\033[97m"
    RESET = "\033[0m"

    tardis_lines = [
        "        ___        ",
        " _______(_@_)_______ ",
        "|  POLICE      BOX  |",
        "|___________________|",
        " | _____   _____ |   ",
        " | |###|   |###| |   ",
        " | |###|   |###| |   ",
        " | _____   _____ |   ",
        " | || ||   || || |   ",
        " | ||_||   ||_|| |   ",
        " | _____   _____ |   ",
        " | || ||   || || |   ",
        " | ||_||   ||_|| |   ",
        " |         |      |  ",
        " *******************  ",
    ]

    ohmycli_lines = [
        "                                                                                        ",
        "                                                                                        ",
        "                                                                                        ",
        " ███████    █████   █████ ██████   ██████ █████ █████   █████████  █████       █████    ",
        "███░░░░░███ ░░███   ░░███ ░░██████ ██████ ░░███ ░░███   ███░░░░░███░░███       ░░███    ",
        "███     ░░███ ░███    ░███  ░███░█████░███  ░░███ ███   ███     ░░░  ░███        ░███   ",
        "░███      ░███ ░███████████  ░███░░███ ░███   ░░█████   ░███          ░███        ░███  ",
        "░███      ░███ ░███░░░░░███  ░███ ░░░  ░███    ░░███    ░███          ░███        ░███  ",
        "░░███     ███  ░███    ░███  ░███      ░███     ░███    ░░███     ███ ░███      █ ░███  ",
        " ░░░███████░   █████   █████ █████     █████    █████    ░░█████████  ███████████ █████ ",
        "   ░░░░░░░    ░░░░░   ░░░░░ ░░░░░     ░░░░░    ░░░░░      ░░░░░░░░░  ░░░░░░░░░░░ ░░░░░  ",
    ]

    dalek_lines = [
        "         Exterminate!            ",
        "               /                 ",
        "           ___                   ",
        "     D>=G==='   '.               ",
        "           |======|              ",
        "           |======|              ",
        "       )--/]IIIIII]              ",
        "          |_______|              ",
        "          C O O O D              ",
        "         C O  O  O D             ",
        "        C  O  O  O  D            ",
        "        C__O__O__O__D            ",
        "       [_____________]           ",
    ]

    # Para ponerlos lado a lado, deben tener misma cantidad de líneas
    max_lines = max(len(tardis_lines), len(ohmycli_lines), len(dalek_lines))

    # Relleno con líneas vacías si alguna figura es más corta
    tardis_lines += [" " * len(tardis_lines[0])] * (max_lines - len(tardis_lines))
    ohmycli_lines += [" " * len(ohmycli_lines[0])] * (max_lines - len(ohmycli_lines))
    dalek_lines += [" " * len(dalek_lines[0])] * (max_lines - len(dalek_lines))

    # Imprimir en paralelo
    for t, o, d in zip(tardis_lines, ohmycli_lines, dalek_lines):
        print(BLUE + t + "   " + o + RESET + RED + "   " + d + RESET)
