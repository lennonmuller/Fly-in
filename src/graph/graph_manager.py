from __future__ import annotations

from typing import Any

from models.edge import Edge
from models.node import Node


class Graph:
    """Manage the zone network topology."""

    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.adj: dict[str, list[Edge]] = {}
        self.start_hub: str | None = None
        self.end_hub: str | None = None

    def build(self, data: dict[str, Any]) -> None:
        """Populate the graph from parsed map data."""
        for hub in data.get("hubs", []):
            node = Node(
                name=str(hub["name"]),
                x=int(hub["x"]),
                y=int(hub["y"]),
                type=str(hub.get("type", "hub")),
                max_drones=int(hub.get("max_drones", 1)),
                color=hub.get("color"),
            )
            self.add_node(node)

        for connection in data.get("connections", []):
            self.add_edge(
                Edge(
                    source=str(connection["src"]),
                    destination=str(connection["dst"]),
                    max_link_capacity=int(connection.get("max_link_capacity", 1)),
                )
            )

        if data.get("start_hub") is not None:
            self.start_hub = str(data["start_hub"]["name"])
        if data.get("end_hub") is not None:
            self.end_hub = str(data["end_hub"]["name"])

    def add_node(self, node: Node) -> None:
        """Add a hub to the graph."""
        self.nodes[node.name] = node
        self.adj.setdefault(node.name, [])

    def add_edge(self, edge: Edge) -> None:
        """Add a bidirectional connection."""
        self.adj.setdefault(edge.source, []).append(edge)
        reverse_edge = Edge(
            source=edge.destination,
            destination=edge.source,
            max_link_capacity=edge.max_link_capacity,
        )
        self.adj.setdefault(edge.destination, []).append(reverse_edge)

    def get_neighbors(self, node_name: str) -> list[str]:
        """Return the names of the hubs connected to this node."""
        return [edge.destination for edge in self.adj.get(node_name, [])]

    def get_edge(self, source: str, destination: str) -> Edge | None:
        """Return the direct edge between two hubs when it exists."""
        for edge in self.adj.get(source, []):
            if edge.destination == destination:
                return edge
        return None

    def get_node_capacity(self, node_name: str) -> float:
        """
        Returns the node's capacity.
        Start and End have infinite capacity.
        """
        if node_name == self.start_hub or node_name == self.end_hub:
            return float('inf')

        node = self.nodes.get(node_name)
        return node.max_drones if node else 0

    def get_edge_capacity(self, src: str, dst: str) -> float:
        """Returns the maximum capacity of the edge between two nodes."""
        edge = self.get_edge(src, dst)
        return edge.max_link_capacity if edge else 0
