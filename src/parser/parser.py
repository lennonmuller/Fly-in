class Parser:
    """Responsible for reading and validating the Fly-in input file."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.drones_count: int = 0
        self.hubs: list[dict] = []
        self.connections: list[dict] = []

    def parse(self) -> None:
        """It reads the file line by line and fills in the internal data."""
        pass

    def _parse_line(self, line: str, line_num: int) -> None:
        """It identifies the row type and applies the corresponding Regex."""
        pass