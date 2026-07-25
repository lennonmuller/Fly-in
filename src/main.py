from __future__ import annotations

import sys

from algorithms.pathfinder import PathFinder
from graph.graph_manager import Graph
from models.drone import Drone
from parser.parser import Parser
from renderer.display import Renderer
from scheduler.scheduler import Scheduler
from simulation.engine import Simulator


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 src/main.py <map_file>")
        raise SystemExit(1)

    renderer = Renderer()

    try:
        parser = Parser(sys.argv[1])
        data = parser.parse()

        graph = Graph()
        graph.build(data)

        if graph.start_hub is None or graph.end_hub is None:
            raise ValueError(
                "The map must define a start and an end hub"
            )

        pathfinder = PathFinder(graph)

        drones: list[Drone] = []

        for drone_id in range(1, int(data["nb_drones"]) + 1):
            path = pathfinder.get_path(
                graph.start_hub,
                graph.end_hub,
            )

            if not path:
                raise ValueError(
                    "No path found between start and end hub"
                )

            drones.append(
                Drone(
                    id=drone_id,
                    path=path,
                )
            )

        scheduler = Scheduler(graph)

        # Novo construtor (Renderer não pertence mais ao Simulator)
        engine = Simulator(
            drones=drones,
            scheduler=scheduler,
            graph=graph,
            renderer=renderer,
        )

        simulation_running = True

        while renderer.running:

            renderer.handle_events()

            if simulation_running:
                simulation_running = engine.step()

            renderer.render_state(
                graph=graph,
                drones=engine.active_drones,
            )

    except (
        FileNotFoundError,
        KeyError,
        ValueError,
    ) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1) from exc

    finally:
        renderer.close()


if __name__ == "__main__":
    main()
