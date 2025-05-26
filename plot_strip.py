import os
import json
import numpy as np
import matplotlib.pyplot as plt

# 1. Locate the JSON file inside results_strip/
folder = 'results_strip'
json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
if not json_files:
    raise FileNotFoundError(f"No JSON files found in '{folder}' directory.")
# Pick the first matching file (or specify one by name)
json_file = json_files[0]
file_path = os.path.join(folder, json_file)
print(f"Loading data from: {file_path}")

# 2. Load the data
with open(file_path, 'r') as f:
    data = json.load(f)

# 2.1. Exclude any 'traditional' formulation entries
data = [d for d in data if d['formulation'] != 'traditional']

# 3. Prepare unique instances and models
instances = sorted({d['instance'] for d in data})
models    = sorted({f"{d['formulation']}_{d['reform']}" for d in data})

# 3.1. re-sort so that '5_1','5_2','5_3','8_1',…,'15_3' appear in increasing numeric order
instances = sorted(instances, key=lambda s: (int(s.split('_')[0]), int(s.split('_')[1])))

# 4. Map each (instance, model) to its runtime, with a little rename‐map
rename_map = {
    'reagg_MIP':      'altered_reagg',
    'reagg_tres_MIP': 'tres_reagg',
}

# rebuild time_map using the renamed labels
time_map = {
    (d['instance'],
     rename_map.get(f"{d['formulation']}_{d['reform']}",
                    f"{d['formulation']}_{d['reform']}")): d['time_sec']
    for d in data
}

# rebuild & sort your model list from the (possibly renamed) keys
models = sorted({m for (_, m) in time_map},
                key=lambda s: (s.split('_')[0], s.split('_')[1]))

# 5. Plotting setup
n_inst = len(instances)
n_mod  = len(models)
x      = np.arange(n_inst)
width  = 0.8 / n_mod

fig, ax = plt.subplots(figsize=(12, 6))
for i, model in enumerate(models):
    times = [time_map.get((inst, model), np.nan) for inst in instances]
    ax.bar(x + i*width, times, width, label=model)

# 6. Formatting
ax.set_xlabel('Instance')
ax.set_ylabel('Time (sec)')
ax.set_yscale('log')     
ax.set_title('Benchmark Run Times by Model & Reformulation')
ax.set_xticks(x + width*(n_mod-1)/2)
ax.set_xticklabels(instances)
ax.legend(title='model_reform', bbox_to_anchor=(1.05,1), loc='upper left')
# ax.grid(True)
plt.tight_layout()

# 7. Save to PNG and PDF
out_base = os.path.join(folder, 'benchmark_run_times')
fig.savefig(out_base + '.png', dpi=150)
fig.savefig(out_base + '.pdf')

print(f"Saved plot as:\n  {out_base}.png\n  {out_base}.pdf")

# 8. (Optional) Show plot interactively
# plt.show()