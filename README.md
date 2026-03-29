# Predicting_Binding_Sites

This project leverages ESM2, a state-of-the-art protein language model developed by Meta AI, to generate residue-level embeddings from raw protein sequences obtained from the database Biolip. These embeddings are then used as input features for machine/deep learning models trained to predict binding sites,residues that interact with ligands or other proteins. The goal is to accurately identify functional regions of proteins using sequence information and 3D structure.

### `Biolip: The dataset (see data/README.md)` 

Biolip is a protein database and its ligand/protein interaction, semi-manually curated. It contains more than 989,000 sequences that have been extracted from the Protein Data Bank (PDB) and completed with literature reviews.
This database is really useful for our project because

1) It allows obtaining the protein sequence in text as required by our pLM.
2) It allows comparing our obtained results with the real binding site.
3) It contains enough proteins to train machine or deep learning models.


### `ESM-2: transforming aminoacids in embeddings`

In recent years, the emergence of NLPs (Natural Language Processing) has been a major technological advance. This success has led to attempts to apply these models to language-like structures, and of course, the biology world is exploring the use of NLP in proteins: these specific models are called pLM (Protein Language Models) [1].
One of the first algorithms to appear was BERT and, similarly, ESM-2 was born derived from it [1]. This is a pLM developed by Meta AI in 2022, trained with more than 250 million protein sequences. The interesting thing about this model is that it allows capturing the biological semantics of proteins and, therefore, we believe that by using it, ESM-2 will give similar embeddings to amino acids that are binding sites. [2]
Therefore, ESM-2 has been the algorithm we have used to obtain 960 embeddings of each residue of each of the proteins in the Biolip (cleaned) dataset in order to predict a binding site with some confidence.


### `Creating our model: model.pth`

After trying some Machine Learning approaches like LightGBM, we saw that our results had quite low and unreliable precision, recall and accuracy. Taking this into account, we decided to create a prediction model based on deep learning which resulted in better results in all aspects.
# YANG ESCRIBE TU AQUÍ QUE CONTROLAS MÁS SOBRE TODAS LAS ESTADÍSTICAS QUE NOS DA EL MODELO EXACTAMENTE.


### `Final Remarks`

To see exactly what we used to build our model we recommend visiting data/README.md, as we filtered the Biolip dataset in order to reduce unnecessary dimensionality caused by closely related proteins within the dataset. The dimensionality reduction was done in order to lighten the computational power required, as we do not have the necessary resources to run large programs with high complexity.




> [1] Ofer, D., Brandes, N., & Linial, M. (2021). The language of proteins: NLP, machine learning & protein sequences.
> Computational and structural biotechnology journal, 19, 1750–1758. https://doi.org/10.1016/j.csbj.2021.03.022

> [2] ESM-2 - BioNEMO Framework. (s. f.). https://docs.nvidia.com/bionemo-framework/2.0/models/esm2/