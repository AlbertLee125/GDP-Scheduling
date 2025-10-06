# performance_profile_gdp.py

import os
import json
import numpy as np
import matplotlib.pyplot as plt

# ── 1) Load JSON ────────────────────────────────────────────────────────────────
file_path = 'results_strip/benchmark_results_dantzig_scip.json'
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
    'altered_bigm':    'Original Big-M',
    'altered_hull':    'Original Hull',
    'reagg_MIP':       'Original Reaggregated-Hull',
    'reagg_tres_MIP':  'Trespalacios Reaggregated-Hull',
    'tres_bigm':       'Trespalacios Big-M',
    'tres_hull':       'Trespalacios Hull',
}

solvers = [
    'Original Big-M',
    'Original Hull',
    'Original Reaggregated-Hull',
    'Trespalacios Big-M',
    'Trespalacios Hull',
    'Trespalacios Reaggregated-Hull',
]

label_map = {
    'Original Big-M':              'S0 Big-M',
    'Original Hull':               'S0 HR',
    'Original Reaggregated-Hull':  'S0 Reaggregated-Hull',
    'Trespalacios Big-M':          'S1 Big-M',
    'Trespalacios Hull':           'S1 HR',
    'Trespalacios Reaggregated-Hull': 'S1 Reaggregated-Hull',
}

# ── 3) Build time & objective maps ─────────────────────────────────────────────
time_map = {}
obj_map  = {}
gap_map  = {}

for d in data:
    inst = d['instance']
    raw  = f"{d['formulation']}_{d['reform']}"
    sol  = rename_map.get(raw, raw)
    time_map[(inst, sol)] = d['time_sec']
    obj_map [(inst, sol)] = d.get('objective', np.nan)
    gap_map [(inst, sol)] = d.get('gap',       np.nan)

# Do we have any finite objectives?
has_obj = not np.all([np.isnan(v) for v in obj_map.values()])

if has_obj:
    # best objective per instance (if needed for recomputing gaps)
    best_obj = {
        inst: min(obj_map[(inst, s)] for s in solvers)
        for inst in instances
    }

# ── 4) Assemble per-solver arrays ───────────────────────────────────────────────
times = np.array([[ time_map[(inst, s)] for inst in instances ] for s in solvers])

if has_obj:
    # directly use JSON‐provided gaps
    gaps = np.array([[ gap_map[(inst, s)] for inst in instances ]
                     for s in solvers])

# ── 5) Compute performance profiles ────────────────────────────────────────────

n_inst = len(instances)

# — replace linspace with actual unique solve times for crisp steps —
all_times = np.unique(times[np.isfinite(times)])
time_x   = np.concatenate(([0.0], all_times))
perf_time = {
    solvers[i]: np.mean(times[i, None, :] <= time_x[:, None], axis=1) * n_inst
    for i in range(len(solvers))
}

if has_obj:
    all_gaps = np.unique(gaps[np.isfinite(gaps)])
    gap_x    = np.concatenate(([0.0], all_gaps))
    perf_gap = {
        solvers[i]: np.mean(gaps[i, None, :] <= gap_x[:, None], axis=1) * n_inst
        for i in range(len(solvers))
    }

# ── 5.1) Virtual Best & Virtual Worst across formulations ──────────────────────
# (rows = formulations, cols = instances)
vb_time_per_inst = np.nanmin(times, axis=0)   # virtual best time per instance
vw_time_per_inst = np.nanmax(times, axis=0)   # virtual worst time per instance
perf_time_vb = np.mean(vb_time_per_inst[None, :] <= time_x[:, None], axis=1) * n_inst
perf_time_vw = np.mean(vw_time_per_inst[None, :] <= time_x[:, None], axis=1) * n_inst

if has_obj:
    vb_gap_per_inst = np.nanmin(gaps, axis=0)   # best (smallest) gap per instance
    vw_gap_per_inst = np.nanmax(gaps, axis=0)   # worst (largest) gap per instance
    perf_gap_vb = np.mean(vb_gap_per_inst[None, :] <= gap_x[:, None], axis=1) * n_inst
    perf_gap_vw = np.mean(vw_gap_per_inst[None, :] <= gap_x[:, None], axis=1) * n_inst

# ── 6) Plot with a broken, log-scaled runtime axis ─────────────────────────────
if has_obj:
    fig, (ax1, ax2) = plt.subplots(
        1, 2,
        figsize=(11, 11),
        sharey=True,
        gridspec_kw={'width_ratios': [3, 1], 'wspace': 0}
    )

    # left panel log-scale
    ax1.set_xscale('log')
    ax1.spines['right'].set_visible(False)
    ax2.spines['left'] .set_visible(False)

    # diagonal “break” markers
    d = .02
    ax1.plot((1, 1), (-d, d), transform=ax1.transAxes, color='k', clip_on=False)
    ax1.plot((1, 1), (1 - d, 1 + d), transform=ax1.transAxes, color='k', clip_on=False)
    ax2.plot((0, 0), (-d, d), transform=ax2.transAxes, color='k', clip_on=False)
    ax2.plot((0, 0), (1 - d, 1 + d), transform=ax2.transAxes, color='k', clip_on=False)

    # plot the profiles
    for name in solvers:
        ax1.step(time_x[1:], perf_time[name][1:], where='post', label=name)
        ax2.step(gap_x[1:],  perf_gap [name][1:], where='post')

    # Virtual Best and Virtual Worst
    ax1.step(time_x[1:], perf_time_vb[1:], where='post',
         label='Virtual Best', linewidth=3, linestyle='--')
    ax1.step(time_x[1:], perf_time_vw[1:], where='post',
            label='Virtual Worst', linewidth=3, linestyle=':')

    ax2.step(gap_x[1:],  perf_gap_vb[1:], where='post',
            label='Virtual Best', linewidth=3, linestyle='--')
    ax2.step(gap_x[1:],  perf_gap_vw[1:], where='post',
            label='Virtual Worst', linewidth=3, linestyle=':')

    # increase x- and y-tick label size
    ax1.tick_params(axis='both', which='major', labelsize=18)
    ax2.tick_params(axis='both', which='major', labelsize=18)

    # force y-axis exactly 0 → 150
    pad = 0.02 * n_inst
    ax1.set_ylim(-pad, n_inst + pad)
    ax1.set_yticks([0, 30, 60, 90, 120, n_inst])


    # labels & title
    ax1.set_xlabel('Runtime [s]', fontsize=18)
    ax2.set_xlabel('Gap (%)',      fontsize=18)
    ax1.set_ylabel('Number of Instances', fontsize=18)
    fig.suptitle('Absolute Performance Profile of Strip Packing Problem using SCIP', fontsize=18)

    # axis limits
    ax1.set_xlim(time_x[1], time_x[-1])
    ax2.set_xlim(0,       gap_x[-1])

    handles, labels = ax1.get_legend_handles_labels()
    mapped_labels = [label_map.get(lbl, lbl) for lbl in labels]
    ax1.legend(handles, mapped_labels,
            loc='lower right',
            fontsize='small',
            title='Model & Reformulation',
            prop={'size': 14},
            title_fontsize=14)
    ax1.grid(True, alpha=0.3)
    ax2.grid(True, alpha=0.3)

else:
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.set_xscale('log')
    for s in solvers:
        ax1.step(time_x[1:], perf_time[s][1:], where='post', label=s)
    ax1.set_xlabel('Runtime [s]')
    ax1.set_ylabel('Number of Instances')
    ax1.set_title('Performance Profile (Runtime Only)')
    ax1.set_xlim(time_x[1], time_x[-1])
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='lower right', fontsize='small')

plt.tight_layout()
plt.savefig('performance_profile_150_scip.png', dpi=150)
plt.savefig('performance_profile_150_scip.pdf', dpi=150)
plt.show()
