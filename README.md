# Immuno trajectory GRN integrative workflow

This repository gives you one container recipe and one main notebook.

If you follow the steps below, you can reproduce the workflow in `workflow/protocol.ipynb` from the beginning through the final, taking into account that scenic inference step should be previously ran in your computer.

## What to use

Use these files:

- `env/pstime.def`: recipe used to build the image
- `env/environment.yml`: conda environment specification used inside the image
- `workflow/protocol.ipynb`: main notebook
- `check_container.sh`: one-command validation script

The repository tracks the recipe, not the built container image. You build `pstime.sif` locally from `env/pstime.def`.

## Before you start

You need:

- Linux or WSL
- Apptainer installed
- internet access for building the image and downloading the public GEO example files
- enough disk space for the image build

## Step 1. Build the image locally

From the repository root, run:

```bash
apptainer build --fakeroot pstime.sif env/pstime.def
```

If your system does not support `--fakeroot`, run:

```bash
sudo apptainer build pstime.sif env/pstime.def
```

The resulting `pstime.sif` is a local build artifact and is ignored by Git.

## Step 2. Check that the local image works

Run:

```bash
./check_container.sh
```

This script checks:

- that Apptainer is available
- that your local `pstime.sif` exists
- that Python starts inside the container
- that the notebook packages import correctly
- that Jupyter Lab and `nbconvert` are available

If you want to check a different image path, you can pass it as an argument:

```bash
./check_container.sh /path/to/pstime.sif
```

## Step 3. Start Jupyter Lab

From the repository root, run:

```bash
apptainer -q exec --bind "$PWD":/workspace pstime.sif \
  python -m jupyter lab \
  --no-browser \
  --ip=0.0.0.0 \
  --port=8888 \
  --ServerApp.root_dir=/workspace
```

Then open the URL shown by Jupyter in your browser.

Inside Jupyter, open:

- `workflow/protocol.ipynb`

Important:

- use `python -m jupyter ...` exactly as shown above
- do not run `jupyter` through `bash -lc 'jupyter ...'`

## Step 4. Run the notebook

The notebook `workflow/protocol.ipynb` is now fully reproducible from start to finish inside the container environment.

The workflow includes:

1. downloading the public GEO example data
2. reading metadata and count matrices
3. building the `AnnData` object
4. preprocessing and quality control
5. patient-effect correction with Harmony
6. clustering and UMAP visualization
7. trajectory inference and pseudotime analysis
8. transcription factor activity analysis
9. integration of GRN/pySCENIC-derived outputs
10. regulatory network interpretation and visualization

The notebook is designed to be run sequentially from the first cell to the last cell. For best reproducibility, run it from the repository root using the container environment described above.


## Example data used by the notebook

The first notebook cells create a local data directory and download these public files:

- `GSE123813_scc_metadata.txt.gz`
- `GSE123813_scc_scRNA_counts.txt.gz`

They are downloaded into:

- `workflow/data/GSE123813/`

So if the notebook asks for internet access during the first run, that is expected.

## Quick smoke test without opening Jupyter

If you only want to test the container manually, run:

```bash
apptainer -q exec pstime.sif python - <<'PY'
import scanpy, decoupler, pandas, numpy, pyslingshot, py_monocle, harmonypy
import scipy.sparse
import matplotlib.pyplot as plt
print('container OK for protocol.ipynb up to Scenic pruning')
PY
```

## What was validated

A fresh image built from `env/pstime.def` was validated on April 27, 2026.

Validated successfully:

- the image build
- the conda environment `pstime_env`
- all package names declared in `env/environment.yml`
- the notebook import set needed up to `# Scenic pruning step`
- `python -m jupyter lab --version`
- `python -m nbconvert --version`
- a non-interactive execution of the notebook up to the cell before `# Scenic pruning step`

## Summary

For this repository, the easy path is:

1. build `pstime.sif`
2. run `./check_container.sh`
3. launch Jupyter Lab
4. run `workflow/protocol.ipynb` up to the cell before `# Scenic pruning step`
