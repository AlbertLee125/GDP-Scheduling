import os
import json
import numpy as np
import matplotlib.pyplot as plt

# 1. Specify your folder and the exact JSON filename:
folder    = 'results_strip'
json_file = 'benchmark_results_datnzig_extended_extended.json'  # ← paste your JSON name here
file_path = os.path.join(folder, json_file)

if not os.path.isfile(file_path):
    raise FileNotFoundError(f"JSON file not found: {file_path}")
print(f"Loading data from: {file_path}")

# 2. Load the data (list of dicts with keys 'instance','formulation','reform','time_sec',…)
with open(file_path, 'r') as f:
    data = json.load(f)

# 2.1. Exclude any 'traditional' formulation entries
data = [d for d in data if d['formulation'] != 'traditional']

# 3. Build your set of sizes and models
#    size = int(prefix before '_'), e.g. '5_3' → size=5
sizes = sorted({int(d['instance'].split('_')[0]) for d in data})
#    model labels before/after renaming
raw_models = {f"{d['formulation']}_{d['reform']}" for d in data}

# 4. Optional rename‐map to clean up labels
rename_map = {
    'bigM_altered':       'altered_bigm',
    'hull_altered':       'altered_hull',
    'reagg_MIP':          'altered_reagg',
    'bigM_tres':          'tres_bigm',
    'hull_tres':          'tres_hull',
    'reagg_tres_MIP':     'tres_reagg',
}

# 5. Initialize a dict to collect all times for each (size, model)
times = { (size, rename_map.get(m, m)): [] 
          for size in sizes 
          for m in raw_models }

# 6. Fill it
for d in data:
    size = int(d['instance'].split('_')[0])
    raw_m = f"{d['formulation']}_{d['reform']}"
    m = rename_map.get(raw_m, raw_m)
    times[(size, m)].append(d['time_sec'])

# 7. Compute means & std‐devs
means = { (size, m): np.mean(ts) 
          for (size,m), ts in times.items() if ts }
stds  = { (size, m): np.std(ts, ddof=1) 
          for (size,m), ts in times.items() if ts }

# 8. Sort your model list (after rename) for consistent ordering
models = sorted({m for (_,m) in means.keys()},
                key=lambda s: (s.split('_')[0], s.split('_')[1]))

# 9. Plot
x     = np.arange(len(sizes))
width = 0.8 / len(models)

fig, ax = plt.subplots(figsize=(12, 6))

for i, model in enumerate(models):
    # bar centers
    xs = x + i*width

    # mean & std
    y = [means[(size, model)] for size in sizes]
    e = [stds [(size, model)] for size in sizes]

    # draw bars
    ax.bar(xs, y, width, label=model)

    # draw ±1σ errorbars in data coords
    cap = width * 0.4
    for x0, yi, ei in zip(xs, y, e):
        y_lo, y_hi = yi - ei, yi + ei
        ax.vlines(x0, y_lo, y_hi, color='black')
        ax.hlines([y_lo, y_hi], x0-cap, x0+cap, color='black')

# set log scale once
ax.set_yscale('log')

# 10. Final formatting
ax.set_xticks(x + width*(len(models)-1)/2)
ax.set_xticklabels(sizes)
ax.set_xlabel('Instance Size')
ax.set_ylabel('Average Time (sec)')
ax.set_title('Average Solve Time by Size & Reformulation\n(5 Cases Averaged, ±1 std)')
ax.legend(title='Model_Reform', bbox_to_anchor=(1.02,1), loc='upper left')
plt.tight_layout()

# 11. Save & Show
out_png = os.path.join(folder, 'avg_run_times_by_size_modified.png')
out_pdf = os.path.join(folder, 'avg_run_times_by_size_modified.pdf')
plt.savefig(out_pdf, dpi=150)
print(f"Saved plots to:\n  {out_png}\n  {out_pdf}")
plt.show()