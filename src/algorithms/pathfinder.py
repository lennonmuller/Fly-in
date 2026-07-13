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
        """It calculates and returns the ideal route between two hubs."""
        # Dijkstra
        pass

    def _get_node_cost(self, node_name: str) -> int:
        """Returns the cost in turns to enter a specific zone."""
        node = self.graph.nodes.get(node_name)
        if not node or node.type == "blocked":
            return float('inf')

        if node.type == "restricted":
            return 2

        return 1
