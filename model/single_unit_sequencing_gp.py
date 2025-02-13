import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
import json
import os

def build_single_unit_sequencing_gp():
    # Get the absolute path of the current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the JSON file, Modify the path number for different scheduling data
    json_file_path = os.path.join(script_dir, "../scheduling_data/scheduling_data_9.json")

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

    # General Precedence Disjunction
    def define_disjuncts(m, i, j):
        if i < j:
            m.before = Disjunct()
            m.after = Disjunct()

            # Access the parent model inside the disjuncts
            model_ref = m.model()

            # i before j
            @m.before.Constraint()
            def before_constraint(m):
                return model_ref.x[i] + model_ref.p[i] <= model_ref.x[j]

            # j before i
            @m.after.Constraint()
            def after_constraint(m):
                return model_ref.x[j] + model_ref.p[j] <= model_ref.x[i]
            
    m.disjuncts = pyo.Block(m.I, m.I, rule=define_disjuncts)

    def sequencing_disjunction(m, i, j):
        if i < j:
            return [m.disjuncts[i, j].before, m.disjuncts[i, j].after]
        return pyo.Constraint.Skip
    
    m.sequencing_disjunction = Disjunction(m.I, m.I, rule=sequencing_disjunction)

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
    m = build_single_unit_sequencing_gp()
    
    # Apply Big-M Reformulation (or alternatively, use the convex hull reformulation)
    pyo.TransformationFactory("gdp.bigm").apply_to(m)
    # pyo.TransformationFactory("gdp.hull").apply_to(m)
    
    # Solve the model (solver can be 'gams' with 'baron', 'knitro', etc.)
    solver = pyo.SolverFactory("gurobi")
    # solver.options["solver"] = "baron"
    results = solver.solve(m, tee=True)
    # m.display()
    # print objective
    print("Objective value (makespan):", pyo.value(m.obj))
