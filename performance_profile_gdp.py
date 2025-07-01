# performance_profile_gdp.py

import os
import json
import numpy as np
import matplotlib.pyplot as plt

# ── 1) Load JSON ────────────────────────────────────────────────────────────────
file_path = 'results_strip/benchmark_results_datnzig_extended_overall.json'
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
for d in data:
    inst = d['instance']
    raw  = f"{d['formulation']}_{d['reform']}"
    sol  = rename_map.get(raw, raw)
    time_map[(inst, sol)] = d['time_sec']
    obj_map [(inst, sol)] = d.get('obj', np.nan)

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
    gaps = np.array([[ 
        (obj_map[(inst, s)] - best_obj[inst]) / abs(best_obj[inst])
        for inst in instances ] for s in solvers])

# ── 5) Compute performance profiles ────────────────────────────────────────────
max_time = np.nanmax(times)
time_x   = np.linspace(0, max_time, 300)
perf_time = {
    solvers[i]: np.mean(times[i, None, :] <= time_x[:, None], axis=1)
    for i in range(len(solvers))
}

if has_obj:
    max_gap = np.nanmax(gaps)
    gap_x   = np.linspace(0, max_gap, 300)
    perf_gap = {
        solvers[i]: np.mean(gaps[i, None, :] <= gap_x[:, None], axis=1)
        for i in range(len(solvers))
    }

# ── 6) Plot ────────────────────────────────────────────────────────────────────
if has_obj:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6), sharey=True)
else:
    fig, ax1 = plt.subplots(1, 1, figsize=(6, 3.5))

# Plot runtime profile
for s in solvers:
    ax1.plot(time_x, perf_time[s], label=s)
ax1.set_xlabel('Runtime (s)')
ax1.set_xlim(0, max_time)
ax1.set_ylabel('Fraction of Instances')
ax1.set_title('Runtime Profile')
ax1.grid(True)

if has_obj:
    # Plot gap profile
    for s in solvers:
        ax2.plot(gap_x, perf_gap[s], label=s)
    ax2.set_xlabel('Optimality Gap')
    ax2.set_xlim(0, max_gap)
    ax2.set_title('Gap Profile')
    ax2.grid(True)
    ax1.legend(loc='lower right', fontsize='small')
    plt.suptitle('Performance Profiles of Six GDP Reformulations', y=1.02)
    plt.tight_layout()
else:
    ax1.legend(loc='lower right', fontsize='small')
    plt.title('Performance Profile (Runtime Only)')
    plt.tight_layout()

plt.savefig('performance_profile.png', dpi=150)
plt.savefig('performance_profile.pdf', dpi=150)
print("Saved plots to:\n  performance_profile.png\n  performance_profile.pdf")
plt.show()
