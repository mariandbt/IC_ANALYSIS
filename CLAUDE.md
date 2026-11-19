# IC_ANALYSIS: context for Claude on Hyperion

Marian's PhD (NEXT collaboration, 0νββ in Xe-136, high-pressure gas TPC). This repository reruns the 2025
NEXT-100 **WLS-fibers vs PMTs** simulation with Invisible Cities (IC), to compare the energy plane of
fibers (108 channels) with the PMTs (60), with Kr-83m (41.5 keV) and 0νββ (Q_bb = 2458 keV).
Read `README.md` for the layout. Work in English. Explain simply and step by step; don't overcomplicate.

## Rules (Marian's, they override defaults)
- **Never launch a cluster job without permission.** Before any `sbatch`/`srun`/`salloc`/`submit.sh --submit`
  (tests too), describe it: what it runs, input → output, resources (tasks, CPUs, memory, time limit),
  expected duration, and ask. One approval covers one job. Do not chain steps (`--after`).
- Run the pipeline **one step at a time**: detsim → check → copy outputs to `/data` **from the login node**
  (compute nodes can't write `/data`; `tools/store.sh`) → hypathia → check → copy → dorothea.
- All jobs send start/end/fail emails (`--mail-type=BEGIN,END,FAIL`), already set in `slurm/*.slurm`.
- Never push. Marian commits herself (or with `/sess-wrapup` on her laptop). No Claude co-author lines.
- Do not invent results or references. Mark your own estimates as estimates.
- Don't run heavy work on the login node (`hyperion-login-01`); notebooks run on a compute node
  (VS Code job `slurm/vscode.slurm`, kernel **IC_ANALYSIS (IC-3.8)**, which already has the env.sh paths).
- `.bashrc` prints `module: command not found`: harmless.

## Sample names
`1Kev`, `50Kev`, `100Kev` mean **thousands of events** (1Kev = 1000 events per file), not energy. `300ev` = 300 events.

## Pipeline
| Step | Input | Slicing | City / tool | Output |
|---|---|---|---|---|
| 0 slim | nexus `/data/marian/s2simulation/Kr/<sample>_<i>.next.h5` (57 GB) | one file per task | `tools/slim_nexus.py` | `Kr_slim/<sample>_<i>.next.h5` (0.05 GB) |
| 1 detsim | slim nexus file | 50 000 events/file → 5 chunks of 10 000 (`event_range`) | detsim: hits → electrons → drift → EL light → waveforms | `<sample>_<i>_<c>.detsim.h5` |
| 2 hypathia | detsim output | same chunks | hypathia: S1/S2 peak finding | `.hypathia.h5` (PMAPs) |
| 3 dorothea | hypathia output | same chunks | dorothea: Kr point reconstruction | `.dorothea.h5` (kDST) → `05_dorothea_kr` |

Outputs: `$ICA_OUT=/scratch/marian/IC_ANALYSIS_OUT/<sample>/<fibers|pmts>_g<EL_GAIN>/<city>/`.
Chunks: `run_city.slurm` with `--export=ALL,EL_GAIN=1050,ICA_NCHUNK=5,ICA_CHUNK_EVENTS=10000`; array task t →
file i = (t-1)/5+1, chunk c = (t-1)%5, events [c·10000, (c+1)·10000).

## Why slim files (important)
Every IC city ends with `components.copy_mc_info` → `mcinfo_io.read_mc_tables`, which loads the input's MC
tables **whole** into pandas. In the EL-off Kr files `/MC/particles` has 93M rows (56.5 GB), 99.7 % `ie-`
(ionization electrons tracked by nexus). The 2026-11-18 run (jobs 8043384–8043420, 12 GB/task) died of
OUT_OF_MEMORY at the end of detsim; 2025 jobs had asked for 200 GB – 2 TB. Detsim only reads `/MC/hits`
(`MC_hits_from_files` → `load_mchits_df`), so `slim_nexus.py` drops only the `ie-` rows (keeps the 253k
`e-`/`gamma` rows and every other table, checks row counts and events). IC itself is not modified.
Explained in `notebooks/03_detsim.ipynb`, section "Slim nexus inputs and reading in chunks".

## Settings of the new runs (choice A)
EL gain 1050 ph/e (nexus yield at 10 bar, 1.3 kV/cm/bar), diffusion 1.072 / 0.267 mm/√cm (Simón 2018 scaled
to 10 bar), lifetime 12 ms. The 2025 runs used gain 365 and IC-default diffusion 1.20 / 0.30.
2025 fibers Kr result (reproduced): 3.84 % FWHM after lifetime correction, τ = 12.44 ms, 5165 events, R < 30 mm.
Fiber S1 in detsim is a placeholder (60 PMT S1 waveforms copied into 108 channels): see 03 and 07.

## Status (2026-11-19)
- Job 0 done (jobs 8049441, 8065923): all 40 slim files in `/data/marian/s2simulation/Kr_slim/` (2.9 GB, all checks
  passed, 50 000 events each). `samples.sh` points the 50Kev sample at `Kr_slim`.
- Detsim test, file 1 chunk 0, gain 1050, 4 GB: fibers 8066025, PMTs 8066026. When done: `seff <jobid>_1`
  (time, memory) to size the full run (40 files × 5 chunks per detector) — ask Marian before launching it.
- Before hypathia: its input path in `pipeline.sh` still points to `$ICA_OUT` (scratch); change it to the
  `/data` copy (`/data/marian/IC_ANALYSIS/...`, see `tools/store.sh`).
- `icana/paths`: `file_index` / `chunk_index` handle chunk files `<sample>_<i>_<c>`; `EL_GAIN` defaults to 1050.
- Plots: `icana/plots.py` reproduces the 2025 notebook plots (`set_style`, `hits_projections`, `waveforms`,
  `fib_vs_pmt`, `save` → `work/figures/*.pdf`). Also `pmap`, `dst_overview`, `dst_compare`, `peak_fit`,
  `lifetime`, `peak_in_z_slices`. In 03, 04 and 05 (section "Plots (2025 style)", `SAVE = True` saves them).
- Job names: `<city>_<detector>` from submit.sh (e.g. `detsim_fibers`), `slim_nexus`, `notebook`, `vscode`.

## Notebooks (one per step; header cell says purpose, inputs, checks)
00 inventory of all files and settings · 01 nexus inputs · 02 light tables (fiber/PMT ratio prediction) ·
03 detsim waveforms (+ slim check) · 04 hypathia PMAPs · 05 dorothea Kr resolution · 06 Q_bb (skeleton) ·
07 fiber S1 from nexus vs dark counts. `USE_NEW = False` reads the 2025 outputs, `True` the new ones.
Executed copies: `sbatch slurm/run_notebook.slurm notebooks/<nb>` (ask first) → `work/executed/`.
