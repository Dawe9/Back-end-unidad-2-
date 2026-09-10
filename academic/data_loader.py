"""Utilidades para cargar y guardar la base de datos de la tienda en JSON."""

import json
from pathlib import Path


# La ruta se calcula desde este archivo para funcionar desde cualquier carpeta.
DATA_FILE = Path(__file__).resolve().parent.parent / 'data' / 'data.json'


def load_store_data():
    """Lee el catálogo y las compras guardadas en JSON."""

    # La información se mantiene persistente en un archivo local del proyecto.
    with DATA_FILE.open(encoding='utf-8') as file:
        return json.load(file)


def save_store_data(data):
    """Guarda los cambios de la tienda en el mismo archivo JSON."""

    # Se escribe el contenido actualizado con formato legible para facilitar debugging.
    with DATA_FILE.open('w', encoding='utf-8') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


