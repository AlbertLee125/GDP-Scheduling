import pyomo.environ as pyo
from pyomo.gdp import Disjunction, Disjunct

# Initialize model
m = pyo.ConcreteModel()

# Define sets
I = [1, 2, 3, 4, 5]
J = [1, 2, 3, 4, 5]

# Define variables
m.a = pyo.Var(bounds=(-0.3, 0.2))
m.b = pyo.Var(bounds=(-0.9, -0.5))

# Define disjuncts for Y1
m.Y1_disjuncts = Disjunct(I)
for i in I:
    m.Y1_disjuncts[i].y1_constraint = pyo.Constraint(
        expr=m.a == -0.3 + 0.1 * (i - 1)
    )

# Define disjuncts for Y2
m.Y2_disjuncts = Disjunct(J)
for j in J:
    m.Y2_disjuncts[j].y2_constraint = pyo.Constraint(
        expr=m.b == -0.9 + 0.1 * (j - 1)
    )

# Define disjunctions
m.y1_disjunction = Disjunction(expr=[m.Y1_disjuncts[i] for i in I])
m.y2_disjunction = Disjunction(expr=[m.Y2_disjuncts[j] for j in J])

# Logical constraints to enforce exactly one selection
m.Y1_limit = pyo.LogicalConstraint(
    expr=pyo.exactly(1, [m.Y1_disjuncts[i].indicator_var for i in I])
)
m.Y2_limit = pyo.LogicalConstraint(
    expr=pyo.exactly(1, [m.Y2_disjuncts[j].indicator_var for j in J])
)

# Define objective function
m.obj = pyo.Objective(
    expr=4 * m.a**2
    - 2.1 * m.a**4
    + (1 / 3) * m.a**6
    + m.a * m.b
    - 4 * m.b**2
    + 4 * m.b**4,
    sense=pyo.minimize,
)

# Solve with GDPopt-LDSDA
results = pyo.SolverFactory("gdpopt.ldsda").solve(
    m,
    tee=True,
    starting_point=[1, 1],
    disjunction_list=[m.y1_disjunction, m.y2_disjunction],
    # logical_constraint_list=[m.Y1_limit, m.Y2_limit],
    direction_norm="Linf",
)

# Print results
print(results)

print("\nOptimal Values:")
print(f"a = {pyo.value(m.a)}")
print(f"b = {pyo.value(m.b)}")

# You can also check which disjuncts are active
for i in I:
    if m.Y1_disjuncts[i].indicator_var.value == 1:
        print(f"Y1 Disjunct selected: {i}")

for j in J:
    if m.Y2_disjuncts[j].indicator_var.value == 1:
        print(f"Y2 Disjunct selected: {j}")
