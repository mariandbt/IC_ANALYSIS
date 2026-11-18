# Known nexus samples: SAMPLE -> "<subfolder of $NEXUS_DIR> <first index> <last index>"
# All at 10 bar, EL off, NEXT-100 fibers geometry (checked in /MC/configuration, 2026-11-18).
declare -A SAMPLES=(
  [20250624_Next100_1Kev_ELoff_Kr]="Kr 1 50"     # Kr-83m, 50 x 1000 events. Matched fibers/PMTs sample.
  [20250626_Next100_50Kev_ELoff_Kr]="Kr 1 40"    # Kr-83m, 40 x 50000 events. 2025 fibers result (3.84% FWHM).
  [20250205_Next100_bb_300ev_ELoff]="bb 1 50"    # Xe-136 0nubb (Decay0 mode 1), 300 events per file, SECTOR_AREA. 42 files: 1, 9, 10, 12, 37, 44, 45, 47 were never produced.
)
