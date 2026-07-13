from models.node import Node
from models.edge import Egde


class Graph:
    """
    Manages the zone network topology.
    Uses an adjacency list for efficiency O(1)
    """
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.adj: dict[str, list[Egde]] = {}

    def add_node(self, node: Node) -> None:
        """Add a hub to the graph."""
        self.nodes[node.name] = node
        if node.name not in self.adj:
            self.adj[node.nome] = []

    def add_edge(self, edge: Egde) -> None:
        """add a bidirectional conexion"""
        self.adj[edge.source].append(edge)  # sentido A -> B
        reverse_edge = Egde(
            edge.destination,
            edge.source,
            edge.max_link_capacity)  # sentido B -> A (invertido)
        self.adj[edge.destination].append(reverse_edge)

    def get_neighbors(self, node_name: str) -> list[str]:
        """Returns the names of the hubs connected to this."""
        return [e.destination for e in self.adj.get(node_name, [])]
