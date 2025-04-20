import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
import json
import os
import time

def build_single_unit_sequencing_gp_reagg(j):
    # Get the absolute path of the current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the JSON file, Modify the path number for different scheduling data
    json_file_path = os.path.join(
        script_dir, f"../scheduling_data/scheduling_data_{j}.json"
    )

    # load data from json file
    with open(json_file_path, "r") as f:
        data = json.load(f)

    m = pyo.ConcreteModel()

    # Convert dictionary keys from strings to integers
    data["processing_time"] = {int(k): v for k, v in data["processing_time"].items()}
    data["release_time"] = {int(k): v for k, v in data["release_time"].items()}
    data["due_time"] = {int(k): v for k, v in data["due_time"].items()}

    # Orders (jobs)
    m.I = pyo.Set(initialize=data["jobs"])

    # Pair-index set (i,j) with i<j
    m.IJ = pyo.Set(dimen=2, initialize=[(i, j) for i in m.I for j in m.I if i < j]) 

    # Define parameters dynamically from JSON
    m.p = pyo.Param(m.I, initialize=data["processing_time"])
    m.r = pyo.Param(m.I, initialize=data["release_time"])
    m.d = pyo.Param(m.I, initialize=data["due_time"])

    # Define the bounds for start times: 
    # Each job must start no earlier than its release time and no later than its due date minus processing time.
    def x_bounds_rule(m, i):
        return (m.r[i], m.d[i] - m.p[i])
    m.x = pyo.Var(m.I, bounds=x_bounds_rule)

    # Binary variables for the disjunctions
    m.y = pyo.Var(m.IJ, domain=pyo.Binary)

    # First lower bound for reaggregation:
    m.LowerBound1 = pyo.Param(m.IJ, initialize= lambda m, i, j: m.r[i] - m.d[j] + m.p[j], within=pyo.Reals)
    # Second lower bound for reaggregation:
    m.LowerBound2 = pyo.Param(m.IJ, initialize = lambda m, i, j: max(m.p[j], m.r[i]-m.d[j]+m.p[j]), within=pyo.Reals)

    # First upper bound for reaggregation:
    m.UpperBound1 = pyo.Param(m.IJ, initialize= lambda m, i, j: min(-m.p[i], m.d[i]-m.p[i]-m.r[j]), within=pyo.Reals)
    # Second upper bound for reaggregation:
    m.UpperBound2 = pyo.Param(m.IJ, initialize= lambda m, i, j: m.d[i]-m.p[i]-m.r[j], within=pyo.Reals)

    # Compute bounds for makespan:
    lower_bound_makespan = min(data["release_time"][i] + data["processing_time"][i] for i in data["jobs"])
    upper_bound_makespan = max(data["due_time"][i] for i in data["jobs"])
    m.makespan = pyo.Var(bounds=(lower_bound_makespan, upper_bound_makespan))

    # Lower Bound for reaggregation
    def lower_bound_reaggreation_rule(m, i, j):
        return m.x[i] - m.x[j] >= m.LowerBound1[i,j] * m.y[i,j] + m.LowerBound2[i,j] * (1 - m.y[i,j])
    m.lower_bound_reaggregation = pyo.Constraint(m.IJ, rule=lower_bound_reaggreation_rule)

    # Upper Bound for reaggregation
    def upper_bound_reaggreation_rule(m, i, j):
        return m.x[i] - m.x[j] <= m.UpperBound1[i,j] * m.y[i,j] + m.UpperBound2[i,j] * (1 - m.y[i,j])
    m.upper_bound_reaggregation = pyo.Constraint(m.IJ, rule=upper_bound_reaggreation_rule)


    # Define Constraints 
    def release_time_constraint(m, i):
        return m.x[i] >= m.r[i]
    m.release_time_constraint = pyo.Constraint(m.I, rule=release_time_constraint)

    def due_date_constraint(m, i):
        return m.x[i] + m.p[i] <= m.d[i]
    m.due_date_constraint = pyo.Constraint(m.I, rule=due_date_constraint)

    def makespan_constraint(m, i):
        return m.x[i] + m.p[i] <= m.makespan
    m.makespan_constraint = pyo.Constraint(m.I, rule=makespan_constraint)

    # Define objective: minimize makespan
    m.obj = pyo.Objective(expr=m.makespan, sense=pyo.minimize)

    return m

if __name__ == "__main__":
    j = range(1, 11)

    for js in j:
        m = build_single_unit_sequencing_gp_reagg(js)
        solver = pyo.SolverFactory("gurobi")
        results = solver.solve(m, tee=True)
        print(f"Objective value (makespan) for scheduling_data_{js}.json:", pyo.value(m.obj))


    m = build_single_unit_sequencing_gp_reagg(1)
    
    # Solve the model (solver can be 'gams' with 'baron', 'knitro', etc.)
    solver = pyo.SolverFactory("gurobi")
    # solver.options["solver"] = "baron"
    results = solver.solve(m, tee=True)#, time_limit=900)
    # m.display()
    # print objective
    print("Objective value (makespan):", pyo.value(m.obj))
