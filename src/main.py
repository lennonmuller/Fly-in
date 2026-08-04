from __future__ import annotations

import sys

from app import AppController


def main() -> None:
    """Ponto de entrada do sistema Fly-in."""
    args = sys.argv[1:]

    # Trata a flag de livecoding sem interferir no caminho do mapa
    show_capacity = "--capacity-info" in args
    if show_capacity:
        args.remove("--capacity-info")

    map_file: str | None = None

    if len(args) == 1:
        map_file = args[0]
    elif len(args) > 1:
        print("Uso: python3 src/main.py [caminho_do_mapa.txt] [--capacity-info]")
        raise SystemExit(1)

    try:
        # Se map_file for None, o AppController iniciará no STATE_MENU
        app = AppController(map_file)
        app.run()
    except Exception as exc:
        print(f"Erro Fatal: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
