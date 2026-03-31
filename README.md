# Predicting_Binding_Sites

This project leverages ESM2, a state-of-the-art protein language model developed by Meta AI, to generate residue-level embeddings from raw protein sequences obtained from the database Biolip. These embeddings are then used as input features for machine/deep learning models trained to predict binding sites,residues that interact with ligands or other proteins. The goal is to accurately identify functional regions of proteins using sequence information and 3D structure.

### Pipeline

`BioLip DB ---> Data Cleaning ---> ESM-2 Embeddings (960-dim) ---> Deep Learning Model ---> Binding Site Predictions`




### `Biolip: The dataset (see data/README.md)` 

Biolip is a protein database and its ligand/protein interaction, semi-manually curated. It contains more than 989,000 sequences that have been extracted from the Protein Data Bank (PDB) and completed with literature reviews.
This database is really useful for our project because

1) It allows obtaining the protein sequence in text as required by our pLM.
2) It allows comparing our obtained results with the real binding site.
3) It contains enough proteins to train machine or deep learning models.


### `ESM-2: transforming aminoacids in embeddings`

In recent years, the emergence of NLPs (Natural Language Processing) has been a major technological advance. This success has led to attempts to apply these models to language-like structures, and of course, the biology world is exploring the use of NLP in proteins: these specific models are called pLM (Protein Language Models) [1].
One of the first algorithms to appear was BERT and, similarly, ESM-2 was born derived from it [1]. This is a pLM developed by Meta AI in 2022, trained with more than 250 million protein sequences. The interesting thing about this model is that it allows capturing the biological semantics of proteins and, therefore, we believe that by using it, ESM-2 will give similar embeddings to amino acids that are binding sites. [2]
Thus, ESM-2 has been the algorithm we have used to obtain 960 embeddings of each residue of each of the proteins in the Biolip (cleaned) dataset in order to predict a binding site with some confidence.


### `Creating our model: model.pth`

First, we applied the filter pipeline described in the ./data folder to obtain a high-quality subset of the dataset. This subset revealed a highly imbalanced class distribution, with a 1:25 ratio of binding to non-binding residues. After exploring several classical Machine Learning approaches, including LightGBM with various balancing strategies, we found that results were inconsistent with low and unreliable precision and recall.

This led us to adopt a deep learning approach, which gived better results across all metrics. Specifically, we use an MLP (Multilayer Perceptron), which is well-suited for high-dimensional inputs like our ESM embeddings. These embeddings encode rich evolutionary and structural information per residue, and the MLP is able to learn the non-linear patterns that separate binding from non-binding residues in that complex space.

To address the class imbalance during training, we use Focal Loss, which automatically down-weights easy examples and forces the model to focus on the hard and ambiguous residues near binding sites.

To ensure reliable and generalizable evaluation, train/test splits are performed at the protein level, grouping all residues from the same PDB structure together. This prevents data leakage, where residues from the same protein could appear in both train and test sets, and ensures the model is evaluated on truly unseen proteins rather than just unseen residues.

Finally, MCC (Matthews Correlation Coefficient)-based threshold tuning is applied to select the optimal decision boundary. Unlike accuracy, MCC accounts for all four classification outcomes and gives a fair and reliable measure of performance under severe class imbalance.

The metrics we've gotten after optimizing the threshold and evaluate the model with the test set was:
| Metric             | Value  |
|--------------------|--------|
| Threshold          | 0.448  |
| MCC                | 0.6232 |
| Balanced Accuracy  | 0.8081 |
| ROC AUC            | 0.9586 |
| F1 (Weighted)      | 0.9720 |
| Precision          | 0.6453 |
| Recall             | 0.6301 |
| Specificity        | 0.9860 |

The high ROC AUC indicates strong discriminative ability between binding and non-binding residues. The model achieves excellent specificity, meaning it rarely misclassifies non-binding residues as binding. The MCC of 0.6232 provides the most honest overall summary, as it accounts for all four classification outcomes and is robust to the imbalance dataset.

<img width="673" height="468" alt="image" src="https://github.com/user-attachments/assets/16297f43-d0ca-4971-9e6d-028ae2049939" />


### `Final Remarks`

To see exactly what we used to build our model, we recommend visiting data/README.md. We filtered the BioLiP dataset to obtain a high-quality subset, which also helped reduce resource consumption. Working with high-dimensional dataframes is computationally demanding, and given our hardware limitations, managing memory and processing power was a significant constraint throughout the project.

> [1] Ofer, D., Brandes, N., & Linial, M. (2021). The language of proteins: NLP, machine learning & protein sequences.
> Computational and structural biotechnology journal, 19, 1750–1758. https://doi.org/10.1016/j.csbj.2021.03.022

> [2] ESM-2 - BioNEMO Framework. (s. f.). https://docs.nvidia.com/bionemo-framework/2.0/models/esm2/

---
### General tutorial

1. Git clone the repo and create a specific conda environment.
    ```bash
    git clone "repo link"
    conda create -n env_name
    ```

3. Then conda activate and install numpy and pandas using install and pip install the rest of the packages with with the requirements.txt file. 
    ```bash
    conda activate env_name
    pip install -r requirements.txt
    ```

5. Once you have installed all necessary pacakges, run the script "main.py" with the command:
    ```bash
    python main.py pdb_filepath
    ```

7. The script will output a file for pymol with the format PDB_id_binding.pml that you can open either in a text editor to view the predicted binding sites, or you can open in pymol for a visual confirmation.

#### In the test folder, you can see:

> ![Pymol File for 1HSG](./test/test1/1HSG_binding.pml)
> which can be used for visualization in pymol
