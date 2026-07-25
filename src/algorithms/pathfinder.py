from __future__ import annotations

import heapq

from graph.graph_manager import Graph


class PathFinder:
    """Route planning strategist using Dijkstra's algorithm."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    def get_path(self, start: str, end: str) -> list[str]:
        """Calculate the path between two hubs."""
        if start not in self.graph.nodes or end not in self.graph.nodes:
            return []

        distances = {node_name: float("inf") for node_name in self.graph.nodes}
        distances[start] = 0

        predecessors: dict[str, str] = {}
        priority_queue: list[tuple[float, str]] = [(0.0, start)]
        visited: set[str] = set()

        while priority_queue:
            current_cost, current_node = heapq.heappop(priority_queue)

            if current_node == end:
                break

            if current_node in visited:
                continue
            visited.add(current_node)

            for neighbor in self.graph.get_neighbors(current_node):
                move_cost = self._get_node_cost(neighbor)
                if move_cost == float("inf"):
                    continue

                new_cost = current_cost + move_cost
                if new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    predecessors[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_cost, neighbor))

        return self._reconstruct_path(predecessors, start, end)

    def _reconstruct_path(
        self,
        predecessors: dict[str, str],
        start: str,
        end: str,
    ) -> list[str]:
        """Backtrack the predecessors to assemble the path list."""
        path: list[str] = []
        current = end

        if end not in predecessors and start != end:
            return []

        while current:
            path.append(current)
            current = predecessors.get(current)
            if current == start:
                path.append(start)
                break

        return path[::-1]

    def _get_node_cost(self, node_name: str) -> float:
        """Return the cost in turns to enter a specific zone."""
        node = self.graph.nodes.get(node_name)
        if not node or node.type == "blocked":
            return float("inf")

        if node.type == "restricted":
            return 2.0

        return 1.0
