import json
import os
import time
import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from strip_packing.strip_packing import build_rect_strip_packing_model
from strip_packing.strip_packing_altered import (
    build_rect_strip_packing_model_altered,
    build_rect_strip_packing_model_reagg,
)
from strip_packing.strip_packing_trespacolis import (
    build_rect_strip_packing_model_altered_Tres,
    build_rect_strip_packing_model_reagg_Tres,
)

def plot_and_save(model, inst, label, reform):
    """
    Prints x,y for each rectangle and
    draws & saves the packing layout.
    """
    # 1) print out coords
    print(f"\nInstance {inst}, formulation {label}, reform {reform}:")
    for i in model.rectangles:
        xi = pyo.value(model.x[i])
        yi = pyo.value(model.y[i])
        print(f"  Rect {i}: x = {xi:.2f}, y = {yi:.2f}")

    # 2) plot
    fig, ax = plt.subplots(figsize=(8, 5))
    for i in model.rectangles:
        x     = pyo.value(model.x[i])
        y_top = pyo.value(model.y[i])
        w     = pyo.value(model.rect_width[i])
        h     = pyo.value(model.rect_length[i])
        y_bot = y_top - w

        rect = Rectangle((x, y_bot), h, w, edgecolor='black',
                         facecolor='skyblue', lw=1)
        ax.add_patch(rect)
        ax.text(x + h/2, y_bot + w/2, str(i),
                ha='center', va='center', fontsize=7)

    ax.set_xlim(0, pyo.value(model.strip_length)*1.05)
    ax.set_ylim(0, pyo.value(model.strip_width)*1.05)
    ax.set_aspect('equal')
    ax.set_xlabel("X (length)")
    ax.set_ylabel("Y (width)")
    ax.set_title(f"{inst} | {label} | {reform}")
    ax.grid(True)
    plt.tight_layout()

    # 3) save
    base = f"strip_figures/{inst}_{label}_{reform}"
    fig.savefig(base + ".png", dpi=150)
    fig.savefig(base + ".pdf")
    plt.close(fig)
    print(f"  → saved figures to {base}.png and {base}.pdf")

instance_ids = [
    "5_1",
    "5_2",
    # "5_3",
    # "8_1",
    # "8_2",
    # "8_3",
    # "10_1",
    # "10_2",
    # "10_3",
    # "12_1",
    # "12_2",
    # "12_3",
    # "15_1",
    # "15_2",
    # "15_3",
]

time_limit = 900
solver_name = "gurobi"
results_dir = "results_strip"
output_file = os.path.join(results_dir, "benchmark_results_datnzig.json")

# each entry: (label, builder_fn, is_gdp)
models_to_test = [
    ("traditional", build_rect_strip_packing_model, True),
    ("altered",     build_rect_strip_packing_model_altered, True),
    ("tres",        build_rect_strip_packing_model_altered_Tres, True),
    ("reagg",       build_rect_strip_packing_model_reagg, False),
    ("reagg_tres",  build_rect_strip_packing_model_reagg_Tres, False),
]

# make sure results directory exists
os.makedirs(results_dir, exist_ok=True)

results = []

for inst in instance_ids:
    for label, builder, is_gdp in models_to_test:
        # build model for this instance
        model = builder(inst)

        if is_gdp:
            # apply both Big-M and Hull reformulations
            for reform in ("gdp.bigm", "gdp.hull"):
                mip = pyo.TransformationFactory(reform).create_using(model)
                solver = pyo.SolverFactory(solver_name)
                solver.options["TimeLimit"] = time_limit
                solver.options["Threads"]   = 1

                start = time.time()
                res = solver.solve(mip, tee=True)
                duration = time.time() - start

                results.append({
                    "instance":    inst,
                    "formulation": label,
                    "reform":      reform.split(".")[1],   # "bigm" or "hull"
                    "time_sec":    round(duration, 2),
                    "objective":   pyo.value(mip.strip_length),
                    "status":      str(res.solver.termination_condition),
                })

                plot_and_save(mip, inst, label, reform.split('.')[1])

        else:
            # directly a MIP
            solver = pyo.SolverFactory(solver_name)
            solver.options["TimeLimit"] = time_limit
            solver.options["Threads"]   = 1

            start = time.time()
            res = solver.solve(model, tee=True)
            duration = time.time() - start

            results.append({
                "instance":    inst,
                "formulation": label,
                "reform":      "MIP",
                "time_sec":    round(duration, 2),
                "objective":   pyo.value(model.strip_length),
                "status":      str(res.solver.termination_condition),
            })

            plot_and_save(model, inst, label, "MIP")

# write out JSON
with open(output_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"Benchmark finished. Results written to {output_file}")

