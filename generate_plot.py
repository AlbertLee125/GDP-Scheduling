import json
import pandas as pd
import matplotlib.pyplot as plt
import os

# Get the absolute path of the current directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the JSON file, Modify the path number for different scheduling data
json_file_path = os.path.join(
    script_dir, f"results/benchmark_results_900.json"
)

# load data from json file
with open(json_file_path, "r") as f:
    data = json.load(f)

# Create a DataFrame from the JSON data
df = pd.DataFrame(data)

# Filter out rows where the objective is "ABORTED"
df_filtered = df[df['objective'] != "ABORTED"].copy()

# Create a new column that combines model_name and transformation
df_filtered['method'] = df_filtered['model_name'] + " " + df_filtered['transformation']

# Replace the method names with abbreviations
method_mapping = {
    "General Precedence GDP gdp.bigm": "GP_BM",
    "General Precedence GDP gdp.hull": "GP_HR",
    "Immediate Precedence BigM MINLP": "IP_BM",
    "Immediate Precedence HR MINLP": "IP_HR",
    "Time Slots GDP gdp.bigm": "TS_BM",
    "Time Slots GDP gdp.hull": "TS_HR",
    "Time Slots Hull MINLP": "TS_HR_C"
}
df_filtered['method'] = df_filtered['method'].replace(method_mapping)

# Pivot the data: scheduling_data as index and each method as a separate column with time_sec as values
pivot_df = df_filtered.pivot_table(index='scheduling_data', 
                                   columns='method', 
                                   values='time_sec', 
                                   aggfunc='first')

# Sort the DataFrame by scheduling_data for proper ordering on the x-axis
pivot_df.sort_index(inplace=True)

# Create a grouped bar chart with an increased figure size for wider bars
fig, ax = plt.subplots(figsize=(14, 8))
pivot_df.plot(kind='bar', ax=ax, width=0.8)
ax.set_xlabel("Scheduling Data", fontsize=20)
ax.set_ylabel("Time (sec)", fontsize=20)
ax.set_title("Benchmark Results for Single Unit Sequencing Problem", fontsize=20)

# Set the y-axis to a logarithmic scale
ax.set_yscale('log')

# Define the mapping for the problem size j for each scheduling_data
j_mapping = {1: 15, 2: 15, 3: 20, 4: 20, 5: 20, 6: 25, 7: 25, 8: 25, 9: 30, 10: 30}

# Update x-axis tick labels to have "Ex. " prefix (e.g., 1 becomes "Ex. 1") and its problem size on the second line
ax.set_xticklabels([f"Ex. {x}\n $|I| = {j_mapping.get(x, '?')}$" for x in pivot_df.index])

# Place the legend below the plot, remove the box, and organize it in 3 columns
legend = ax.legend(title="Method", loc='upper center', bbox_to_anchor=(0.5, -0.22), ncol=7, frameon=True, fontsize=12, title_fontsize=14)
plt.xticks(rotation=0, fontsize=16)
plt.yticks(rotation=0, fontsize=16)
plt.tight_layout(rect=[0, 0.05, 1, 1])  # leave space at the bottom for the legend

# Display the plot
plt.show()

# Save the plot as an PDF file
plt.savefig('benchmark_results_900.pdf', bbox_inches='tight')
# Save the plot as an PNG file
plt.savefig('benchmark_results_900.png', bbox_inches='tight')