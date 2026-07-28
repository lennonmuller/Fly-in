from __future__ import annotations

import heapq

from graph.graph_manager import Graph
from graph.reservation import ReservationTable


class PathFinder:
    """Route planning strategist using Space-time Dijkstra's algorithm."""

    def __init__(self, graph: Graph, reservation: ReservationTable) -> None:
        self.graph = graph
        self.reservation = reservation
        self.max_time = 200  # contra loops infinitos

    def get_path(self, start: str, end: str) -> list[str]:
        """Calculate the optimal path avoiding collisions in time and space."""
        if start not in self.graph.nodes or end not in self.graph.nodes:
            return []

        priority_queue: list[tuple[float, int, str]] = [(0.0, 0, start)]
        distances: dict[tuple[str, int], float] = {(start, 0): 0.0}
        predecessors: dict[tuple[str, int], tuple[str, int, list[str]]] = {}

        while priority_queue:
            current_cost, t, u = heapq.heappop(priority_queue)

            if u == end:
                return self._reconstruct_and_reserve(
                    predecessors, (u, t), start)

            if t >= self.max_time:
                continue

            # Acao 1: ESPERAR
            # Fica no mesmo nó até o próximo turno, se houver capacidade.
            if self.reservation.get_node_occupancy(u, t + 1) < self.graph.get_node_capacity(u):
                new_cost = current_cost + 1
                if new_cost < distances.get((u, t + 1), float("inf")):
                    distances[(u, t + 1)] = new_cost
                    predecessors[(u, t + 1)] = (u, t, [u])
                    heapq.heappush(priority_queue, (new_cost, t + 1, u))

            # acao 2: mover
            for neighbor_name in self.graph.get_neighbors(u):
                node_v = self.graph.nodes.get(neighbor_name)
                if not node_v or node_v.type == "blocked":
                    continue

                edge_cap = self.graph.get_edge_capacity(u, neighbor_name)
                node_cap = self.graph.get_node_capacity(neighbor_name)

                if node_v.type == "restricted":
                    # Zonas restritas demoram 2 turnos. A aresta fica ocupada no turno T e T+1.
                    if (
                        self.reservation.get_edge_occupancy(u, neighbor_name, t) < edge_cap
                        and self.reservation.get_edge_occupancy(u, neighbor_name, t + 1) < edge_cap
                        and self.reservation.get_node_occupancy(neighbor_name, t + 2) < node_cap
                    ):
                        new_cost = current_cost + 2.0
                        if new_cost < distances.get((neighbor_name, t + 2), float("inf")):
                            distances[(neighbor_name, t + 2)] = new_cost
                            # A sintaxe de zona restrita gera um estado na "aresta" no turno do meio
                            conn_name = f"{u}-{neighbor_name}"
                            predecessors[(neighbor_name, t + 2)] = (u, t, [conn_name, neighbor_name])
                            heapq.heappush(priority_queue, (new_cost, t + 2, neighbor_name))
                else:
                    # Zonas normais ou de prioridade demoram 1 turno.
                    if (
                        self.reservation.get_edge_occupancy(u, neighbor_name, t) < edge_cap
                        and self.reservation.get_node_occupancy(neighbor_name, t + 1) < node_cap
                    ):
                        # Dica de Mestre: Nós prioritários custam 1 de tempo,
                        # mas damos um "desconto" artificial na heurística para o Dijkstra preferi-los.
                        step_cost = 0.1 if node_v.type == "priority" else 1.0
                        new_cost = current_cost + step_cost

                        if new_cost < distances.get((neighbor_name, t + 1), float("inf")):
                            distances[(neighbor_name, t + 1)] = new_cost
                            predecessors[(neighbor_name, t + 1)] = (u, t, [neighbor_name])
                            heapq.heappush(priority_queue, (new_cost, t + 1, neighbor_name))
        return []

    def _reconstruct_and_reserve(
        self,
        predecessors: dict[tuple[str, int], tuple[str, int, list[str]]],
        target_state: tuple[str, int],
        start_node: str,
    ) -> list[str]:
        """Constrói a lista final da rota e carimba na ReservationTable."""
        path_segments: list[str] = []
        curr_state = target_state

        while curr_state in predecessors:
            prev_node, prev_t, segments = predecessors[curr_state]
            path_segments.extend(reversed(segments))
            curr_state = (prev_node, prev_t)

        path_segments.append(start_node)
        path_segments.reverse()

        self._reserve_path(path_segments)
        return path_segments

    def _reserve_path(self, path: list[str]) -> None:
        """Garante a vaga do drone na malha do tempo."""
        for t in range(len(path)):
            loc = path[t]
            if "-" in loc:
                # O drone está no meio de uma conexão restrita
                u, v = loc.split("-")
                self.reservation.reserve_edge(u, v, t)
                self.reservation.reserve_edge(u, v, t - 1)
            else:
                self.reservation.reserve_node(loc, t)
                # Se o drone se moveu, reservamos a aresta que ele usou no turno anterior
                if t > 0:
                    prev_loc = path[t - 1]
                    if prev_loc != loc and "-" not in prev_loc:
                        self.reservation.reserve_edge(prev_loc, loc, t - 1)
