# Massive Scalar Field Evolution in Schwarzschild Spacetime

University project in progress. The current theory reaches the Schwarzschild
metric, the tortoise coordinate and the radial massive Klein-Gordon equation
with its effective potential. **The seven simulations completed so far are in
flat spacetime.** Schwarzschild time evolution has not been included in this
milestone.

- `report/`: the Spanish report, bibliography and institutional template.
- `src/`: the flat solver, experiment runner, explanatory figures and delivery script.
- `results/flat/`: the seven runs' tables and lossless WebP figures.

All commands run from this repository's existing root. The project is not copied
or moved to prepare a delivery.

## What was simulated?

Each run evolves a real field on a periodic interval of length `2π`, with mass
parameter `0.7`, initial field `cos(j*x)`, zero initial time derivative and final
time `20`. Four modes check dispersion; four resolutions check joint space/time
refinement. Their shared case makes seven distinct runs:

| Run | Grid points N | Spatial mode j | Check |
| --- | ---: | ---: | --- |
| N64_j2 | 64 | 2 | Refinement |
| N128_j2 | 128 | 2 | Refinement |
| N256_j1 | 256 | 1 | Dispersion |
| N256_j2 | 256 | 2 | Both |
| N256_j3 | 256 | 3 | Dispersion |
| N256_j4 | 256 | 4 | Dispersion |
| N512_j2 | 512 | 2 | Refinement |

For these initial data, the mode obeys `a'' + (j² + 0.7²)*a = 0`: it oscillates.
Its envelope remains constant because this model has no damping term and the
periodic boundaries give no net energy loss. Crossing zero is not decay. The
animation reconstructs one recorded flat mode; the Schwarzschild coordinate
diagram explains geometry and does not show an evolved field.

## Run and prepare a partial submission

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python src\run_flat_validation.py
.\report\compilar.ps1
.venv\Scripts\python src\prepare_submission.py
```

Python 3.13 and the pinned dependencies were used. Compiling requires pdfLaTeX
and Biber; the existing script detects MiKTeX. The canonical PDF is
`report/main.pdf`. The local `partial-submission/` contains only `report.pdf` and
`flat-standing-wave.gif`; it is ignored by Git. It has no HTML entry point or
duplicate source tree.

Small tables and WebP figures are versioned. Traces, CSV summaries, generated
vector PDFs, the animation, environment, compiled report and temporary files
are regenerated locally. No additional workflow documents are needed.
