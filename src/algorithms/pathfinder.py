import heapq
from typing import List, Dict, Optional
from models.node import Node
from graph.graph_manager import Graph


class PathFinder:
    """
    Route planning strategist.
    Implements Dijkstra's theorem to ensure the shortest travel time (shifts).
    """

    def __init__(self, graph: Graph):
        self.graph = graph

    def get_path(self, start: str, end: str) -> List[str]:
        """
        It calculates and returns the ideal using dijkstra,
        considering costs of zones.
        """

        # inicializacao
        # Distancia para todos os nodes comeca como infinito, exceto o inicio
        distances = {node_name: float('inf') for node_name in self.graph.nodes}
        distances[start] = 0

        # Mapa para construir o caminho (filho -> pai)
        predecessors: Dict[str, str] = {}

        # fila de prioridade: armazena tuplas (custo_acumulado, nome_do_node)
        priority_queue = [(0, start)]

        # conjunto de visitados para otimizacao (nao visitar o mesmo node)
        visited = set()

        while priority_queue:
            # extrai o node com o menor custo acumulado atual
            current_cost, current_node = heapq.heappop(priority_queue)

            if current_node == end:
                break  # encontramos o caminho mais curto ate o destino

            if current_node in visited:
                continue
            visited.add(current_node)

            # Relaxamento de arestas (verificacao de atalhos)
            for neighbor in self.graph.get_neighbors(current_node):
                move_cost = self._get_node_cost(neighbor)

                if move_cost == float('inf'):
                    continue

                new_cost = current_cost + move_cost

                # atualizamos se encontramos caminhos mais rapidos
                if new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    predecessors[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_cost, neighbor))

        return self._reconstruct_path(predecessors, start, end)

    def _reconstruct_path(
            self,
            predecessors: Dict[str, str],
            start: str, end: str) -> List[str]:
        """It backtracks the predecessors to assemble the path list."""
        path = []
        current = end

        # se o destino nao tem predecessor e nao e o inicio entao nao ha
        # caminho
        if end not in predecessors and start != end:
            return []

        while current:
            path.append(current)
            current = predecessors.get(current)
            if current == start:
                path.append(start)
                break

        return path[::-1]

    def _get_node_cost(self, node_name: str) -> int:
        """Returns the cost in turns to enter a specific zone."""
        node = self.graph.nodes.get(node_name)
        if not node or node.type == "blocked":
            return float('inf')

        if node.type == "restricted":
            return 2

        return 1
