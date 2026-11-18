#!/bin/bash
# Copy finished outputs from /scratch to /data (long-term). /data is read-only on compute nodes:
# run this on a LOGIN node.   bash tools/store.sh [sample]
# Copies only complete files (no .part), never overwrites. Delete from /scratch yourself afterwards.
set -e
cd "$(dirname "$0")/.."; source env.sh >/dev/null
DEST=/data/marian/IC_ANALYSIS
rsync -av --ignore-existing --exclude='*.part' "$ICA_OUT/${1:-}" "$DEST/"
