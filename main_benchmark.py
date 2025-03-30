import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct
import time
import json
import os

from model.single_unit_sequencing_gp import build_single_unit_sequencing_gp
from model.single_unit_sequencing_ip import build_single_unit_sequencing_Immediate_Precedence_BigM
from model.single_unit_sequencing_ts import build_single_unit_sequencing_time_slots, build_single_unit_sequencing_time_slots_hull

# Set the number of jobs 1 to 10
J = set(range(1, 11))

# MINLP reformulation
reformulation = {'gdp.bigm', 'gdp.hull'}

if __name__ == "__main__":
    # Example usage
    j = 1  # Change this value to test different scheduling data
    m = build_single_unit_sequencing_time_slots(j)
    # m = build_single_unit_sequencing_gp(j)
    # m = build_single_unit_sequencing_ip(j)

    # Solve the model using a solver of your choice
    pyo.TransformationFactory("gdp.hull").apply_to(m)
    solver = pyo.SolverFactory("gurobi")
    results = solver.solve(m, tee=True)

    # Display results
    # m.display()
    print("Solver Status:", results.solver.termination_condition)
    print("Solver Time:", results.solver.wallclock_time)
    print("Objective Value (MakeSpan):", pyo.value(m.obj))
