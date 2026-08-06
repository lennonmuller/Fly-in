from __future__ import annotations

import re
from typing import Any

from constants import ALLOWED_CONN_TAGS, ALLOWED_HUB_TAGS, CONN_PATTERN, HUB_PATTERN


class Parser:
    """Responsible for reading and validating the Fly-in input file."""

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.nb_drones = 0
        self.hubs: list[dict[str, Any]] = []
        self.connections: list[dict[str, Any]] = []
        self._start_node_found = False
        self._end_node_found = False

    def parse(self) -> dict[str, Any]:
        """Read the map file and return a structured representation."""
        try:
            with open(self.filepath, "r", encoding="utf-8") as file:
                for line_num, line in enumerate(file, 1):
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith("#"):
                        continue
                    self._parse_line(clean_line, line_num)
            self._validate_final_state()
        except FileNotFoundError as exc:
            message = f"File {self.filepath} not found."
            raise FileNotFoundError(message) from exc

        return {
            "nb_drones": self.nb_drones,
            "hubs": self.hubs,
            "connections": self.connections,
            "start_hub": self._get_hub("start_hub"),
            "end_hub": self._get_hub("end_hub"),
        }

    def _parse_line(self, line: str, line_num: int) -> None:
        """Identify the row type and apply the corresponding regex."""
        if self.nb_drones == 0:
            if match := re.match(r"^nb_drones:\s(?P<num>\d+)$", line):
                self.nb_drones = int(match.group("num"))
                return
            self._raise_error(
                line_num,
                "The first line must be 'nb_drones'",
            )

        if (
            line.startswith(prefix)
            for prefix in ["hub:", "start_hub:", "end_hub:"]
        ) and (match := HUB_PATTERN.match(line)):
            self._handle_hub_data(match.groupdict(), line_num)
            return

        if line.startswith("connection:"):
            if match := CONN_PATTERN.match(line):
                meta_str = str(match.group("meta") or "")
                metadata = self.extract_metadata(meta_str)

                for key in metadata:
                    if key not in ALLOWED_CONN_TAGS:
                        self._raise_error(line_num, f"Unsupported connection tag: {key}")

                link_cap = 1
                if "max_link_capacity" in metadata:
                    link_cap = self.validate_positive_int(
                        metadata["max_link_capacity"],
                        "max_link_capacity",
                        line_num
                    )

                self.connections.append(
                    {
                        "src": match.group("src"),
                        "dst": match.group("dst"),
                        "max_link_capacity": link_cap
                    }
                )
                return

        self._raise_error(
            line_num,
            f"Invalid syntax or unknown command: {line}",
        )

    def _handle_hub_data(self, data: dict[str, Any], line_num: int) -> None:
        hub_type = data.get("type", "hub")
        metadata = self.extract_metadata(str(data.get("meta", "")))
        self.validate_allowed_keys(metadata)

        if hub_type == "start_hub":
            if self._start_node_found:
                self._raise_error(line_num, "Duplicate start_hub declaration")
            self._start_node_found = True
        elif hub_type == "end_hub":
            if self._end_node_found:
                self._raise_error(line_num, "Duplicate end_hub declaration")
            self._end_node_found = True
        elif hub_type == "hub":
            hub_type = metadata.get("zone", "normal")

        hub_data: dict[str, Any] = {
            "name": data.get("name"),
            "x": int(data.get("x", 0)),
            "y": int(data.get("y", 0)),
            "type": hub_type,
        }

        max_drones = metadata.get("max_drones")
        if max_drones is not None:
            hub_data["max_drones"] = self.validate_positive_int(
                max_drones,
                "max_drones",
                line_num,
            )
        else:
            hub_data["max_drones"] = 1

        if "color" in metadata:
            hub_data["color"] = metadata["color"]

        self.hubs.append(hub_data)

    def _validate_final_state(self) -> None:
        if not self._start_node_found or not self._end_node_found:
            self._raise_error(
                0,
                "Map must exactly one 'start_hub' and one 'end_hub'",
            )

        hub_names = {hub["name"] for hub in self.hubs}
        for connection in self.connections:
            if (
                connection["src"] not in hub_names
                or connection["dst"] not in hub_names
            ):
                self._raise_error(
                    0,
                    f"Connection {connection['src']}-{connection['dst']} "
                    "references an undefined hub",
                )

        if self.nb_drones <= 0:
            self._raise_error(1, "Number of drones must be a positive integer")

    def _get_hub(self, hub_type: str) -> dict[str, Any] | None:
        for hub in self.hubs:
            if hub.get("type") == hub_type:
                return hub
        return None

    def extract_metadata(self, meta_string: str) -> dict[str, str]:
        """Transform metadata into a dictionary."""
        if not meta_string:
            return {}

        tag_pattern = re.compile(r"(\w+)=([^\s\[\]]+)")
        matches = tag_pattern.findall(meta_string)
        return dict(matches)

    def validate_allowed_keys(self, meta_string: dict[str, str]) -> None:
        for key in meta_string:
            if key not in ALLOWED_HUB_TAGS:
                raise KeyError(f"Unsupported hub tag: {key}")

    def validate_positive_int(
        self,
        value_str: str,
        field_name: str,
        line_num: int,
    ) -> int:
        """Validate an integer value."""
        try:
            value = int(value_str)
            if value <= 0:
                raise ValueError("Must be positive")
            return value
        except ValueError as exc:
            message = (
                f"Parsing Error (line {line_num}): {field_name} "
                f"'{value_str}' is invalid. Cause: Must be a positive integer."
            )
            raise ValueError(message) from exc

    def _raise_error(self, line_num: int, cause: str) -> None:
        """Interrupt execution and display the error."""
        location = f"line {line_num}" if line_num > 0 else "end of file"
        raise ValueError(f"Parsing Error ({location}): {cause}")
