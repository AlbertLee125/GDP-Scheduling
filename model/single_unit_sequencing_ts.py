import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
import json
import os

def build_single_unit_sequencing_time_slots():
    # Get the absolute path of the current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the JSON file, Modify the path number for different scheduling data
    json_file_path = os.path.join(script_dir, "../scheduling_data/scheduling_data_1.json")

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

    # Create discrete time slots from 1 to the number of jobs
    num_slots = len(data["jobs"])
    m.T = pyo.Set(initialize=range(1, num_slots + 1))

    # Define parameters dynamically from JSON
    m.p = pyo.Param(m.I, initialize=data["processing_time"])
    m.r = pyo.Param(m.I, initialize=data["release_time"])
    m.d = pyo.Param(m.I, initialize=data["due_time"])

    # Define x as the domain of the jobs using time slots
    def x_bounds_rule(m, i):
        return (0, 1e6)
    m.x = pyo.Var(m.T, bounds=x_bounds_rule)

    # Compute bounds for makespan:
    lower_bound_makespan = min(data["release_time"][i] + data["processing_time"][i] for i in data["jobs"])
    upper_bound_makespan = max(data["due_time"][i] for i in data["jobs"])
    m.makespan = pyo.Var(bounds=(lower_bound_makespan, upper_bound_makespan))

    # Define the time slots disjuncts
    def time_slot_disjunct(disjunct, i, t):
        m = disjunct.model()
        disjunct.cons = pyo.ConstraintList()
        # xt>=r(i)
        disjunct.cons.add(m.x[t] >= m.r[i])
        # xt+p(i)<=d(i)
        disjunct.cons.add(m.x[t] + m.p[i] <= m.d[i])
        # if t = num_slots, then makespan >= x[t] + p[i]
        if t == num_slots:
            disjunct.cons.add(m.makespan >= m.x[t] + m.p[i])
        # if t < num_slots, then x[t] + p[i] <= x[t+1]
        else:
            disjunct.cons.add(m.x[t] + m.p[i] <= m.x[t + 1])
    m.time_slot_disjunct = Disjunct(m.I, m.T, rule=time_slot_disjunct)

    # Define the time slot disjunctions
    def time_slot_disjunction_rule(m, t):
        return [m.time_slot_disjunct[i, t] for i in m.I]
    m.time_slot_disjunction = Disjunction(m.T, rule=time_slot_disjunction_rule)

    # Define the logical constraints for one to be true
    def logical_constraints1(m, t):
        return pyo.exactly(1, (m.time_slot_disjunct[i,t].indicator_var for i in m.I))
    m.logical_constraints1 = pyo.LogicalConstraint(m.T, rule=logical_constraints1)


    # Define the logical constraints for one to be true
    def logical_constraints2(m, i):
        return pyo.exactly(1, (m.time_slot_disjunct[i,t].indicator_var for t in m.T))
    m.logical_constraints2 = pyo.LogicalConstraint(m.I, rule=logical_constraints2)

    # Define objective: minimize makespan
    m.obj = pyo.Objective(expr=m.makespan, sense=pyo.minimize)

    return m

if __name__ == "__main__":
    m = build_single_unit_sequencing_time_slots()
    
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
