# Cancer pseudotime GRN workflow

Aquest repositori recull el material del protocol de *pseudotime* i inferència de xarxes reguladores (GRN) a partir de dades de *single-cell RNA-seq*.

## Estructura del repositori

- `env/pstime.def`: recepta de Singularity/Apptainer per construir la imatge `.sif`.
- `env/environment.yml`: entorn conda exportat que s'utilitza com a base de la imatge.
- `env/pstime.yml`: còpia de l'entorn original.
- `scripts/pstime_protocol.ipynb`: tutorial principal del protocol.
- `scripts/methods.ipynb`: notebook complementari amb mètodes.
- `scripts/data/GSE123813/*`: dades d'exemple per executar el tutorial.

## Requisits

- Linux amb [Apptainer](https://apptainer.org/) o [SingularityCE](https://sylabs.io/singularity/) instal·lat.
- Espai en disc suficient (la construcció de la imatge pot ocupar diversos GB).
- Recomanat: `--fakeroot` o permisos d'administrador per fer `build` local.

## Construcció de la imatge `.sif`

La recepta ja està preparada per:

1. Instal·lar dependències del sistema (`git`, `build-essential`).
2. Corregir l'`environment.yml` (neteja de `prefix`, canvi de nom de l'entorn).
3. Crear l'entorn `pstime_env` amb `mamba`.
4. Instal·lar `py-monocle` des de GitHub dins del contenidor.

### Opció A (recomanada): Apptainer

Des de l'arrel del repositori:

```bash
apptainer build --fakeroot pstime.sif env/pstime.def
```

Si tens permisos root:

```bash
sudo apptainer build pstime.sif env/pstime.def
```

### Opció B: SingularityCE

```bash
sudo singularity build pstime.sif env/pstime.def
```

## Com executar el tutorial

### 1) Llançar Jupyter Lab dins del contenidor

```bash
apptainer exec --bind "$PWD":/workspace pstime.sif \
  bash -lc 'cd /workspace && jupyter lab --ip 0.0.0.0 --port 8888 --no-browser'
```

- Obre al navegador la URL que mostri Jupyter (normalment `http://127.0.0.1:8888/...`).
- Navega a `scripts/pstime_protocol.ipynb` per seguir el tutorial principal.

> Si uses SingularityCE, substitueix `apptainer` per `singularity`.

### 2) Execució no interactiva del notebook (opcional)

Per validar que el tutorial corre de cap a peus:

```bash
apptainer exec --bind "$PWD":/workspace pstime.sif \
  bash -lc 'cd /workspace && jupyter nbconvert --to notebook --execute scripts/pstime_protocol.ipynb --output pstime_protocol.executed.ipynb'
```

## Verificació ràpida de la imatge

Per comprovar que l'entorn del contenidor és l'esperat:

```bash
apptainer exec pstime.sif python -c "import scanpy, decoupler, sklearn; print('OK')"
```

## Notes importants

- La recepta `env/pstime.def` ja exporta el `PATH` perquè `pstime_env` sigui l'entorn per defecte dins la imatge.
- Les dades d'exemple del directori `scripts/data/GSE123813/` es poden usar directament al notebook.
- Si el `build` falla per permisos, prova amb `--fakeroot` o fes el `build` en una màquina/HPC on estigui habilitat.

## Citació i context

Aquest repositori conté material de suport per al protocol de treball de *pseudotime* i GRN. Si l'utilitzes en entorns reproductibles (HPC, clústers, etc.), es recomana conservar la imatge `pstime.sif` com a artefacte versionat.
