import re


# Padrao para hub: name x y [metadata]
HUB_PATTERN = re.compile(r"""
    ^                   # Inicio da linha
    (?P<type>hub|start_hub|end_hub):  # Grupo 'type': identifica o tipo
    \s+                 # Espaco obrigatorio
    (?P<name>[^- \s]+)  # Grupo 'name': qualquer char exceto traco ou espaco
    \s+                 # Espaco
    (?P<x>-?\d+)        # Grupo 'x': coordenada inteira
    \s+                 # Espaco
    (?P<y>-?\d+)        # Grupo 'y': coordenada inteira
    (?:\s*\[?P<meta>.*)\])?  # Grupo 'meta'opcional: tudo dentro dos colchetes
    $                   # fim da linha
""", re.VERBOSE)

# Padrao para: connection: zone1-zone2 [metadata]
CONN_PATTERN = re.compile(r"""
    ^connection:            # Identificador fixo
    \s+                     # Espaco
    (?P<src>[^- \s]+)       # Nome da zona de origem
    -                       # O traco separador
    (?P?<dst>[^- \s]+)      # Nome da zona de destino
    (?:\s*\[(?P<meta>.*)\])?  # Metadados opcionais
    $
""", re.VERBOSE)

ALLOWED_HUB_TAGS = [
    "zone",
    "color",
    "max_drones"
]
