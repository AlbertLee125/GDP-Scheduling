import os
import json
import numpy as np
import matplotlib.pyplot as plt

# 0) Corrected method‐name → abbreviation mapping (note the " - ")
method_mapping = {
    "General Precedence GDP - gdp.bigm":      "GP_BM",
    "General Precedence GDP - gdp.hull":      "GP_HR",
    "General Precedence Hull Reagg - MINLP":  "GP_RHR",
    "Immediate Precedence BigM - MINLP":      "IP_BM",
    "Immediate Precedence HR - MINLP":        "IP_HR",
    "Time Slots GDP - gdp.bigm":              "TS_BM",
    "Time Slots GDP - gdp.hull":              "TS_HR",
    "Time Slots Hull - MINLP":                "TS_RHR"
}

# 1) Load JSON
file_path = 'results/benchmark_results_overall_1to10_900.json'
with open(file_path, 'r') as f:
    data = json.load(f)

# 2) Collect instances & solver labels (mapped)
instances = sorted({d['scheduling_data'] for d in data})
full_methods = {
    f"{d['model_name']} - {d['transformation']}"
    for d in data
}
# apply mapping here
solvers = sorted(method_mapping.get(m, m) for m in full_methods)

# 3) Build runtime & gap maps, using abbreviations
time_map = {}
gap_map  = {}
for d in data:
    inst       = d['scheduling_data']
    full_label = f"{d['model_name']} - {d['transformation']}"
    method     = method_mapping.get(full_label, full_label)
    if isinstance(d['objective'], str):  # aborted
        time_map[(inst, method)] = np.nan
        gap_map [(inst, method)] = np.nan
    else:
        time_map[(inst, method)] = d['time_sec']
        gap_map [(inst, method)] = d.get('gap', np.nan)

# 4) Assemble into arrays
times = np.array([[time_map.get((i,s), np.nan) for i in instances] 
                                           for s in solvers])
gaps  = np.array([[gap_map .get((i,s), np.nan) for i in instances] 
                                           for s in solvers])

# 5) Perf‐profile data
n_inst       = len(instances)
min_positive = np.nanmin(times[times>0])
max_time     = np.nanmax(times)

base_grid = np.linspace(0, max_time, 300)
actual    = np.unique(np.sort(times[~np.isnan(times)]))
time_x    = np.unique(np.concatenate((base_grid, actual)))
time_x    = time_x[time_x>0]

perf_time = {
    sol: np.mean(times[idx,None,:] <= time_x[:,None], axis=1) * n_inst
    for idx, sol in enumerate(solvers)
}

max_gap = np.nanmax(gaps)
gap_x   = np.linspace(0, max_gap, 300)
perf_gap = {
    sol: np.mean(gaps[idx,None,:] <= gap_x[:,None], axis=1) * n_inst
    for idx, sol in enumerate(solvers)
}

# 6) Plot
fig, (ax1, ax2) = plt.subplots(
    1, 2, figsize=(12,6),
    sharey=True,
    gridspec_kw={'width_ratios':[3,1], 'wspace':0}
)

for ax in (ax1, ax2):
    ax.tick_params(
        axis='both',          # both x and y
        which='major',        # major ticks
        labelsize=14          # <-- change this number
    )

ax1.set_xscale('log')
ax1.spines['right'].set_visible(False)
ax2.spines['left'].set_visible(False)

# slashes at break
d = .02
for axis, x in ((ax1,1),(ax2,0)):
    axis.plot((x,x),(-d,d),transform=axis.transAxes,color='k',clip_on=False)
    axis.plot((x,x),(1-d,1+d),transform=axis.transAxes,color='k',clip_on=False)

# draw the curves
for sol in solvers:
    ax1.step(time_x, perf_time[sol], where='post', label=sol)
    ax2.step(gap_x,  perf_gap [sol], where='post')

# labels & limits
ax1.set_xlabel('Runtime [s]', fontsize=14)
ax2.set_xlabel('Gap (%)',      fontsize=14)
ax1.set_ylabel('Number of Instances', fontsize=14)
fig.suptitle('Absolute Performance Profile of Single-Unit Scheduling Reformulations using Gurobi', fontsize=16)
ax1.set_xlim(min_positive, max_time)
ax2.set_xlim(0, max_gap)

# remap legend labels (though solvers is already abbreviated)
handles, labels = ax1.get_legend_handles_labels()
# ax1.legend(handles, labels, title='Method', loc='lower right', fontsize='small')

# 2) Shrink bottom margin so there’s room for the legend
plt.subplots_adjust(bottom=0.25)

# 3) Add a figure‐level legend centered at the bottom
fig.legend(
    handles,
    labels,
    title='Method',
    loc='lower center',
    bbox_to_anchor=(0.5, 0.03),
    ncol=8,               # adjust number of columns as needed
    title_fontsize=12,
    fontsize= 12,
    frameon=True
)

ax1.grid(True, alpha=0.3)
ax2.grid(True, alpha=0.3)

# plt.tight_layout()
plt.savefig('performance_profile_scheduling_gurobi.png', dpi=150)
plt.savefig('performance_profile_scheduling_gurobi.pdf', dpi=150)
plt.show()
