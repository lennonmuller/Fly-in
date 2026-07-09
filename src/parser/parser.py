import re
from constants import ALLOWED_HUB_TAGS, HUB_PATTERN, CONN_PATTERN


class Parser:
    """Responsible for reading and validating the Fly-in input file."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.drones_count: int = 0
        self.hubs: list[dict] = []
        self.connections: list[dict] = []
        self._start_node_found = False
        self._end_node_found = False

    def parse(self) -> None:
        """It reads the file line by line and fills in the internal data."""
        try:
            with open(self.filepath, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith('#'):
                        continue
                    self._parse_line(clean_line, line_num)
            self._validade_final_state()
        except FileNotFoundError:
            print(f"Error: File {self.filepath} not found.")
            exit(1)

    def _parse_line(self, line: str, line_num: int) -> None:
        """It identifies the row type and applies the corresponding Regex."""
        # Validar primeira linha 'nb_drones'
        if self.nb_drones == 0:
            if match := re.match(r"^nb_drones:\s(?P<num>\d+)$", line):
                self.nb_drones = int(match.group("num"))
                return
            self._raise_error(line_num, "The first line must be 'nb_drones'")

        # padroes de hub
        if any(line.startswith(p) for p in ["hub:", "start_hub:", "end_hub:"]):
            if match := HUB_PATTERN.match(line):
                data = match.groupdict()
                self._handle_hub_data(data, line_num)
                return

        # tentar padrao de conexao
        if line.startswith("connection:"):
            if match := CONN_PATTERN.match(line):
                self.connections.append(match.groupdict())
                return

        self._raise_error(
            line_num, f"Invalid syntax or unknown command:{line}")

    def _validate_final_state(self) -> None:
        # Validar inicio e fim
        if not self._start_node_found or not self._end_node_found:
            self._raise_error(
                0, "Map must exactly one 'start_hub' and one 'end_hub'")

        hub_names = {h['name'] for h in self.hubs}
        for conn in self.connections:
            if conn['src'] not in hub_names or conn['dst'] not in hub_names:
                self._raise_error(
                    0, f"Connection {conn['src']}-{conn['dst']} \
                        reference an undefined hub")

        if self.nb_drones <= 0:
            self._raise_error(1, "Number of drones must be a positive integer")

    def extract_metadata(meta_string: str) -> dict[str, str]:
        """Transform metadata in a dict and extract metadata.
        No metter the order of the tags."""
        if not meta_string:
            return {}

        # Padrao para capturar chave=valor
        tag_pattern = re.compile(r'(\w+)=([^- \s\[\]]+)')

        # re.findall retorna uma lista de tuplas
        matches = tag_pattern.findall(meta_string)

        return dict(matches)

    def validate_allowed_keys(meta_string: dict[str, str]) -> None:
        for key in ALLOWED_HUB_TAGS:
            if key not in meta_string:
                raise KeyError(f"Missing required key: {key}")

    def validate_positive_int(
            value_str: str,
            field_name: str,
            line_num: int) -> int:
        """Make the validation for integers"""
        try:
            value = int(value_str)
            if value <= 0:
                raise ValueError("Must be positive")
            return value
        except ValueError:
            print(
                f"Parsing Error (line {line_num}): {field_name} '{value_str}' \
                is Invalid. Cause: Must be a positive integer.")
            exit(1)

    def _raise_error(self, line_num: int, cause: str) -> None:
        """It interrupts execution and displays the error."""
        location = f"line {line_num}" if line_num > 0 else "end of file"
        print(f"Parsing Error ({location}): {cause}")
        exit(1)
