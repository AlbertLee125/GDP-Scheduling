# performance_profile_gdp.py

import os
import json
import numpy as np
import matplotlib.pyplot as plt

# ── 1) Load JSON ────────────────────────────────────────────────────────────────
file_path = 'results_strip/benchmark_results_datnzig_extended_extended.json'
if not os.path.isfile(file_path):
    raise FileNotFoundError(f"Cannot find JSON file at {file_path}")
with open(file_path, 'r') as f:
    data = json.load(f)

# Filter out any “traditional” entries
data = [d for d in data if d.get('formulation') != 'traditional']

# ── 2) Instances & Solvers ─────────────────────────────────────────────────────
instances = sorted(
    {d['instance'] for d in data},
    key=lambda s: (int(s.split('_')[0]), int(s.split('_')[1]))
)

# Raw labels
raw_labels = sorted({f"{d['formulation']}_{d['reform']}" for d in data})
print("Detected raw solver labels:", raw_labels)

# Map to your six clean names
rename_map = {
    'bigM_altered':    'altered_bigm',
    'hull_altered':    'altered_hull',
    'reagg_MIP':       'altered_reagg',
    'bigM_tres':       'tres_bigm',
    'hull_tres':       'tres_hull',
    'reagg_tres_MIP':  'tres_reagg',
}
solvers = [rename_map.get(r, r) for r in raw_labels]

# ── 3) Build time & objective maps ─────────────────────────────────────────────
time_map = {}
obj_map  = {}
gap_map  = {}
# Populate maps with data from JSON
for d in data:
    inst = d['instance']
    raw  = f"{d['formulation']}_{d['reform']}"
    sol  = rename_map.get(raw, raw)
    time_map[(inst, sol)] = d['time_sec']
    obj_map [(inst, sol)] = d.get('objective', np.nan)
    gap_map [(inst, sol)] = d.get('gap',       np.nan)

# Check if we have any non‐NaN objectives
has_obj = not np.all([np.isnan(v) for v in obj_map.values()])

# If we do, compute best objective per instance
if has_obj:
    best_obj = {
        inst: min(obj_map[(inst, s)] for s in solvers)
        for inst in instances
    }

# ── 4) Assemble per-solver arrays ───────────────────────────────────────────────
times = np.array([[ time_map[(inst, s)] for inst in instances ] for s in solvers])

if has_obj:
    # directly use the JSON‐provided gap values
    gaps = np.array([[ gap_map[(inst, s)] for inst in instances ] 
                     for s in solvers])

# ── 5) Compute performance profiles ────────────────────────────────────────────
max_time = np.nanmax(times)
time_x   = np.linspace(0, max_time, 300)
n_inst   = len(instances)

# runtime profile: number of instances solved by time τ
perf_time = {
    solvers[i]: np.mean(times[i, None, :] <= time_x[:, None], axis=1) * n_inst
    for i in range(len(solvers))
}

if has_obj:
    max_gap = np.nanmax(gaps)
    gap_x   = np.linspace(0, max_gap, 300)
    # gap profile: number of instances within gap δ
    perf_gap = {
        solvers[i]: np.mean(gaps[i, None, :] <= gap_x[:, None], axis=1) * n_inst
        for i in range(len(solvers))
    }

# ── 6) Plot with a broken, log-scaled runtime axis ─────────────────────────────
if has_obj:
    fig, (ax1, ax2) = plt.subplots(
        1, 2,
        figsize=(12, 6),
        sharey=True,
        gridspec_kw={'width_ratios': [3, 1], 'wspace': 0}
    )

    # 1) log-scale left panel
    ax1.set_xscale('log')

    # 2) hide the “inner” spines so top/bottom borders look continuous
    ax1.spines['right'].set_visible(False)
    ax2.spines['left'] .set_visible(False)

    # 3) draw the diagonal “break” markers at x=1 (ax1) and x=0 (ax2)
    d = .02  # size of the diagonal slashes
    # bottom slash on left
    ax1.plot((1, 1), (-d, d), transform=ax1.transAxes, color='k', clip_on=False)
    # top slash on left
    ax1.plot((1, 1), (1 - d, 1 + d), transform=ax1.transAxes, color='k', clip_on=False)
    # bottom slash on right
    ax2.plot((0, 0), (-d, d), transform=ax2.transAxes, color='k', clip_on=False)
    # top slash on right
    ax2.plot((0, 0), (1 - d, 1 + d), transform=ax2.transAxes, color='k', clip_on=False)

    # 4) plot the two profiles
    for s in solvers:
        ax1.step(time_x, perf_time[s], where='post', label=s)
        ax2.step(gap_x,  perf_gap [s], where='post')

    # axis labels & title
    ax1.set_xlabel('Runtime [s]', fontsize=14)
    ax2.set_xlabel('Gap (%)',      fontsize=14)
    ax1.set_ylabel('Number of Instances', fontsize=14)
    fig.suptitle('Absolute Performance Profile', fontsize=16)

    # axis limits
    ax1.set_xlim(time_x[1], max_time)  # avoid zero on log axis
    ax2.set_xlim(0,        max_gap)

    # legend & grid
    ax1.legend(loc='lower right', fontsize='small')
    ax1.grid(True, alpha=0.3)
    ax2.grid(True, alpha=0.3)

else:
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.set_xscale('log')
    for s in solvers:
        ax1.step(time_x, perf_time[s], where='post', label=s)
    ax1.set_xlabel('Runtime [s]')
    ax1.set_ylabel('Number of Instances')
    ax1.set_title('Performance Profile (Runtime Only)')
    ax1.set_xlim(time_x[1], max_time)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='lower right', fontsize='small')

plt.tight_layout()
plt.savefig('performance_profile_150.png', dpi=150)
plt.savefig('performance_profile_150.pdf', dpi=150)
plt.show()


