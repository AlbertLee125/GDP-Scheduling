import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
import json
import os

def build_single_unit_sequencing_Immediate_Precedence():
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

    # first job disjuncts
    def first_job_disjunct_rule(disjunct, i):
        m = disjunct.model()
        disjunct.cons=pyo.ConstraintList()
        # xi+ pi <= xj for all i not equal to j
        for j in m.I:
            if i != j:
                disjunct.cons.add(m.x[i] + m.p[i] <= m.x[j])
    m.first_job_disjunct = Disjunct(m.I, rule=first_job_disjunct_rule)

    def first_job_disjunction_rule(m):
    # Return a list of first-job disjuncts, one per job
        return [m.first_job_disjunct[i] for i in m.I]
    m.first_job_disjunction = Disjunction(rule=first_job_disjunction_rule)

    # last job disjuncts
    def last_job_disjunct_rule(disjunct, i):
        m = disjunct.model()
        disjunct.cons=pyo.ConstraintList()
        # xj + pj <= xi for all i not equal to j
        for j in m.I:
            if i != j:
                disjunct.cons.add(m.x[j] + m.p[j] <= m.x[i])
    m.last_job_disjunct = Disjunct(m.I, rule=last_job_disjunct_rule)

    def last_job_disjunction_rule(m):
    # Return a list of last-job disjuncts, one per job
        return [m.last_job_disjunct[i] for i in m.I]
    m.last_job_disjunction = Disjunction(rule=last_job_disjunction_rule)

    # Logic Expression
    def logic_expression_rule(m, i):
        return pyo.lnot(pyo.land(m.first_job_disjunct[i].indicator_var, m.last_job_disjunct[i].indicator_var))
    m.logic_expression = pyo.LogicalConstraint(m.I, rule=logic_expression_rule)

    # Immediate precedence disjuncts
    def immediate_precedence_disjunct_rule(disjunct, i, j):
        m = disjunct.model()
        if i == j:
            disjunct.deactivate() # Deactivate the disjunct if i == j
        else:
            disjunct.cons = pyo.Constraint(expr=m.x[i] + m.p[i] <= m.x[j])
    m.immediate_precedence_disjunct = Disjunct(m.I, m.I, rule=immediate_precedence_disjunct_rule)

    # Successor Disjunction
    def successor_disjunction_rule(m, i):
        return [m.immediate_precedence_disjunct[i, j] for j in m.I if j != i] + [m.last_job_disjunct[i]]
    m.SuccessorDisjunction = Disjunction(m.I, rule=successor_disjunction_rule)

    # Predecessor Disjunction
    def predecessor_disjunction_rule(m, i):
        return [m.immediate_precedence_disjunct[j, i] for j in m.I if j != i] + [m.first_job_disjunct[i]]
    m.PredecessorDisjunction = Disjunction(m.I, rule=predecessor_disjunction_rule)

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
    m = build_single_unit_sequencing_Immediate_Precedence()
    
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
