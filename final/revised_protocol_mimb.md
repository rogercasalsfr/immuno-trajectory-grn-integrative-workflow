# Integrative Trajectory and Gene Regulatory Network Inference to Dissect T-Cell State Transitions During Cancer Immunotherapy

Author names and affiliations to be inserted here according to the invited protocol template.

## Abstract

Single-cell RNA sequencing makes it possible to reconstruct how immune cells progress between functional states during cancer immunotherapy, but trajectory inference alone does not identify the transcriptional programs that may drive those transitions. This protocol describes a reproducible workflow for combining trajectory inference, transcription factor activity analysis, pathway interpretation, and downstream gene regulatory network analysis in tumor-infiltrating T cells. The workflow is illustrated with a publicly available squamous cell carcinoma dataset containing samples collected before and after anti-PD-1 treatment. After data loading, quality control, and optional batch correction, the user defines a biologically coherent T-cell subset and infers trajectories with complementary approaches including PAGA, Monocle 3, and Slingshot. Pseudotime-associated genes are then identified, pathway activity is quantified, and transcription factor activity is ranked along the inferred manifold with decoupler. Finally, precomputed pySCENIC outputs are integrated to prioritize regulons and visualize TF-TF subnetworks associated with lineage progression or branch-specific fate decisions. The protocol emphasizes practical decision points that strongly affect interpretation, including annotation quality, root selection, treatment-specific stratification, and the distinction between exploratory regulatory hypotheses and direct mechanistic proof. The resulting workflow provides a practical guide for identifying candidate regulators of T-cell state transitions in immunotherapy studies while remaining adaptable to related single-cell datasets.

## Keywords

pseudotime; trajectory inference; single-cell RNA sequencing; immunotherapy; T cells; Monocle 3; Slingshot; PAGA; pySCENIC; decoupler; regulons

## 1 Introduction

The tumor microenvironment is a dynamic system in which T cells continuously change their transcriptional and functional states in response to tumor-derived signals, chronic antigen exposure, and therapeutic intervention. Immune checkpoint blockade can shift these states in complex ways, but static clustering alone often provides only a partial view of how cells move between precursor, effector, dysfunctional, or regulatory programs. Single-cell RNA sequencing offers the resolution required to examine this heterogeneity, and trajectory inference provides a way to order cells along a continuous process that approximates biological progression.

Trajectory inference, however, is only part of the biological question. Pseudotime methods can suggest how cells are organized along a manifold and where branch points may occur, but they do not directly explain which transcription factors or regulons may be associated with those transitions. Regulatory analysis therefore adds an important second layer. By integrating transcription factor activity scoring and downstream gene regulatory network analysis, the user can move from descriptive cell ordering toward mechanistic hypotheses about the programs that accompany lineage progression, treatment response, or branch divergence.

This protocol adapts the computational workflow described in `final_protocol.ipynb` into a MiMB-style chapter format. The example analysis uses GEO accession `GSE123813`, a single-cell RNA sequencing dataset of tumor-infiltrating lymphocytes from squamous cell carcinoma patients sampled before and after anti-PD-1 therapy. The protocol guides the reader through data preparation, selection of biologically coherent T-cell populations, quality control, patient-effect handling, trajectory inference with complementary methods, identification of pseudotime-associated genes, pathway interpretation, transcription factor activity analysis, and downstream integration of precomputed pySCENIC outputs.

The protocol is intended for readers who are comfortable with basic Python or notebook-based analysis and who wish to connect cell-state progression with regulatory interpretation. It is most informative when the analyzed cell subset represents a plausible continuum of related states, such as CD4+ or CD8+ T-cell programs. The workflow is also deliberately explicit about its limitations. Pseudotime is inferred rather than observed, embedding and preprocessing choices can affect topology, and regulon analysis is best interpreted as a source of candidate mechanisms that should be validated experimentally or with orthogonal computational evidence.

## 2 Materials

### 2.1 Software and computational environment

1. Linux workstation, server, or HPC environment with `Apptainer` or `SingularityCE` for containerized execution.
2. The workflow repository `cancer-pseudotime-grn-workflow`, which includes `env/pstime.def`, `env/environment.yml`, `env/pstime.yml`, `scripts/pstime_protocol.ipynb`, and `scripts/methods.ipynb`.
3. Python `3.14.3` environment containing at least the core packages recorded in `env/environment.yml`, including `anndata 0.12.6`, `scanpy 1.12`, `decoupler-py 2.1.4`, `pandas 2.3.3`, `numpy 1.26.4`, `scipy 1.17.1`, `scikit-learn 1.8.0`, `umap-learn 0.5.11`, `py-monocle 0.1.1`, `pyslingshot 0.2.0`, `networkx 3.6.1`, `matplotlib 3.10.8`, and `jupyterlab 4.5.5`.
4. Optional annotation software such as `celltypist` when manual annotations are not supplied by the source dataset.
5. `pySCENIC 0.12.1` in Docker for upstream regulon inference when raw-expression GRN reconstruction is required.
6. `Cytoscape` or equivalent graph visualization software for TF-TF network display.

### 2.2 Hardware requirements

1. A personal workstation with approximately `16 GB` RAM and `~10` CPU cores is sufficient for a reduced tutorial-scale analysis.
2. Larger datasets and the pySCENIC motif-pruning step benefit from HPC execution.
3. For full pySCENIC processing, plan for high-memory nodes; in this project, the regulon inference step is treated as an external high-resource analysis and may require `>60 GB` RAM depending on dataset size.

### 2.3 Input data

1. GEO accession `GSE123813`, including the raw count matrix and associated cell-level metadata.
2. Cell metadata containing at least cell barcodes, patient identifiers, treatment labels, and, when available, source-study cell-type annotations.
3. User-provided single-cell RNA sequencing data in an equivalent genes-by-cells format can also be used if matching metadata are available.

### 2.4 Reference files for regulatory analysis

1. Transcription factor list for pySCENIC, for example `TF_names_v_1.01.txt`.
2. Human `hg38` cisTarget ranking databases and motif annotations required for pySCENIC context pruning.
3. If the downstream notebook is used without rerunning pySCENIC, the precomputed GRN files `expr_mat.adjacencies.tsv`, `regulons.csv`, and either `auc_mtx.csv` or `final.loom`.

## 3 Methods

### 3.1 Create a reproducible analysis environment

1. Clone or download the repository to a Linux-accessible working directory.
2. Build the container image from the provided recipe when reproducible execution is required. A typical command is `apptainer build --fakeroot pstime.sif env/pstime.def`.
3. If a container is not used, recreate the environment from `env/environment.yml`, making sure that the package versions remain synchronized with the notebook used for the analysis.
4. Launch JupyterLab inside the environment and open `scripts/pstime_protocol.ipynb` or `final/final_protocol.ipynb` as the working notebook.

Critical. Use a fixed environment for the full workflow. Small differences in package versions can change the nearest-neighbor graph, clustering, UMAP layout, and downstream activity scores.

### 3.2 Download and organize the example dataset

1. Create a dedicated data directory, for example `data/GSE123813`.
2. Download the metadata and count matrix files associated with GEO accession `GSE123813`.
3. Keep the original file names and document the download date if the protocol is being reused as a teaching or benchmarking resource.
4. Store the raw input files separately from derived objects such as filtered matrices, figures, and pseudotime outputs.

### 3.3 Load the count matrix and metadata into an AnnData object

1. Read the count matrix and metadata table into Python.
2. Transpose the count matrix if needed so that cells are rows and genes are columns before creating the `AnnData` object.
3. Align the metadata to the expression matrix by cell barcode and confirm that the order of cells is identical in both objects.
4. Record the initial dimensions of the dataset and inspect whether duplicated barcodes or missing metadata entries are present.

Critical. Do not continue until cell identifiers match exactly between the metadata and the expression matrix. Misaligned metadata will invalidate every downstream biological interpretation.

### 3.4 Inspect the dataset and define the biological analysis scope

1. Review the number of cells, number of genes, available metadata fields, treatment labels, and patient representation.
2. Determine whether the study question should be addressed jointly across all T cells or separately within biologically coherent compartments such as CD4+ and CD8+ cells.
3. Inspect whether pre-treatment and post-treatment cells occupy overlapping manifolds or whether they form strongly separated state spaces.
4. If treatment conditions are topologically disconnected or dominated by condition-specific cell states, plan separate trajectory analyses and compare the results afterward rather than forcing all cells into a single pseudotime.

### 3.5 Select the cells of interest and validate cell-state annotations

1. Subset the dataset to the T-cell compartment relevant to the biological question.
2. In this workflow, CD4+ and CD8+ analyses are treated as distinct use cases because they represent different differentiation programs and should not be mixed without strong justification.
3. Use author-provided annotations when available, and refine them with canonical marker genes.
4. If annotations are missing or weak, use an automated annotation framework such as `celltypist` as a starting point and then manually verify the labels.
5. Confirm that expected markers support the chosen labels. In the example workflow, markers such as `CXCR4` for naive-like cells, `FOXP3` for Treg, `CXCL13` for Tfh, and `KLRB1` for Th17-like states help validate annotation quality.

Critical. Annotation quality is one of the main determinants of whether trajectory inference will be biologically interpretable. A poor annotation step propagates directly into root selection, branch labeling, and regulatory interpretation.

### 3.6 Perform quality control and normalization

1. Filter genes detected in very few cells, for example fewer than `5` cells.
2. Remove low-quality cells using dataset-specific thresholds for total UMI counts, number of detected genes, and mitochondrial transcript percentage.
3. Normalize counts per cell to a fixed library size, apply log transformation, identify highly variable genes, scale the matrix, and compute principal components.
4. Inspect QC distributions before fixing thresholds and document any deviations from the default tutorial settings.

Critical. The thresholds used in the example notebook are dataset-specific examples rather than universal defaults. Overly permissive filtering retains damaged cells, whereas overly stringent filtering can remove rare transitional states that are essential for trajectory analysis.

### 3.7 Correct patient effects, cluster the cells, and compute a UMAP embedding

1. Compute PCA on the filtered and normalized matrix.
2. If patient identity is a dominant source of variation, apply `Harmony` to the PCA coordinates using patient ID as the batch variable.
3. Build the nearest-neighbor graph on the corrected latent space, calculate Leiden clusters, and compute a UMAP embedding for visualization.
4. Plot the embedding colored by cell type, patient, and treatment condition to confirm that the main structure reflects biology rather than patient-specific artifacts.
5. Tune clustering resolution and neighborhood parameters according to the biological granularity of interest, and document the values used in the final analysis.

Critical. UMAP is useful for visualization, but trajectory-learning methods can be sensitive to embedding choices. Important conclusions should be cross-checked against PCA or batch-corrected latent spaces rather than accepted solely on the basis of a visually appealing embedding.

### 3.8 Choose a biologically plausible trajectory root

1. Select the trajectory root using prior biological knowledge, marker expression, and cluster identity rather than visual position alone.
2. In the example workflow, naive-like T cells are used as the default root because they represent the least differentiated state within the analyzed continuum.
3. When a truly naive population is absent, choose the earliest biologically plausible precursor state, such as a memory-like or stem-like compartment, and justify the choice explicitly.
4. Save the root definition together with the final metadata so that the pseudotime orientation can be reproduced exactly.

Critical. Root choice determines pseudotime direction. An implausible root can invert biological interpretation and change the ranking of genes, pathways, and regulators associated with progression.

### 3.9 Infer trajectories with complementary methods

#### 3.9.1 PAGA

1. Run `PAGA` on the annotated states or on unsupervised clusters to obtain a coarse-grained view of connectivity.
2. Use the PAGA graph to determine whether the selected cell subset forms a single connected manifold.
3. Remove clearly disconnected populations if they do not belong to the biological process under study.

#### 3.9.2 Monocle 3

1. Learn a principal graph on the selected embedding and assign pseudotime values from the chosen root cells.
2. Visualize pseudotime and the principal graph on the embedding.
3. Inspect sensitivity to neighborhood construction, embedding parameters, and partitioning behavior before fixing the final trajectory.

#### 3.9.3 Slingshot

1. Run `Slingshot` using cluster labels and a biologically justified starting cluster.
2. Compare the inferred lineage structure with the Monocle 3 result.
3. Use Slingshot as a robustness analysis to determine whether broad lineage structure is stable across trajectory methods.

#### 3.9.4 Compare outputs across methods

1. Accept a trajectory only when topology, marker trends, and biological interpretation agree across PAGA, Monocle 3, Slingshot, and relevant literature.
2. If the methods disagree strongly, revisit the selected cell subset, annotation strategy, batch correction, or root definition before proceeding.

### 3.10 Estimate transcription factor activity along pseudotime with decoupler

1. Retrieve a human TF-target prior network with `decoupler`, for example `CollecTRI`.
2. Score TF activity with the univariate linear model (`ULM`) on the single-cell object.
3. Rank TFs according to their association with pseudotime, for example by distance correlation against the pseudotime order.
4. Visualize the top regulators on the UMAP and as binned trends along pseudotime.

Note. TF activity scores inferred with decoupler summarize coordinated target-gene behavior and should not be interpreted as direct measurements of TF transcript abundance.

### 3.11 Identify genes associated with pseudotime progression and branch divergence

1. Use a graph-aware statistic such as Moran's I to identify genes that vary smoothly along the inferred manifold.
2. Plot the top pseudotime-associated genes on the embedding to confirm that their behavior is consistent with the proposed trajectory.
3. Perform additional differential expression analyses between branches, terminal states, treatment conditions, or manually defined trajectory segments as needed.
4. Keep the statistical framework consistent across comparisons and state clearly whether the analysis is pseudotime-driven, branch-driven, or condition-driven.

### 3.12 Perform pathway enrichment analysis

1. Export significant pseudotime-associated genes for pathway over-representation analysis using resources such as Reactome or Enrichr.
2. Complement gene-list enrichment with single-cell pathway scoring using curated collections such as `Hallmark` gene sets in `decoupler`.
3. Compare pathway behavior across cell types, treatment conditions, and pseudotime intervals rather than interpreting pathway scores in isolation.

### 3.13 Integrate precomputed pySCENIC outputs for regulatory network analysis

1. When full GRN inference is required, run `pySCENIC 0.12.1` outside the main notebook using the standard `grn`, `ctx`, and `aucell` steps.
2. In the workflow repository, the downstream notebook does not execute pySCENIC from raw counts. Instead, it assumes that `expr_mat.adjacencies.tsv`, `regulons.csv`, and AUCell-derived outputs have already been generated.
3. Import the adjacency matrix and regulon definitions, keep the high-confidence TF-target edges, and prune the network to interactions supported both by co-expression and motif-backed regulon enrichment.
4. Re-score the filtered GRN on the single-cell object with `decoupler` to compare regulon behavior across pseudotime, cell states, or branches.

Critical. The downstream protocol is only fully reproducible if the upstream pySCENIC inputs, databases, and command lines are archived together with the notebook outputs.

### 3.14 Identify branch-associated regulatory programs

1. Subset the trajectory to the branch of interest, for example the naive-to-Treg arm.
2. Recompute GRN-based TF activity on the subset and rank the regulators by association with branch-specific pseudotime.
3. Compare branch-associated TFs with canonical markers, pathway results, and global pseudotime trends to prioritize candidate regulators that may drive lineage divergence.

### 3.15 Construct TF-TF subnetworks and visualize candidate regulators

1. Restrict the regulatory network to transcription-factor targets or curated TF lists when generating TF-TF subnetworks.
2. Summarize activity or expression in representative cell states, for example naive, Treg, or Tfh populations.
3. Visualize the resulting subnetwork in `Cytoscape` or directly with `decoupler` network plotting functions.
4. Prioritize regulators that are both dynamically active along the trajectory and central within the network.

## 4 Notes

1. Analyze pre-treatment and post-treatment cells jointly only when the manifold suggests a shared continuum. Large treatment-induced composition shifts are often better handled with separate trajectories and a later comparison.
2. The choice of Leiden resolution, neighborhood size, batch-correction strategy, and UMAP parameters can all change the apparent topology. Treat these settings as sensitivity-analysis parameters rather than fixed truths.
3. Pseudotime is inferred, not measured. It provides a relative ordering of cells within the selected manifold rather than an absolute temporal axis.
4. The interpretation of branch points must be supported by marker genes, pathway behavior, and the literature. Not every bifurcation corresponds to a true fate decision.
5. decoupler-based TF activities and pySCENIC-derived regulons are hypothesis-generating. They should be used to prioritize mechanisms for follow-up rather than as proof of direct causality.
6. pySCENIC motif pruning is memory-intensive and is best run in a containerized or HPC setting. Retain the exact database versions and command lines used for the upstream GRN run.
7. Very small groups can destabilize branch-specific differential expression or regulon comparisons. As a practical guideline, aim for roughly `>=200` cells per condition or branch when possible.
8. If a key transcription factor has weak or undetectable mRNA expression, do not interpret absence too strongly. Check target-gene behavior and regulon activity before concluding that the regulator is inactive.
9. Archive the final environment definition or container image together with the notebook outputs so that the protocol remains reproducible on HPC systems and future software versions.

## References

1. GitHub workflow repository: `https://github.com/rogercasalsfr/cancer-pseudotime-grn-workflow`
2. Add the full bibliography for the companion manuscript here in Springer/MiMB style before submission, including the source dataset, trajectory-inference tools, regulatory-network tools, and pathway-analysis resources cited in the final text.
