"""Copy a nexus file without the ionization-electron rows ("ie-") of /MC/particles.

Why: in the EL-off Kr files ~99.7 % of /MC/particles are ie- (about 1850 per event, 93M rows,
56 GB per file). IC cities copy the MC tables of their input at the end of the run
(components.copy_mc_info -> mcinfo_io.read_mc_tables loads each table whole), which needs
more memory than a 1-CPU job has. No IC city used here (detsim, hypathia, dorothea) and no
notebook reads /MC/particles; detsim builds the signal from /MC/hits.

Every other table is copied unchanged. The particles table is read in chunks of CHUNK rows,
so memory stays at ~1 GB. The output is written as <out>.part and renamed only after checks.

    python tools/slim_nexus.py <in.next.h5> <out.next.h5>
"""
import os, sys, time
import numpy as np
import tables as tb

CHUNK = 1_000_000
DROP  = b"ie-"

src, dst = sys.argv[1], sys.argv[2]
part = dst + ".part"
t0 = time.time()
filters = tb.Filters(complevel=4, complib="zlib")

with tb.open_file(src) as fin, tb.open_file(part, "w", filters=filters) as fout:
    for node in fin.walk_nodes("/"):
        if node._v_pathname == "/":
            continue
        parent = os.path.dirname(node._v_pathname) or "/"
        if isinstance(node, tb.Group):
            fout.create_group(parent, node._v_name, createparents=True)
        elif node._v_pathname != "/MC/particles":
            node.copy(fout.get_node(parent), filters=filters)
    tin  = fin.root.MC.particles
    tout = fout.create_table("/MC", "particles", description=tin.description,
                             filters=filters, expectedrows=tin.nrows // 300)
    n_in = n_keep = 0
    names = {}
    for start in range(0, tin.nrows, CHUNK):
        rows = tin.read(start, min(start + CHUNK, tin.nrows))
        keep = rows[rows["particle_name"] != DROP]
        tout.append(keep)
        n_in += len(rows); n_keep += len(keep)
        for k, c in zip(*np.unique(rows["particle_name"], return_counts=True)):
            names[k] = names.get(k, 0) + int(c)
        if (start // CHUNK) % 10 == 0:
            print(f"  {start + len(rows):>11,d} / {tin.nrows:,d} rows  {time.time() - t0:7.0f} s", flush=True)
    tout.flush()

# ---- checks: output readable, same tables, same row counts except particles, same events
with tb.open_file(src) as fin, tb.open_file(part) as fout:
    for node in fin.walk_nodes("/", "Leaf"):
        p = node._v_pathname
        m = fout.get_node(p)
        if p != "/MC/particles":
            assert m.nrows == node.nrows, (p, m.nrows, node.nrows)
    ev_hits = np.unique(fin.root.MC.hits.col("event_id"))
    ev_part = np.unique(fout.root.MC.particles.col("event_id"))
    missing = np.setdiff1d(ev_hits, ev_part)
    assert len(missing) == 0, f"{len(missing)} events with hits but no particles left"
    assert fout.root.MC.particles.nrows == n_keep

os.rename(part, dst)
print("particle names in input:", {k.decode(): v for k, v in names.items()})
print(f"particles: {n_in:,d} -> {n_keep:,d} rows ({n_keep / n_in:.2%} kept); events with hits: {len(ev_hits):,d}")
print(f"size: {os.path.getsize(src) / 1e9:.1f} GB -> {os.path.getsize(dst) / 1e9:.2f} GB;  {time.time() - t0:.0f} s")
