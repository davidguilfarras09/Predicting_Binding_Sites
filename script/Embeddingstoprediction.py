import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from itertools import groupby
from Bio.PDB import PDBParser


# ── 1. Definición del modelo ──────────────────────────────────────────────────

class MLP(nn.Module):
    def __init__(self, input_dim=960, hidden_dim=512, dropout=0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 256),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(256, 1)
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


# ── 2. Conversión de DataFrame a dict por cadena ──────────────────────────────

METADATA_COLS = {"pdb_id", "chain", "position", "residue"}

def df_to_embeddings_dict(df: pd.DataFrame) -> tuple:
    """
    Convierte el DataFrame de input al dict de embeddings y al dict de
    posiciones reales que espera el pipeline.

    El DataFrame debe tener las columnas:
        pdb_id, chain, position, residue, + 960 columnas de embedding.

    Returns:
        embeddings_per_chain: {"A": np.ndarray (L_A, 960), ...}
        positions_per_chain:  {"A": [4, 7, 8, ...], ...}  <- posiciones reales del PDB
    """
    feature_cols = [c for c in df.columns if c not in METADATA_COLS]
    embeddings_per_chain = {}
    positions_per_chain = {}

    for chain_id, group in df.groupby("chain", sort=False):
        embeddings_per_chain[chain_id] = group[feature_cols].values.astype(np.float32)
        positions_per_chain[chain_id] = group["position"].tolist()

    return embeddings_per_chain, positions_per_chain


# ── 3. Predicción de residuos binding por cadena ──────────────────────────────

def predict_binding_residues(
    embeddings_per_chain: dict,
    positions_per_chain: dict,
    model_path: str = "model/model.pth",
    threshold: float = 0.384,
    input_dim: int = 960,
) -> dict:
    """
    Carga el modelo y predice qué residuos son binding para cada cadena.


    Returns:
        preds_per_chain: {"A": [7, 8, ...], ...}  <- posiciones reales predichas como binding
    """
    model = MLP(input_dim=input_dim)
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()

    preds_per_chain = {}
    with torch.no_grad():
        for chain_id, emb in embeddings_per_chain.items():
            x_tensor = torch.tensor(emb, dtype=torch.float32)
            logits = model(x_tensor)
            probs = torch.sigmoid(logits)
            binding_mask = (probs > threshold)
            positions = positions_per_chain[chain_id]
            preds_per_chain[chain_id] = [
                positions[i] for i, is_binding in enumerate(binding_mask) if is_binding
            ]

    return preds_per_chain


# ── 4. Extracción de coordenadas Cα desde PDB ─────────────────────────────────

def get_ca_coordinates(pdb_path: str) -> dict:
    """
    Extrae las coordenadas del Cα de cada residuo de la estructura.

    Returns:
        coords: {(chain_id, res_num): np.ndarray (3,)}
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("protein", pdb_path)

    coords = {}
    for model in structure:
        for chain in model:
            for residue in chain:
                if "CA" in residue:
                    coords[(chain.id, residue.get_id()[1])] = (
                        residue["CA"].get_vector().get_array()
                    )
        break  # solo primer modelo

    return coords


# ── 5. Filtrado por proximidad espacial ───────────────────────────────────────

def filter_by_proximity(
    preds_per_chain: dict,
    coords: dict,
    radius: float = 8.0,
    min_neighbors: int = 2,
) -> list:
    """
    Elimina residuos predichos como binding que están aislados espacialmente.

    Args:
        preds_per_chain: {"A": [7, 8, 45, ...], ...}  <- posiciones reales predichas
        coords:          salida de get_ca_coordinates: {(chain_id, res_num): np.ndarray}
        radius:          distancia máxima en Å para considerar vecinos (default 8.0).
        min_neighbors:   mínimo de vecinos requeridos para conservar el residuo (default 2).

    Returns:
        filtered: lista de (chain_id, res_num) que pasan el filtro.
    """
    all_predicted = [
        (chain_id, res)
        for chain_id, positions in preds_per_chain.items()
        for res in positions
    ]

    filtered = []
    for key in all_predicted:
        if key not in coords:
            continue
        neighbors = sum(
            1
            for other in all_predicted
            if other != key
            and other in coords
            and np.linalg.norm(coords[key] - coords[other]) <= radius
        )
        if neighbors >= min_neighbors:
            filtered.append(key)

    removed = sorted(set(all_predicted) - set(filtered))
    print(f"  Predichos originales:   {len(all_predicted):>4}  {sorted(all_predicted)}")
    print(f"  Tras filtro proximidad: {len(filtered):>4}  {sorted(filtered)}")
    print(f"  Eliminados (aislados):  {len(removed):>4}  {removed}")

    return filtered


# ── 6. Generación del script PyMOL ────────────────────────────────────────────

def generate_pymol_script(
    filtered: list,
    pdb_path: str = None,
    color: str = "red",
    representation: str = "sticks",
) -> str:
    """
    Genera un script PyMOL para visualizar el binding site predicho.

    Args:
        filtered:        lista de (chain_id, res_num) tras el filtro de proximidad.
        pdb_path:        si se indica, añade el comando load al inicio del script.
        color:           color para el binding site (default 'red').
        representation:  representación PyMOL (default 'sticks').

    Returns:
        pymol_script: string con los comandos PyMOL.
    """
    lines = []

    if pdb_path:
        lines.append(f"load {pdb_path}, protein")

    chain_ids_present = sorted({c for c, _ in filtered})

    for chain_id, group in groupby(sorted(filtered), key=lambda x: x[0]):
        resi_str = "+".join(str(r) for _, r in group)
        lines.append(f"select binding_{chain_id}, chain {chain_id} and resi {resi_str}")
        lines.append(f"show {representation}, binding_{chain_id}")
        lines.append(f"color {color}, binding_{chain_id}")

    # Selección global que agrupa todas las cadenas
    all_selections = " or ".join(f"binding_{c}" for c in chain_ids_present)
    lines.append(f"select binding_site, {all_selections}")
    lines.append("zoom binding_site")

    return "\n".join(lines)


# ── 7. Pipeline completo ──────────────────────────────────────────────────────

def predict_binding_site(
    df: pd.DataFrame,
    pdb_path: str,
    model_path: str = "model.pth",
    threshold: float = 0.384,
    radius: float = 8.0,
    min_neighbors: int = 2,
    pymol_color: str = "red",
    pymol_representation: str = "sticks",
    save_pymol_script: str = None,
) -> list:
    """
    Pipeline completo: DataFrame de embeddings → predicción → filtrado → PyMOL.

    Args:
        df:              DataFrame con columnas: pdb_id, chain, position, residue
                         + 960 columnas de embedding (una por dimensión).
        pdb_path:        ruta al archivo PDB de la proteína.
        model_path:      ruta al archivo .pth con los pesos.
        threshold:       umbral para clasificar binding (default 0.384).
        radius:          radio de proximidad en Å (default 8.0).
        min_neighbors:   mínimo de vecinos para conservar un residuo (default 2).
        pymol_color:     color del binding site en PyMOL (default 'red').
        pymol_representation: representación PyMOL (default 'sticks').
        save_pymol_script: si se indica, guarda el script en esa ruta .pml.

    Returns:
        filtered: lista de (chain_id, res_num) del binding site predicho.
    """

    embeddings_per_chain, positions_per_chain = df_to_embeddings_dict(df)
    for chain_id, emb in embeddings_per_chain.items():
        print(f"  Cadena {chain_id}: {emb.shape[0]} residuos, {emb.shape[1]} dimensiones")

    preds_per_chain = predict_binding_residues(
        embeddings_per_chain, positions_per_chain, model_path, threshold
    )
    for chain_id, positions in preds_per_chain.items():
        print(f"  Cadena {chain_id}: {len(positions)} residuos predichos como binding")


    coords = get_ca_coordinates(pdb_path)
    filtered = filter_by_proximity(preds_per_chain, coords, radius, min_neighbors)

    pymol_script = generate_pymol_script(
        filtered,
        pdb_path=pdb_path,
        color=pymol_color,
        representation=pymol_representation,
    )
    print(pymol_script)

    if save_pymol_script:
        with open(save_pymol_script, "w") as f:
            f.write(pymol_script)
        print(f"\nScript guardado en: {save_pymol_script}")

    return filtered