from __future__ import annotations

import sys

from app import AppController


def main() -> None:
    """Ponto de entrada do sistema Fly-in."""
    
    # Validações de Live Coding (ex: --capacity-info) podem continuar aqui.
    show_capacity = "--capacity-info" in sys.argv
    if show_capacity:
        sys.argv.remove("--capacity-info")
        
    map_file = None
    if len(sys.argv) == 2:
        map_file = sys.argv[1]
    elif len(sys.argv) > 2:
        print("Uso: python3 src/main.py [caminho_do_mapa.txt]")
        raise SystemExit(1)

    try:
        # Inicia a Máquina de Estados
        app = AppController(map_file)
        app.run()
    except Exception as exc:
        print(f"Erro Fatal: {exc}")
        raise SystemExit(1) from exc

if __name__ == "__main__":
    main()