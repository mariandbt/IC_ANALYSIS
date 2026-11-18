# IC_ANALYSIS: NEXT-100 with WLS fibers, IC chain

Clean, reproducible version of the 2025 fibers simulation analysis (Kr-83m and 0νββ) with Invisible
Cities (IC). One notebook per step, one way to launch jobs, and every output records the settings
that produced it. Cluster rules: https://scc.dipc.org/docs/systems/hyperion/

## Layout
```
env.sh                 source it first: IC from external/IC, conda env, data paths
samples.sh             the nexus samples known to the pipeline
pipeline.sh            where each step reads and writes (used by submit.sh and the slurm job)
submit.sh              dry run of a step + the exact sbatch command (--submit to send it)
slurm/run_city.slurm   one IC city on one input file per array task
slurm/vscode.slurm     VS Code server on a compute node
config/*.template      detsim, hypathia, dorothea configs (same values as the 2025 runs)
icana/                 helpers for the notebooks: paths, checks, fits, light tables
notebooks/             00 → 07, one per step
tools/                 install_kernel.sh, vscode_tunnel.sh (run on your laptop), store.sh
external/IC            submodule: mariandbt/IC, branch fibers (pinned commit, compiled in place)
external/python_cluster  submodule: mariandbt/python_cluster
logs/, work/           slurm logs and per-task configs (not in git)
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
| – | fiber S1 vs dark counts | nexus `/MC/sns_response` | `07_s1_fibers` |

`00_pipeline_and_inventory` checks that all inputs exist, are readable and were made with the same settings.

## Where files go (Hyperion rules)
- Jobs read inputs from `/data` (read-only on compute nodes) and write to **`$ICA_OUT=/scratch/marian/IC_ANALYSIS_OUT/<sample>/<fibers|pmts>_g<EL_GAIN>/<city>/`**.
- `/scratch` has no backup and must stay below 80 % full; quota 2 TB. When a step is finished, copy it to
  `/data/marian/IC_ANALYSIS` from a **login node** with `bash tools/store.sh <sample>`, then delete it from `/scratch`.
- The 2025 outputs in `/data/marian/IC` are never written.

## Running a step (batch)
```bash
cd /scratch/marian/IC_ANALYSIS && source env.sh
./submit.sh detsim fibers 20250205_Next100_bb_300ev_ELoff        # dry run: plan, config, sbatch command
./submit.sh detsim fibers 20250205_Next100_bb_300ev_ELoff --submit
# or paste the printed command, e.g.
sbatch --array=2-8,11 slurm/run_city.slurm detsim fibers 20250205_Next100_bb_300ev_ELoff
squeue -u marian ;  seff <jobid>      # memory/time actually used
```
Jobs use `qos=serial` (1 CPU, up to 1000 running, 2 days). A task writes `<file>.part` and renames it only
when the file is complete and readable; tasks with an existing output are skipped (`--force` to redo).

## Running a notebook as a job (checks without an interactive session)
```bash
sbatch slurm/run_notebook.slurm notebooks/05_dorothea_kr.ipynb                    # executed copy in work/executed/
sbatch --qos=test --time=00:10:00 slurm/run_notebook.slurm notebooks/02_light_tables.ipynb   # quick, high priority
```

## Working interactively
**Terminal on a compute node** (never compute on the login nodes):
```bash
salloc --qos=regular --cpus-per-task=4 --mem=16G --time=8:00:00 srun --pty bash
cd /scratch/marian/IC_ANALYSIS && source env.sh
```
**VS Code + notebooks on a compute node** (DIPC VS Code guide):
1. Once: `bash tools/install_kernel.sh` (registers the Jupyter kernel `IC_ANALYSIS (IC-3.8)` with all paths set),
   and on your laptop add to `~/.ssh/config`:
   ```
   Host hyperion-tunnel
     HostName localhost
     Port 2222
     User marian
   ```
2. On the cluster: `sbatch slurm/vscode.slurm` (8 h, 4 CPUs, 16 GB). Note the job id.
3. On your laptop: `bash tools/vscode_tunnel.sh <jobid>` (copy it from `tools/`; leave the terminal open).
4. VS Code → Remote Explorer → `hyperion-tunnel` → open `/scratch/marian/IC_ANALYSIS`.
   Install the Python and Jupyter extensions on the remote side, open a notebook, kernel `IC_ANALYSIS (IC-3.8)`.
5. When done: `scancel <jobid>`.

## Settings (same as 2025, see the stored /config in every output)
- Pressure 10 bar (nexus), lifetime 12 ms, drift velocity 1 mm/µs, Fano 0.15, W_i 22.4 eV.
- **EL gain `EL_GAIN = 782` photons/e⁻ (env.sh)**: NEXT-100 as it runs now. Monteiro et al. 2007 (quoted as eq. 2.13 of
  the NEXT 2009 proposal): η = 140 (E/p − 0.83) p Δx, with E/p = 2.27 kV/cm/bar and p = 4 bar (Kr run June–Sept 2025,
  MartinezLema2025 Table 1) and Δx = 0.97 cm (same paper, Sec. 2) → η ≈ 782. The 2025 runs used 365 (IC default).
  Outputs carry the gain in their path (`<det>_g782/`), so runs with different gains never mix.
  Note: the nexus samples are at 10 bar; at 10 bar the same E/p would give η ≈ 1955 but needs a 22 kV gate (design limit
  20 kV, NEXT-100 detector paper), and 20 kV at 10 bar gives E/p = 2.06 → η ≈ 1673. Change with `EL_GAIN=<value> ./submit.sh ...`.
- Diffusion 1.20 / 0.30 mm/√cm (IC defaults). NEXT-White at 10 bar: 1.07 / 0.27 (Simón et al. 2018).
- S2 tables: fibers `20250408_s2_table.h5` (per EL photon, from the 500 × 100k `20240405_Next100_ie_s2` runs);
  PMTs IC `NEXT100_S2_LT.h5`. At R < 30 mm: fibers 1.35 %, PMTs 0.87 % per EL photon (ratio 1.56).
- S1: the PMT table for both. For fibers it is a placeholder: `scale_and_repeat_s1` copies the 60 PMT S1
  waveforms into 108 channels with `scaling_factor = 1`. The real fiber S1 is in the nexus files (`07_s1_fibers`).

## Known problems of the 2025 data (storage incident, Dec 2025)
- Unreadable: hypathia 50Kev files 5, 17, 18, 19, 25, 33, 39; the 300ev S1 runs; three 1Kev per-file dorothea
  outputs. The merged 2025 dorothea files are fine (made before the incident). Regenerate with `submit.sh`.
- The old working copies `/scratch/marian/IC` and `/scratch/marian/python` have zeroed files and a
  corrupted git pack. This repository uses fresh clones in `external/`.
