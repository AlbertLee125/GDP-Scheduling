import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
from itertools import product
import json
import os


def build_single_unit_sequencing_time_slots(j):
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
    lower_bound_makespan = min(
        data["release_time"][i] + data["processing_time"][i] for i in data["jobs"]
    )
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
        return pyo.exactly(1, (m.time_slot_disjunct[i, t].indicator_var for i in m.I))

    m.logical_constraints1 = pyo.LogicalConstraint(m.T, rule=logical_constraints1)

    # Define the logical constraints for one to be true
    def logical_constraints2(m, i):
        return pyo.exactly(1, (m.time_slot_disjunct[i, t].indicator_var for t in m.T))

    m.logical_constraints2 = pyo.LogicalConstraint(m.I, rule=logical_constraints2)

    # Define objective: minimize makespan
    m.obj = pyo.Objective(expr=m.makespan, sense=pyo.minimize)

    return m

def print_true_indicator_variables(m):
    print("True Indicator Variables:")
    for i in m.I:
        for t in m.T:
            disjunct = m.time_slot_disjunct[i, t]
            if pyo.value(disjunct.indicator_var) > 0.5:
                print(f"Job {i} scheduled in time slot {t} (Indicator: {disjunct.indicator_var})")

if __name__ == "__main__":
    m = build_single_unit_sequencing_time_slots(2)

    # Apply Big-M Reformulation (or alternatively, use the convex hull reformulation)
    # pyo.TransformationFactory("gdp.bigm").apply_to(m)
    pyo.TransformationFactory("gdp.hull").apply_to(m)
    m.pprint()

    # Solve the model (solver can be 'gams' with 'baron', 'knitro', etc.)
    # solver = pyo.SolverFactory("gurobi")
    # solver = pyo.SolverFactory("gdpopt.gloa") # for gdpopt.loa, lbb
    # solver = pyo.SolverFactory("gdpopt.ldsda")
    # solver = pyo.SolverFactory("gdpopt.enumerate")

    # # solver.options["solver"] = "baron"
    # results = solver.solve(m, 
    #                        tee=True, 
    #                        minlp_solver='gurobi', 
    #                        starting_point=[15, 11, 12, 4, 3, 13, 2, 14, 6, 1, 9, 7, 5, 8, 10], 
    #                     #    starting_point=[15, 11, 12, 4, 3, 13, 14, 2, 6, 1, 9, 7, 5, 8, 10], 
    #                         # starting_point=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    #                        disjunction_list=[m.time_slot_disjunction]) # for gdpopt.ldsda

    # results = solver.solve(m, tee=True)
    # m.display()
    # print objective and solution time
    # print("Objective value (makespan):", pyo.value(m.obj))
    # print_true_indicator_variables(m)

    # # List to record starting points with non-optimal termination conditions
    # failed_starting_points = []

    # for starting_point in product(range(1, 16), repeat=15):
    #     sp_list = list(starting_point)
    #     print("\nUsing starting point:", sp_list)
        
    #     # Solve the model using the current starting point
    #     results = solver.solve(m, 
    #                            tee=True, 
    #                            starting_point=sp_list, 
    #                            disjunction_list=[m.time_slot_disjunction])
        
    #     # Get the termination condition
    #     term_cond = results.solver.termination_condition
    #     print("Termination condition:", term_cond)
        
    #     # If not optimal, record the starting point and termination condition
    #     if term_cond != pyo.TerminationCondition.optimal:
    #         failed_starting_points.append({
    #             "starting_point": sp_list,
    #             "termination_condition": str(term_cond)
    #         })
    #         print("Recorded failed starting point:", sp_list)
        
    #     # Optionally, reset or rebuild the model if needed
    #     # m = build_single_unit_sequencing_time_slots()

    # # Save all recorded failed starting points to a JSON file
    # with open("failed_starting_points.json", "w") as outfile:
    #     json.dump(failed_starting_points, outfile, indent=4)
    
    # print("Failed starting points have been recorded in failed_starting_points.json")
