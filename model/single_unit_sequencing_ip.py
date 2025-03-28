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

    # last job disjuncts
    def last_job_disjunct_rule(disjunct, i):
        m = disjunct.model()
        disjunct.cons=pyo.ConstraintList()
        # xj + pj <= xi for all i not equal to j
        for j in m.I:
            if i != j:
                disjunct.cons.add(m.x[j] + m.p[j] <= m.x[i])
    m.last_job_disjunct = Disjunct(m.I, rule=last_job_disjunct_rule)

    # Logic Expression
    def logic_expression_rule(m, i):
        return pyo.lnot(pyo.land(m.first_job_disjunct[i].indicator_var, m.last_job_disjunct[i].indicator_var))
    m.logic_expression = pyo.LogicalConstraint(m.I, rule=logic_expression_rule)

    def one_first_job_rule(m, i):
        return pyo.exactly(1, (m.first_job_disjunct[i].indicator_var))
    m.one_first_job = pyo.LogicalConstraint(m.I, rule=one_first_job_rule)

    def one_last_job_rule(m, i):
        return pyo.exactly(1, (m.last_job_disjunct[i].indicator_var))
    m.one_last_job = pyo.LogicalConstraint(m.I, rule=one_last_job_rule)

    # --- Split Immediate Precedence Disjuncts ---
    # Define a common disjunct rule for immediate precedence.
    def immediate_precedence_disjunct_rule(disjunct, i, j):
        m = disjunct.model()
        if i == j:
            disjunct.deactivate()  # deactivate if indices are the same
        else:
            disjunct.cons = pyo.Constraint(expr = m.x[i] + m.p[i] <= m.x[j])
    
    # Create two separate sets of immediate precedence disjuncts:
    m.immediate_precedence_successor = Disjunct(m.I, m.I, rule=immediate_precedence_disjunct_rule)
    m.immediate_precedence_predecessor = Disjunct(m.I, m.I, rule=immediate_precedence_disjunct_rule)

    # Successor Disjunction: For each job i, either one of the immediate precedence_successor disjuncts holds
    # (i.e. job i must precede all its successors) or the last-job condition holds.
    def successor_disjunction_rule(m, i):
        return [m.immediate_precedence_successor[i, j] for j in m.I if j != i] + [m.last_job_disjunct[i]]
    m.SuccessorDisjunction = Disjunction(m.I, rule=successor_disjunction_rule)

    # Predecessor Disjunction: For each job i, either one of the immediate precedence_predecessor disjuncts holds
    # (i.e. job i must follow all its predecessors) or the first-job condition holds.
    def predecessor_disjunction_rule(m, i):
        return [m.immediate_precedence_predecessor[j, i] for j in m.I if j != i] + [m.first_job_disjunct[i]]
    m.PredecessorDisjunction = Disjunction(m.I, rule=predecessor_disjunction_rule)

    # # Define Constraints 
    # def release_time_constraint(m, i):
    #     return m.x[i] >= m.r[i]
    # m.release_time_constraint = pyo.Constraint(m.I, rule=release_time_constraint)

    # def due_date_constraint(m, i):
    #     return m.x[i] + m.p[i] <= m.d[i]
    # m.due_date_constraint = pyo.Constraint(m.I, rule=due_date_constraint)

    def makespan_constraint(m, i):
        return m.x[i] + m.p[i] <= m.makespan
    m.makespan_constraint = pyo.Constraint(m.I, rule=makespan_constraint)

    # Define objective: minimize makespan
    m.obj = pyo.Objective(expr=m.makespan, sense=pyo.minimize)

    return m

def build_single_unit_sequencing_Immediate_Precedence_BigM():
    # Get the absolute path of the current directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the JSON file, Modify the path number for different scheduling data
    json_file_path = os.path.join(script_dir, "../scheduling_data/scheduling_data_2.json")

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

    def x_bounds_rule(m, i):
        return (m.r[i], m.d[i] - m.p[i])
    m.x = pyo.Var(m.I, bounds=x_bounds_rule)

    # Compute bounds for makespan:
    lower_bound_makespan = min(data["release_time"][i] + data["processing_time"][i] for i in data["jobs"])
    upper_bound_makespan = max(data["due_time"][i] for i in data["jobs"])
    m.makespan = pyo.Var(bounds=(lower_bound_makespan, upper_bound_makespan))

    # Introduce binary variables:
    # y_first[i] = 1 if job i is chosen as the first job.
    # y_last[i]  = 1 if job i is chosen as the last job.
    m.y_first = pyo.Var(m.I, domain=pyo.Binary)
    m.y_last  = pyo.Var(m.I, domain=pyo.Binary)
    m.y = pyo.Var(m.I, m.I, domain=pyo.Binary)


    # Define the big-M parameter for each ordered pair (i, j) with i != j:
    def M_rule(m, i, j):
        if i == j:
            return pyo.Param.Skip
        else:
            return m.d[i] - m.r[j]
    m.M = pyo.Param(m.I, m.I, initialize=M_rule, within=pyo.Any)

    def immediate_precedence_rule(m, i, j):
        if i == j:
            return pyo.Constraint.Skip
        else:
            return m.x[i] + m.p[i] <= m.x[j] + m.M[i, j] * (1 - m.y[i, j])
    m.immediate_precedence = pyo.Constraint(m.I, m.I, rule=immediate_precedence_rule)

    # # the following two constraints made the problem infeasible
    # def first_job_constraint_rule(m, i, j):
    #     if i == j:
    #         return pyo.Constraint.Skip
    #     else:
    #         return m.x[i] + m.p[i] <= m.x[j] + m.M[i, j] * (1 - m.y_first[i])
    # m.first_job_constraint = pyo.Constraint(m.I, m.I, rule=first_job_constraint_rule)

    # def last_job_constraint_rule(m, i, j):
    #     if i == j:
    #         return pyo.Constraint.Skip
    #     else:
    #         return m.x[j] + m.p[j] <= m.x[i] + m.M[j, i] * (1 - m.y_last[i])
    # m.last_job_constraint = pyo.Constraint(m.I, m.I, rule=last_job_constraint_rule)

    def predecessor_assignment_rule(m, i):
        return sum(m.y[i,j] for j in m.I if j != i) + m.y_first[i] == 1
    m.predecessor_assignment = pyo.Constraint(m.I, rule=predecessor_assignment_rule)

    def successor_assignment_rule(m, i):
        return m.y_last[i] + sum(m.y[j,i] for j in m.I if j != i) == 1
    m.successor_assignment = pyo.Constraint(m.I, rule=successor_assignment_rule)

    def first_job_rule(m):
        return sum(m.y_first[i] for i in m.I) == 1
    m.first_job = pyo.Constraint(rule=first_job_rule)

    def last_job_rule(m):
        return sum(m.y_last[i] for i in m.I) == 1
    m.last_job = pyo.Constraint(rule=last_job_rule)

    def demorgan_rule(m, i):
        return m.y_first[i] + m.y_last[i] <= 1
    m.demorgan = pyo.Constraint(m.I, rule=demorgan_rule)

    def makespan_constraint(m, i):
        return m.x[i] + m.p[i] <= m.makespan
    m.makespan_constraint = pyo.Constraint(m.I, rule=makespan_constraint)

    # Define objective: minimize makespan
    m.obj = pyo.Objective(expr=m.makespan, sense=pyo.minimize)

    return m

def build_single_unit_sequencing_Immediate_Precedence_HR():
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

    def x_bounds_rule(m, i):
        return (m.r[i], m.d[i] - m.p[i])
    m.x = pyo.Var(m.I, bounds=x_bounds_rule)

    # Compute bounds for makespan:
    lower_bound_makespan = min(data["release_time"][i] + data["processing_time"][i] for i in data["jobs"])
    upper_bound_makespan = max(data["due_time"][i] for i in data["jobs"])
    m.makespan = pyo.Var(bounds=(lower_bound_makespan, upper_bound_makespan))

    # Introduce binary variables:
    # y_first[i] = 1 if job i is chosen as the first job.
    # y_last[i]  = 1 if job i is chosen as the last job.
    m.y_first = pyo.Var(m.I, domain=pyo.Binary)
    m.y_last  = pyo.Var(m.I, domain=pyo.Binary)
    m.y = pyo.Var(m.I, m.I, domain=pyo.Binary)

    return m

if __name__ == "__main__":
    m = build_single_unit_sequencing_Immediate_Precedence() # Putting the same disjunct in multiple disjunctions is not supported in Pyomo.
    # m = build_single_unit_sequencing_Immediate_Precedence_BigM()
    # m = build_single_unit_sequencing_Immediate_Precedence_HR()

    # Apply Big-M Reformulation (or alternatively, use the convex hull reformulation)
    # pyo.TransformationFactory("gdp.bigm").apply_to(m)
    # pyo.TransformationFactory("gdp.hull").apply_to(m)
    
    # Solve the model (solver can be 'gams' with 'baron', 'knitro', etc.)
    solver = pyo.SolverFactory("gurobi")
    # solver.options["solver"] = "baron"
    
    results = solver.solve(m, tee=True)
    # m.display()

    # print objective
    print("Objective value (makespan):", pyo.value(m.obj))
