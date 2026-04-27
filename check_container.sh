#!/usr/bin/env bash
set -euo pipefail

IMAGE_ARG="${1:-pstime.sif}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "$IMAGE_ARG" = /* ]]; then
  IMAGE_PATH="$IMAGE_ARG"
elif [[ -f "$ROOT_DIR/$IMAGE_ARG" ]]; then
  IMAGE_PATH="$ROOT_DIR/$IMAGE_ARG"
else
  IMAGE_PATH="$IMAGE_ARG"
fi

echo "Cancer pseudotime container check"
echo "Repository: $ROOT_DIR"
echo "Image: $IMAGE_PATH"
echo

if ! command -v apptainer >/dev/null 2>&1; then
  echo "ERROR: apptainer is not installed or not available in PATH."
  exit 1
fi

if [[ ! -f "$IMAGE_PATH" ]]; then
  echo "ERROR: image not found: $IMAGE_PATH"
  echo "Build it locally with: apptainer build --fakeroot pstime.sif env/pstime.def"
  exit 1
fi

if [[ ! -f "$ROOT_DIR/scripts/final_protocol.ipynb" ]]; then
  echo "ERROR: scripts/final_protocol.ipynb was not found in $ROOT_DIR"
  exit 1
fi

echo "Step 1/4: Apptainer"
apptainer --version

echo
echo "Step 2/4: Python inside the container"
apptainer -q exec "$IMAGE_PATH" python - <<'PY'
import sys
print(sys.executable)
print(sys.version)
PY

echo
echo "Step 3/4: Core notebook imports"
apptainer -q exec "$IMAGE_PATH" python - <<'PY'
import importlib
modules = [
    "decoupler",
    "pandas",
    "scanpy",
    "numpy",
    "pyslingshot",
    "py_monocle",
    "harmonypy",
    "scipy.sparse",
    "matplotlib.pyplot",
]
for name in modules:
    importlib.import_module(name)
    print(f"OK {name}")
print("All core imports are available.")
PY

echo
echo "Step 4/4: Jupyter tools"
apptainer -q exec "$IMAGE_PATH" python -m jupyter lab --version
apptainer -q exec "$IMAGE_PATH" python -m nbconvert --version

echo
echo "Container check passed."
echo "Next step:"
echo "apptainer -q exec --bind \"$ROOT_DIR\":/workspace \"$IMAGE_PATH\" python -m jupyter lab --no-browser --ip=0.0.0.0 --port=8888 --ServerApp.root_dir=/workspace"
