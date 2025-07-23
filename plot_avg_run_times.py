import os
import json
import numpy as np
import matplotlib.pyplot as plt

# 1. Load & preprocess exactly as before…
folder    = 'results_strip'
json_file = 'benchmark_results_datnzig_extended_extended.json'
file_path = os.path.join(folder, json_file)
with open(file_path) as f:
    data = json.load(f)
data = [d for d in data if d['formulation'] != 'traditional']

# 2. Build sizes/models and rename_map
sizes      = sorted({int(d['instance'].split('_')[0]) for d in data})
raw_models = {f"{d['formulation']}_{d['reform']}" for d in data}
rename_map = {
    'bigM_altered':   'altered_bigm',
    'hull_altered':   'altered_hull',
    'reagg_MIP':      'altered_reagg',
    'bigM_tres':      'tres_bigm',
    'hull_tres':      'tres_hull',
    'reagg_tres_MIP':'tres_reagg',
}

# 3. Gather the raw times into lists
times = {
    (size, rename_map.get(m, m)): []
    for size in sizes
    for m    in raw_models
}
for d in data:
    size  = int(d['instance'].split('_')[0])
    raw_m = f"{d['formulation']}_{d['reform']}"
    code  = rename_map.get(raw_m, raw_m)
    times[(size, code)].append(d['time_sec'])

# 4. Compute *linear* means, and *log‐space* means & std‐devs
means      = {}
log_means  = {}
log_stds   = {}
for (sz,code), ts in times.items():
    if not ts: 
        continue
    arr = np.array(ts)
    means[(sz,code)] = arr.mean()
    logs            = np.log(arr)
    log_means[(sz,code)] = logs.mean()
    log_stds [(sz,code)] = logs.std(ddof=1)

# 5. Prepare for plotting
models = sorted({code for (_,code) in means.keys()},
                key=lambda s:(s.split('_')[0],s.split('_')[1]))
x     = np.arange(len(sizes))
width = 0.8/len(models)

fig, ax = plt.subplots(figsize=(12,6))

# 6. Plot bars + asymmetric log‐space errorbars
for i, code in enumerate(models):
    xs = x + i*width
    y  = [ means[(sz,code)]    for sz in sizes ]
    μ  = [ log_means[(sz,code)] for sz in sizes ]
    σ  = [ log_stds [(sz,code)] for sz in sizes ]
    
    # bar at the *linear* mean
    ax.bar(xs, y, width, label=code)
    
    # compute lower/upper error in *linear* coordinates so that
    # after log‐axis transform they appear ±1σ in log‐space:
    lower = [ np.exp(m) - np.exp(m - s) for m,s in zip(μ,σ) ]
    upper = [ np.exp(m + s) - np.exp(m) for m,s in zip(μ,σ) ]
    ax.errorbar(
        xs, y, 
        yerr=[lower,upper], 
        fmt='none', 
        ecolor='black', 
        capsize=3
    )

# 7. Finish styling
ax.set_yscale('log')
ax.set_xticks(x + width*(len(models)-1)/2)
ax.set_xticklabels(sizes, fontsize=14)
ax.set_xlabel('Instance Size', fontsize=14)
ax.set_ylabel('Average Time (sec)', fontsize=14)
ax.tick_params(axis='y', labelsize=14)
ax.set_title('Average Solve Time by Size & Reformulation\n(10 Cases Averaged, ±1σ in log‐space)', fontsize=14)

# remap legend labels
label_map = {
    'altered_bigm':  'Original Big-M',
    'altered_hull':  'Original Hull',
    'altered_reagg': 'Original Reaggregated-Hull',
    'tres_bigm':     'Trespalacios Big-M',
    'tres_hull':     'Trespalacios Hull',
    'tres_reagg':    'Trespalacios Reaggregated-Hull',
}
handles, labels = ax.get_legend_handles_labels()
labels = [label_map.get(l,l) for l in labels]
ax.legend(handles, labels, title='Model & Reformulation',
          bbox_to_anchor=(1.02,1), loc='upper left')

plt.tight_layout()
out_png = os.path.join(folder, 'avg_run_times_by_size_logerr.png')
out_pdf = os.path.join(folder, 'avg_run_times_by_size_logerr.pdf')
plt.savefig(out_pdf, dpi=150)
plt.savefig(out_png, dpi=150)
plt.show()
