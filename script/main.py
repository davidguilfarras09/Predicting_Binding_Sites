from itertools import groupby
from Bio.PDB import PDBParser as BioPDBParser
import os
import pandas as pd
import numpy as np
import torch
import sys
import torch.nn as nn
from esm.models.esmc import ESMC
from esm.sdk.api import ESMProtein, LogitsConfig
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from class_files.ESM import ESM
from class_files.PDBparser import PDBparser
from class_files.Model_and_Pymol import MLP, predict_binding_site

def main():
    
    if len(sys.argv) < 2:
        print('You need to pass a PDB file')
        sys.exit(1)
        

    pdb_path = sys.argv[1]

    if not os.path.exists(pdb_path):
        print(f"Error: file not found -> {pdb_path}")
        sys.exit(1)
        
    model_path = 'model/model.pth'
    pdb_id = os.path.splitext(os.path.basename(pdb_path))[0]

    pdb_file = PDBparser(pdb_path)
    residues_df = pdb_file.get_residues()
    residues_df = residues_df.drop_duplicates(subset=['sequence'])

    embeddings = ESM(residues_df)
    embeddings_df = embeddings.get_embeddings()

    predicted_sites = predict_binding_site(
        df=embeddings_df,
        pdb_path=pdb_path,
        model_path=model_path,
        threshold=0.384,
        radius=8.0,
        min_neighbors=2,
        save_pymol_script=f'{pdb_id}_binding.pml'
    )
    return predicted_sites

if __name__ == "__main__":
    main()