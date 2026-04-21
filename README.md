# Cancer pseudotime GRN workflow

This repository collects the material used for a *pseudotime* and gene regulatory network (GRN) workflow based on *single-cell RNA-seq* data.

This README preserves the original project narrative and repository structure. The step-by-step execution notes, validation notes, and troubleshooting bullets below were added later to make local execution more reproducible without obscuring the original authorship of the project itself.

## Repository structure

- `env/pstime.def`: Singularity/Apptainer recipe used to build the `.sif` image.
- `env/environment.yml`: single source of truth for the Conda environment used by the image build.
- `scripts/pstime_protocol.ipynb`: main tutorial notebook for the protocol.
- `scripts/methods.ipynb`: complementary notebook with additional methods.
- `scripts/data/GSE123813/*`: example data used by the notebooks.

## Requirements

- Linux with [Apptainer](https://apptainer.org/) or [SingularityCE](https://sylabs.io/singularity/) installed.
- Enough disk space to build the image locally. The build can take several GB.
- Recommended: `--fakeroot` or administrator privileges for the local build.
- Network access during the build. The recipe pulls a base container image and clones `py-monocle` from GitHub.

## Build the `.sif` image

`env/environment.yml` is the only environment file that matters in this repository. The container recipe copies that file into the image and creates `pstime_env` from it.

The recipe is designed to:

1. Install system dependencies (`git`, `build-essential`).
2. Create the `pstime_env` conda environment from `env/environment.yml`.
3. Install `py-monocle` from GitHub inside the container.
4. Run a small import check during the build so obviously broken images fail early.

### Option A (recommended): Apptainer

From the repository root:

```bash
apptainer build --fakeroot pstime.sif env/pstime.def
```

If you have root permissions:

```bash
sudo apptainer build pstime.sif env/pstime.def
```

### Option B: SingularityCE

```bash
sudo singularity build pstime.sif env/pstime.def
```

## Run the tutorial

The commands below assume that you are in the repository root.

### 1) Launch Jupyter Lab inside the container

Use `--cleanenv` so host Python variables such as `PYTHONPATH` do not leak into the container runtime.

```bash
apptainer exec --cleanenv pstime.sif \
  jupyter lab --ip 0.0.0.0 --port 8888 --no-browser
```

What to expect:

- Jupyter prints a local URL with a token, usually something like `http://127.0.0.1:8888/lab?token=...`.
- Open that URL in your browser.
- Navigate to `scripts/pstime_protocol.ipynb` to follow the main tutorial.
- Stop the server with `Ctrl+C`.

> If you use SingularityCE, replace `apptainer` with `singularity`.

### 2) Quick runtime verification

This checks that the core scientific and Jupyter stack can be imported from inside the image.

```bash
apptainer exec --cleanenv pstime.sif \
  python -c "import scanpy, decoupler, sklearn, six, dateutil, jupyterlab, jupyter_client; print('OK')"
```

### 3) Optional non-interactive execution of the notebook

This is useful when you want to validate the notebook from the command line.

```bash
apptainer exec --cleanenv pstime.sif \
  jupyter nbconvert --to notebook --execute scripts/pstime_protocol.ipynb --output pstime_protocol.executed.ipynb
```

## Notes that improve day-to-day use

- The container entrypoint already exposes `pstime_env` on `PATH`, so the image should use the intended Python by default.
- The example data in `scripts/data/GSE123813/` can be used directly from the notebooks.
- If you already have an older local `pstime.sif`, rebuild it after changing `env/pstime.def` or `env/environment.yml`.
- If Apptainer prints messages about missing `squashfuse`, `fuse2fs`, or `gocryptfs`, the image may still run, but startup can be slower because Apptainer converts the SIF into a temporary sandbox.

## Troubleshooting

### `ModuleNotFoundError: No module named 'six.moves'`

In this repository, that error was traced to the host environment leaking `PYTHONPATH` into the container runtime. On this machine, the host `PYTHONPATH` pointed to external paths such as Amber and qtools packages, and one of those shadowed the container's own `six.py`.

The fix is to run the container with `--cleanenv`:

```bash
apptainer exec --cleanenv pstime.sif \
  jupyter lab --ip 0.0.0.0 --port 8888 --no-browser
```

If you want to inspect the problem explicitly on your machine:

```bash
printf '%s\n' "$PYTHONPATH"
```

### Build fails before Jupyter starts

Check the build first:

```bash
apptainer build --fakeroot pstime.sif env/pstime.def
```

If the build succeeds, then check the runtime stack:

```bash
apptainer exec --cleanenv pstime.sif python -c "import jupyterlab, jupyter_client, dateutil, six; print('OK')"
```

## Validation notes

The following checks were run on April 14, 2026 in this environment:

- `apptainer build --fakeroot /tmp/pstime-readme-test.sif env/pstime.def`: completed successfully.
- `apptainer exec --cleanenv /tmp/pstime-readme-test.sif python -c "import six, scanpy, jupyterlab, jupyter_client; print('OK')"`: completed successfully.
- `apptainer exec --cleanenv /tmp/pstime-readme-test.sif bash -lc 'jupyter lab --version && jupyter nbconvert --version'`: returned `4.5.6` and `7.17.1`.
- The pre-existing local `pstime.sif` failed without `--cleanenv` because host `PYTHONPATH` leaked into the container runtime.
- A full `jupyter nbconvert --execute scripts/pstime_protocol.ipynb` run was started, but it was not confirmed to completion in this session, so the command is kept as documented and recommended, but not marked as fully validated here.

## Citation and context

This repository contains supporting material for a *pseudotime* and GRN workflow. If you use it in reproducible environments such as HPC systems or shared clusters, it is reasonable to preserve `pstime.sif` as a build artifact. If you intend to store the image in Git, use Git LFS or release assets rather than a regular git blob.
