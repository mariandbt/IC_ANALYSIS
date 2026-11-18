# IC_ANALYSIS: NEXT-100 with WLS fibers, IC chain

Clean, reproducible version of the 2025 fibers simulation analysis (Kr-83m and 0νββ), built on
Invisible Cities (IC). Every step has its own notebook, every job is launched the same way, and every
output records the settings that produced it.

## Layout
```
env.sh              source it first: IC from external/IC, conda env, data paths
samples.sh          the nexus samples known to the pipeline
submit.sh           run one IC city over one sample as a slurm array (dry run unless --submit)
slurm/run_city.slurm  one task = one input file
config/*.template   detsim, hypathia, dorothea configs (same values as the 2025 runs)
icana/              small helpers for the notebooks: paths, checks, fits, light tables
notebooks/          00 → 06, one per step (see below)
external/IC              submodule: mariandbt/IC, branch fibers (pinned commit)
external/python_cluster  submodule: mariandbt/python_cluster (2023-25 notebooks and s2simulation modules)
logs/, work/        slurm logs and per-task configs (not in git)
```

## Pipeline
| Step | Program | Input → output | Notebook |
|---|---|---|---|
| 0 | nexus, EL off | macro → `<sample>_<i>.next.h5` (in `$NEXUS_DIR`) | `01_nexus_inputs` |
| – | light tables | fibers `20250408_s2_table.h5`, PMTs IC `NEXT100_S2_LT.h5` | `02_light_tables` |
| 1 | detsim | next → `.detsim.h5` (raw waveforms) | `03_detsim` |
| 2 | hypathia | detsim → `.hypathia.h5` (PMaps) | `04_hypathia` |
| 3 | dorothea | hypathia → `.dorothea.h5` (Kr kDST) | `05_dorothea_kr` |
| 4 | Q_bb | hypathia (0νββ) → energy | `06_qbb` |

`00_pipeline_and_inventory` checks that all inputs exist, are readable and were made with the same settings.

## Running
```bash
cd /scratch/marian/IC_ANALYSIS
source env.sh
./submit.sh detsim fibers 20250205_Next100_bb_300ev_ELoff            # dry run: plan + config of the first task
./submit.sh detsim fibers 20250205_Next100_bb_300ev_ELoff --submit   # send the jobs
./submit.sh detsim pmts   20250205_Next100_bb_300ev_ELoff 1-5 --submit   # a subset of files
squeue -u marian
```
Outputs: `$ICA_OUT/<sample>/<fibers|pmts>/<city>/<sample>_<i>.<city>.h5` (`ICA_OUT=/data/marian/IC_ANALYSIS`).
A task writes `<file>.part` and renames it only when the file is complete and readable. Tasks whose output
already exists are skipped (use `--force` to redo them). The 2025 outputs in `/data/marian/IC` are never written.

## Notebooks in VS Code
Remote-SSH to `hyperion-01.sw.ehu.es`, open `/scratch/marian/IC_ANALYSIS`, choose the kernel
`IC-3.8-2024-06-08` and run the first cell. Heavy reading (detsim waveforms) is better done on a compute
node: `srun --pty --mem=8G -t 2:00:00 bash`, then `source env.sh` and `jupyter lab --no-browser`.

## Settings (same as 2025, see the stored /config in every output)
- Pressure 10 bar (nexus), lifetime 12 ms, drift velocity 1 mm/µs, Fano 0.15, W_i 22.4 eV.
- `el_gain = 365` (IC default). nexus at 10 bar and 13 kV/cm gives 1050 ph/e. Open choice.
- Diffusion 1.20 / 0.30 mm/√cm (IC defaults). NEXT-White at 10 bar: 1.07 / 0.27 (Simón et al. 2018).
- S2 tables: fibers `20250408_s2_table.h5` (per EL photon, from the 500 × 100k `20240405_Next100_ie_s2` runs);
  PMTs IC `NEXT100_S2_LT.h5`.
- S1: the PMT table for both. For fibers it is a placeholder: `scale_and_repeat_s1` copies the 60 PMT S1
  waveforms into 108 channels with `scaling_factor = 1`, so the fiber S1 (~1.7x PMTs) is not physics.

## Known problems of the 2025 data (storage incident, Dec 2025)
- Unreadable: hypathia 50Kev files 5, 17, 18, 19, 25, 33, 39; the 300ev S1 runs; three 1Kev per-file dorothea
  outputs. The merged 2025 dorothea files are fine (made before the incident). Regenerate with `submit.sh`.
- The old working copies `/scratch/marian/IC` and `/scratch/marian/python` have zeroed files and a
  corrupted git pack. This repository uses fresh clones in `external/`.
