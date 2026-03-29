## 📦 Dataset

The datasets used in this project are too large to host directly in this repository.
You can download them from Kaggle:

🔗 **[yangxinzhandu/datasets on Kaggle](https://www.kaggle.com/yangxinzhandu/datasets)**

---

### `BioLiP_nr.txt`

[BioLiP](https://zhanggroup.org/BioLiP/) is a semi-manually curated database for high-quality,
biologically relevant ligand–protein binding interactions, updated weekly.

| Property | Details |
|----------|---------|
| Version | 2025-07-30 |
| Entries | 989,724 |
| Format | Tab-separated `.txt` |

#### Column structure

| # | Field | Description |
|---|-------|-------------|
| 01 | `pdb_id` | PDB identifier |
| 02 | `receptor_chain` | Receptor chain ID |
| 03 | `resolution` | Resolution in Å (`-1.00` = not available, e.g. NMR structures) |
| 04 | `binding_site_code` | Binding site number code |
| 05 | `ligand_id` | Ligand ID in the Chemical Component Dictionary (CCD) |
| 06 | `ligand_chain` | Ligand chain ID |
| 07 | `ligand_serial` | Ligand serial number |
| 08 | `binding_residues_pdb` | Binding site residues (original PDB numbering) |
| 09 | `binding_residues_renum` | Binding site residues (renumbered from 1) |
| 10 | `catalytic_residues_pdb` | Catalytic site residues, `;`-separated (original PDB numbering) |
| 11 | `catalytic_residues_renum` | Catalytic site residues, `;`-separated (renumbered from 1) |
| 12 | `ec_number` | EC number |
| 13 | `go_terms` | GO terms |
| 14 | `affinity_manual` | Binding affinity from literature survey (PubMed ID in parentheses) |
| 15 | `affinity_moad` | Binding affinity from [Binding MOAD](http://bindingmoad.chem.lsa.umich.edu/) |
| 16 | `affinity_pdbbind` | Binding affinity from [PDBbind-CN](http://www.pdbbind.org.cn/) |
| 17 | `affinity_bindingdb` | Binding affinity from [BindingDB](https://www.bindingdb.org/) |
| 18 | `uniprot_id` | UniProt ID |
| 19 | `pubmed_id` | PubMed ID |
| 20 | `ligand_seq_num` | Ligand residue sequence number (`_atom_site.auth_seq_id` in mmCIF) |
| 21 | `receptor_sequence` | Full receptor amino acid sequence |

#### How to load
```python
import pandas as pd

columns = [
    "pdb_id",
    "receptor_chain",
    "resolution",
    "binding_site_code",
    "ligand_id",
    "ligand_chain",
    "ligand_serial_number",
    "binding_residues_pdb",
    "binding_residues_seq",
    "catalytic_residues_pdb",
    "catalytic_residues_seq",
    "ec_number",
    "go_terms",
    "binding_affinity_manual",
    "binding_affinity_moad",
    "binding_affinity_pdbbind",
    "binding_affinity_bindingdb",
    "uniprot_id",
    "pubmed_id",
    "ligand_residue_seq_number",
    "sequence"]

df = pd.read_csv('BioLiP_nr.txt', sep='\t', header=None, names=columns)
print(df.shape)  # (86458, 21)
```

> Zhang C, Zhang X, Freddolino PL, Zhang Y. **BioLiP2: an updated structure database for
> biologically relevant ligand–protein interactions.** *Nucleic Acids Research*, gkad630 (2023).

---

### `pdb_ids_cleaned.tsv`

Subset of PDB IDs derived from BioLiP after a multi-step filtering pipeline to produce
a clean, non-redundant set suitable for embedding and model training.

#### Filtering pipeline

| Step | Filter | Criterion |
|------|--------|-----------|
| 1 | Molecular weight | Ligands within a valid MW range |
| 2 | Resolution | ≤ 2.0 Å |
| 3 | Sequence length | Minimum and maximum amino acid length thresholds |
| 4 | Redundancy removal | ≤ 25% maximum pairwise sequence identity (PISCES) |

Redundancy removal was performed with **PISCES**. Sequence identity between PDB entries is
computed by building a hidden Markov model (HMM) for every unique PDB sequence using
**HHblits** (Söding et al.), then cross-searching all HMMs with **HHsearch**. This approach
allows reliable culling at low identity thresholds (15–30%), where simple pairwise alignment
methods become unreliable.

> Wang G, Dunbrack RL Jr. **PISCES: a protein sequence culling server.**
> *Bioinformatics*, 19:1589–1591 (2003).

> Söding J, Biegert A, Lupas AN. **The HHpred interactive server for protein homology
> detection and structure prediction.** *Nucleic Acids Research*, 33:W244–W248 (2005).

---

### `model_dataset_cleaned.parquet`

Final training dataset, built by filtering `BioLiP_nr.txt` to retain only the
**3,362 proteins** whose PDB IDs passed the cleaning pipeline above.

| Property | Details |
|----------|---------|
| Size | ~2 GB |
| Format | Apache Parquet |
| Rows | 1,134,510 |
| Columns | 964 |
| Proteins | 3,362 |

Each **row** represents a single residue from a protein PDB structure.

#### Column structure

| Column(s) | Description |
|-----------|-------------|
| `pdb_id` | PDB identifier of the source protein |
| `position` | Residue position in the chain |
| `residue` | Amino acid in one-letter code (A, M, L...) |
| `isbinding` | Binary label — whether the residue is a binding site (`1`) or not (`0`) |
| `esm_0` → `esm_959` | ESM protein language model embeddings (960 dimensions) |

> The `esm_*` columns are the main features used to train the model.
> They encode protein sequence context as dense numerical vectors.

#### How to load
```python
import pandas as pd

df = pd.read_parquet('model_dataset_cleaned.parquet')
print(df.shape)  # (1134510, 964)
```
