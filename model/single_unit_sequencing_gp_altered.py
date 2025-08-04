import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
import json
import os

def build_single_unit_sequencing_gp_altered(j):
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

    # Compute bounds for makespan:
    lower_bound_makespan = min(data["release_time"][i] + data["processing_time"][i] for i in data["jobs"])
    upper_bound_makespan = max(data["due_time"][i] for i in data["jobs"])
    m.makespan = pyo.Var(bounds=(lower_bound_makespan, upper_bound_makespan))

    def pair_block_rule(b, i, j):
        b.before = Disjunct()
        b.after = Disjunct()
        model = b.model()

        # Precompute the constant bounds (these are numbers since r,p,d are Params)
        lower_before = model.r[i] - model.d[j] + model.p[j]
        upper_before = min(-model.p[i], model.d[i] - model.p[i] - model.r[j])

        lower_after = max(model.p[j], model.r[i] - model.d[j] + model.p[j])
        upper_after = model.d[i] - model.p[i] - model.r[j]

        # before disjunct constraints
        @b.before.Constraint()
        def lb(b):
            return model.x[i] - model.x[j] >= lower_before

        @b.before.Constraint()
        def ub(b):
            return model.x[i] - model.x[j] <= upper_before

        # after disjunct constraints
        @b.after.Constraint()
        def lb(b):
            return model.x[i] - model.x[j] >= lower_after

        @b.after.Constraint()
        def ub(b):
            return model.x[i] - model.x[j] <= upper_after

        # Either "before" or "after" must hold
        b.ordering = Disjunction(expr=[b.before, b.after])

    # Attach the blocks over all i<j pairs
    m.pair_disjunctions = pyo.Block(m.IJ, rule=pair_block_rule)

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
    m = build_single_unit_sequencing_gp(1)
    
    # Apply Big-M Reformulation (or alternatively, use the convex hull reformulation)
    # pyo.TransformationFactory("gdp.bigm").apply_to(m)
    pyo.TransformationFactory("gdp.hull").apply_to(m)
    
    # Solve the model (solver can be 'gams' with 'baron', 'knitro', etc.)
    solver = pyo.SolverFactory("gurobi")
    # solver.options["solver"] = "baron"
    results = solver.solve(m, tee=True)#, time_limit=900)
    # m.display()
    # print objective
    print("Objective value (makespan):", pyo.value(m.obj))
