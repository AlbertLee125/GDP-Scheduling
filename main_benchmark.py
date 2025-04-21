import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
import time
import json
import os

from model.single_unit_sequencing_gp import build_single_unit_sequencing_gp
from model.single_unit_sequencing_gp_reagg import build_single_unit_sequencing_gp_reagg
from model.single_unit_sequencing_ip import (
    build_single_unit_sequencing_Immediate_Precedence_BigM,
    build_single_unit_sequencing_Immediate_Precedence_HR,
)
from model.single_unit_sequencing_ts import (
    build_single_unit_sequencing_time_slots,
    build_single_unit_sequencing_time_slots_hull,
)


def benchmark_models():
    # Create a solver instance and set a time limit.
    solver = pyo.SolverFactory("gurobi")
    solver.options["time_limit"] = 3600  # set time limit for each solve

    # Define scheduling data IDs (for example, 1 to 10)
    scheduling_data_list = list(range(1, 11))

    # MINLP models (manually reformulated into MINLP)
    minlp_models = {
        # "Immediate Precedence BigM": build_single_unit_sequencing_Immediate_Precedence_BigM,
        # "Immediate Precedence HR": build_single_unit_sequencing_Immediate_Precedence_HR,
        # "Time Slots Hull": build_single_unit_sequencing_time_slots_hull,
        "General Precedence Hull Reagg": build_single_unit_sequencing_gp_reagg,
    }

    # GDP models (still in GDP form and require transformation)
    gdp_models = {
        "General Precedence GDP": build_single_unit_sequencing_gp,
        # "Time Slots GDP": build_single_unit_sequencing_time_slots,
    }

    # Container for benchmark results
    results = []

    print("\n========== Running MINLP Models ==========")
    for s in scheduling_data_list:
        for model_name, builder in minlp_models.items():
            print(f"\n[MINLP] Scheduling Data {s} | Model: {model_name}")
            m = builder(s)  # Build the model with scheduling data s
            start_time = time.time()
            try:
                sol = solver.solve(m, tee=True)
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"Solver exception for Scheduling Data {s} | Model: {model_name}: {e}")
                results.append((s, model_name, "MINLP", elapsed, "ABORTED", f"exception: {e}"))
                continue
            elapsed = time.time() - start_time
            termination = sol.solver.termination_condition
            # Check for "aborted" using string comparison.
            if str(termination).lower() == "aborted":
                print(f"Run aborted for Scheduling Data {s} | Model: {model_name} (MINLP)")
                results.append((s, model_name, "MINLP", elapsed, "ABORTED", termination))
                continue
            try:
                obj_val = pyo.value(m.obj)
            except Exception as e:
                print(f"Error computing objective for Scheduling Data {s} | Model: {model_name}: {e}")
                obj_val = "ERROR"
            results.append((s, model_name, "MINLP", elapsed, obj_val, termination))
            print(f"Time: {elapsed:.2f} sec, Objective: {obj_val}, Termination: {termination}")

    print("\n========== Running GDP Models ==========")
    # For GDP models, we run both transformation types.
    for s in scheduling_data_list:
        for model_name, builder in gdp_models.items():
            for trans in ["gdp.bigm", "gdp.hull"]:
                print(f"\n[GDP] Scheduling Data {s} | Model: {model_name} | Transformation: {trans}")
                m = builder(s)  # Build the GDP model
                # Apply the chosen GDP transformation.
                pyo.TransformationFactory(trans).apply_to(m)
                start_time = time.time()
                try:
                    sol = solver.solve(m, tee=True)
                except Exception as e:
                    elapsed = time.time() - start_time
                    print(f"Solver exception for Scheduling Data {s} | Model: {model_name} | Transformation: {trans}: {e}")
                    results.append((s, model_name, trans, elapsed, "ABORTED", f"exception: {e}"))
                    continue
                elapsed = time.time() - start_time
                termination = sol.solver.termination_condition
                if str(termination).lower() == "aborted":
                    print(f"Run aborted for Scheduling Data {s} | Model: {model_name} | Transformation: {trans}")
                    results.append((s, model_name, trans, elapsed, "ABORTED", termination))
                    continue
                try:
                    obj_val = pyo.value(m.obj)
                except Exception as e:
                    print(f"Error computing objective for Scheduling Data {s} | Model: {model_name} | Transformation: {trans}: {e}")
                    obj_val = "ERROR"
                results.append((s, model_name, trans, elapsed, obj_val, termination))
                print(f"Time: {elapsed:.2f} sec, Objective: {obj_val}, Termination: {termination}")

    # Print a summary of all runs to the console.
    print("\n========== Benchmark Results Summary ==========")
    header = ("SchedData", "Model Name", "Trans/Type", "Time (sec)", "Objective", "Termination")
    print("{:<9} | {:<30} | {:<12} | {:>10} | {:>10} | {:<}".format(*header))
    print("-" * 90)
    for s, mname, ttype, t, obj, term in results:
        print("{:<9} | {:<30} | {:<12} | {:10.2f} | {:>10} | {:<}".format(s, mname, ttype, t, obj, term))

    # Create directory for results if it doesn't exist.
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)

    # Write the summary to a text file.
    txt_file = os.path.join(results_dir, "benchmark_results_gp_3600.txt")
    with open(txt_file, "w") as f:
        f.write("{:<9} | {:<30} | {:<12} | {:>10} | {:>10} | {:<}\n".format(*header))
        f.write("-" * 90 + "\n")
        for s, mname, ttype, t, obj, term in results:
            f.write("{:<9} | {:<30} | {:<12} | {:10.2f} | {:>10} | {:<}\n".format(s, mname, ttype, t, obj, term))
    print(f"\nBenchmark summary written to {txt_file}")

    # Write the summary to a JSON file.
    json_file = os.path.join(results_dir, "benchmark_results_gp_3600.json")
    json_results = []
    for s, mname, ttype, t, obj, term in results:
        json_results.append({
            "scheduling_data": s,
            "model_name": mname,
            "transformation": ttype,
            "time_sec": t,
            "objective": obj,
            "termination": str(term)
        })
    with open(json_file, "w") as f:
        json.dump(json_results, f, indent=4)
    print(f"Benchmark results (JSON) written to {json_file}")

    


if __name__ == "__main__":
    benchmark_models()
    # # Create a solver instance once
    # solver = pyo.SolverFactory("gurobi")

    # # for scheduling_data in sorted(Scheduling_Data):
    # #     for reformulation_type in reformulation:

    # j = 1  # Change this value to test different scheduling data
    # m = build_single_unit_sequencing_time_slots(j)
    # # m = build_single_unit_sequencing_gp(j)
    # # m = build_single_unit_sequencing_ip(j)

    # # Solve the model using a solver of your choice
    # pyo.TransformationFactory("gdp.hull").apply_to(m)
    # solver = pyo.SolverFactory("gurobi")
    # results = solver.solve(m, tee=True)

    # # Display results
    # # m.display()
    # print("Solver Status:", results.solver.termination_condition)
    # print("Objective Value (MakeSpan):", pyo.value(m.obj))
